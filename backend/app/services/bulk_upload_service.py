import uuid
import os
from datetime import datetime, timezone
from typing import Optional, List, Dict

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.bulk_upload import BulkUploadJob, BulkUploadItem, BulkJobStatus, BulkItemStatus
from app.models.report import Report
from app.models.agency import Agency
from app.utils.clamav_utils import scan_file_bytes
from app.utils.file_utils import compute_sha256, validate_extension, validate_mime_type

from app.services.password_resolver import resolve_and_decrypt, PasswordResolver, EmptyPasswordResolver
from app.services.objective1_service import Objective1Service
from app.services.report_service import upload_report
from app.config import settings
import httpx
from app.models.report import ReportsData, Vulnerability, SeverityLevel, VulnStatus
from sqlalchemy import delete

async def _run_deep_ai_pipeline(db: AsyncSession, report_id: uuid.UUID, filename: str, file_bytes: bytes, mime_type: str):
    pipeline_url = f"{settings.AI_PIPELINE_URL}/run"
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                pipeline_url,
                data={"report_id": str(report_id)},
                files={"file": (filename, file_bytes, mime_type)},
            )
            response.raise_for_status()
            data = response.json()
            vulns = data.pop("vulnerabilities", [])
            
            existing_rd_res = await db.execute(select(ReportsData).where(ReportsData.report_id == report_id))
            rd = existing_rd_res.scalar_one_or_none()
            if rd:
                rd.data = data
                from sqlalchemy.orm.attributes import flag_modified
                flag_modified(rd, "data")
                rd.updated_at = datetime.now(timezone.utc)
            else:
                rd = ReportsData(report_id=report_id, data=data)
                db.add(rd)
            
            await db.execute(delete(Vulnerability).where(Vulnerability.report_id == report_id))
            for v in vulns:
                severity_str = str(v.get("severity", "")).upper()
                severity_enum = None
                if severity_str == "CRITICAL": severity_enum = SeverityLevel.CRITICAL
                elif severity_str == "HIGH": severity_enum = SeverityLevel.HIGH
                elif severity_str == "MEDIUM": severity_enum = SeverityLevel.MEDIUM
                elif severity_str == "LOW": severity_enum = SeverityLevel.LOW
                elif severity_str == "INFORMATIONAL": severity_enum = SeverityLevel.INFORMATIONAL
                
                status_str = str(v.get("status", "")).upper()
                status_enum = VulnStatus.OPEN
                if status_str == "CLOSED": status_enum = VulnStatus.CLOSED
                elif status_str == "ACCEPTED": status_enum = VulnStatus.ACCEPTED
                elif status_str == "RISK ACCEPTED": status_enum = VulnStatus.RISK_ACCEPTED
                elif status_str == "IN PROGRESS": status_enum = VulnStatus.IN_PROGRESS
                
                vuln = Vulnerability(
                    report_id=report_id,
                    vulnerability_title=v.get("vulnerability_title", "Unknown Vulnerability"),
                    category=v.get("category"),
                    severity=severity_enum,
                    cvss_score=v.get("cvss_score"),
                    cve_ids=v.get("cve_ids", []),
                    cwe_ids=v.get("cwe_ids", []),
                    affected_assets=v.get("affected_assets", []),
                    status=status_enum,
                    new_or_repeat=v.get("new_or_repeat"),
                    revalidation_status=v.get("revalidation_status"),
                    detailed_observation=v.get("detailed_observation"),
                    description=v.get("description"),
                    impact=v.get("impact"),
                    recommendation=v.get("recommendation"),
                    proof_of_concept=v.get("proof_of_concept"),
                    reproduction_steps=v.get("reproduction_steps"),
                    reference=v.get("reference"),
                    meta_data=v.get("additional meta", {})
                )
                db.add(vuln)
            await db.commit()
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Deep AI Pipeline failed for report {report_id}: {e}")

class BulkUploadService:
    @staticmethod
    async def create_job(db: AsyncSession, user_id: uuid.UUID, total_files: int) -> BulkUploadJob:
        job = BulkUploadJob(
            created_by=user_id,
            total_files=total_files,
            status=BulkJobStatus.CREATED
        )
        db.add(job)
        await db.commit()
        await db.refresh(job)
        return job

    @staticmethod
    async def add_item_to_job(
        db: AsyncSession,
        batch_id: uuid.UUID,
        filename: str,
        file_path: str,
        file_bytes: bytes
    ) -> BulkUploadItem:
        # Calculate hash on raw bytes
        file_hash = compute_sha256(file_bytes)
        
        item = BulkUploadItem(
            batch_id=batch_id,
            filename=filename,
            file_path=file_path,
            file_hash=file_hash,
            status=BulkItemStatus.DISCOVERED
        )
        db.add(item)
        await db.commit()
        await db.refresh(item)
        
        # Update job queued count
        await db.execute(
            update(BulkUploadJob)
            .where(BulkUploadJob.id == batch_id)
            .values(queued_files=BulkUploadJob.queued_files + 1)
        )
        await db.commit()
        
        return item

    @staticmethod
    async def process_item(
        db: AsyncSession,
        item_id: uuid.UUID,
        file_bytes: bytes,
        user_id: uuid.UUID,
        password_resolver: Optional[PasswordResolver] = None, last_successful_password: str = None
    ) -> BulkUploadItem:
        if not password_resolver:
            password_resolver = EmptyPasswordResolver()

        # Fetch item
        result = await db.execute(select(BulkUploadItem).where(BulkUploadItem.id == item_id))
        item = result.scalar_one_or_none()
        if not item:
            raise ValueError(f"Item {item_id} not found")
            
        try:
            item.status = BulkItemStatus.PROCESSING
            item.started_at = datetime.now(timezone.utc)
            await db.commit()

            # 2. Validate files (type, size, existing malware scan)
            ext_valid, extension = validate_extension(item.filename)
            if not ext_valid:
                return await BulkUploadService._fail_item(db, item, "INVALID_FILE", f"Invalid extension {extension}")
                
            mime_valid, detected_mime = validate_mime_type(file_bytes, extension)
            if not mime_valid:
                return await BulkUploadService._fail_item(db, item, "INVALID_FILE", f"MIME mismatch {detected_mime}")

            # Malware scan on raw bytes
            is_clean, scan_message = await scan_file_bytes(file_bytes)
            if not is_clean:
                return await BulkUploadService._fail_item(db, item, "INVALID_FILE", f"Malware detected: {scan_message}")

            # 3. Calculate file hash (server-side) -> check duplicate -> skip if DUPLICATE
            # (Hash already calculated during add_item_to_job and stored in item.file_hash)
            # Check against previously processed reports in the main reports table
            existing_report = await db.execute(select(Report).where(Report.sha256_hash == item.file_hash))
            if existing_report.scalar_one_or_none():
                item.status = BulkItemStatus.DUPLICATE
                item.error_code = "DUPLICATE_FILE"
                item.processing_error = "File hash matches an already processed report."
                item.completed_at = datetime.now(timezone.utc)
                await db.commit()
                return item

            # 4, 5, 6. Password detection and decryption
            decrypted_bytes, pwd_status, successful_pwd = await resolve_and_decrypt(
                file_bytes, item.file_path, extension, password_resolver, last_successful_password
            )
            item.password_status = pwd_status
            setattr(item, 'successful_password', successful_pwd)

            if pwd_status == 'DECRYPTED':
                # Overwrite temp file with decrypted bytes so retry skips decryption
                with open(item.file_path, 'wb') as f:
                    f.write(decrypted_bytes)
            
            if pwd_status in ['PASSWORD_NOT_FOUND', 'INVALID_PASSWORD']:
                item.status = BulkItemStatus.PASSWORD_REQUIRED if pwd_status == 'PASSWORD_NOT_FOUND' else BulkItemStatus.FAILED
                item.error_code = pwd_status
                item.processing_error = f"Password resolution failed: {pwd_status}"
                await db.commit()
                return item

            if pwd_status == 'UNSUPPORTED_ENCRYPTION':
                return await BulkUploadService._fail_item(db, item, "UNSUPPORTED_FILE_TYPE", "File encryption not supported")

            # 10, 11. Process report (reuse single upload logic)
            # Agency detection is now handled automatically inside upload_report
            try:
                # We pass the decrypted bytes so that the downstream pipeline doesn't need the password again
                result_dict = await upload_report(
                    db=db,
                    file_bytes=decrypted_bytes,
                    filename=item.filename,
                    user_id=user_id,
                    agency_id=None  # Now determined inside upload_report
                )
                
                new_report_id = result_dict.get("report_id")
                
                # Check if it was flagged as duplicate by the downstream logic
                if result_dict.get("duplicate_status") == "PARTIAL_DUPLICATE":
                    # It's a partial duplicate but still uploaded
                    pass
                    
                # Run the deep AI analytics pipeline automatically as requested!
                if new_report_id:
                    import asyncio
                    # Fire and forget or await it? We'll await it to ensure it completes before marking COMPLETED
                    await _run_deep_ai_pipeline(db, new_report_id, item.filename, decrypted_bytes, detected_mime)

                item.extracted_agency_name = result_dict.get("extracted_agency_name")
                item.matched_agency_id = result_dict.get("matched_agency_id")
                
                agency_status = result_dict.get("agency_status")
                if agency_status in ["AGENCY_PENDING", "AGENCY_REVIEW_REQUIRED"]:
                    item.status = BulkItemStatus.AGENCY_REVIEW_REQUIRED
                else:
                    item.status = BulkItemStatus.COMPLETED
                    
                item.completed_at = datetime.now(timezone.utc)
                await db.commit()
                
            except ValueError as ve:
                if "already exists" in str(ve).lower() or "duplicate" in str(ve).lower():
                    item.status = BulkItemStatus.DUPLICATE
                    item.error_code = "DUPLICATE_FILE"
                    item.processing_error = str(ve)
                else:
                    item.status = BulkItemStatus.FAILED
                    item.error_code = "PROCESSING_FAILED"
                    item.processing_error = str(ve)
                item.completed_at = datetime.now(timezone.utc)
                await db.commit()
            except Exception as e:
                return await BulkUploadService._fail_item(db, item, "UNKNOWN_ERROR", str(e))
                
        except Exception as e:
            return await BulkUploadService._fail_item(db, item, "UNKNOWN_ERROR", str(e))
            
        return item

    @staticmethod
    async def _fail_item(db: AsyncSession, item: BulkUploadItem, error_code: str, error_msg: str) -> BulkUploadItem:
        item.status = BulkItemStatus.FAILED
        item.error_code = error_code
        item.processing_error = error_msg
        item.completed_at = datetime.now(timezone.utc)
        await db.commit()
        return item
