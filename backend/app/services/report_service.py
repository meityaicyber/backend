import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload

from app.models.report import Report, ReportMetadata, FileValidation, FileStorage, UploadStatus
from app.models.audit import AuditLog
from app.utils.file_utils import (
    validate_extension,
    validate_mime_type,
    compute_sha256,
    get_storage_path,
    save_file_to_disk,
    delete_file_from_disk,
    extract_metadata,
    _sanitize_for_json,
    MIME_TYPE_MAP,
)


async def upload_report(
    db: AsyncSession,
    file_bytes: bytes,
    filename: str,
    user_id: uuid.UUID,
) -> Dict[str, Any]:
    """
    Full upload workflow:
    1. Validate extension
    2. Validate MIME type
    3. Check SHA256 duplicate
    4. Save to disk
    5. Extract metadata
    6. Create DB records
    7. Create audit log
    """
    # 1. Validate extension
    ext_valid, extension = validate_extension(filename)
    if not ext_valid:
        # Create audit log for rejection
        await _create_audit_log(
            db, user_id, None, "FILE_UPLOAD", "FAILED",
            {"reason": f"Invalid file extension: {extension}", "filename": filename}
        )
        raise ValueError(f"File extension '{extension}' is not allowed. Allowed: .pdf, .docx, .txt")

    # 2. Validate MIME type
    mime_valid, detected_mime = validate_mime_type(file_bytes, extension)
    if not mime_valid:
        await _create_audit_log(
            db, user_id, None, "FILE_UPLOAD", "FAILED",
            {"reason": f"MIME type mismatch: {detected_mime}", "filename": filename}
        )
        raise ValueError(
            f"File content type '{detected_mime}' does not match extension '{extension}'"
        )

    # 3. Compute SHA256 and check duplicates
    sha256_hash = compute_sha256(file_bytes)
    existing = await db.execute(
        select(Report).where(Report.sha256_hash == sha256_hash)
    )
    if existing.scalar_one_or_none():
        await _create_audit_log(
            db, user_id, None, "FILE_UPLOAD", "FAILED",
            {"reason": "Duplicate file detected", "sha256": sha256_hash, "filename": filename}
        )
        raise ValueError("A file with the same content (SHA256 hash) already exists")

    # 4. Save file to disk
    dir_path, stored_filename = get_storage_path(filename)
    file_path = save_file_to_disk(file_bytes, dir_path, stored_filename)

    # 5. Extract metadata
    file_metadata = extract_metadata(file_path, extension)
    page_count = file_metadata.get("page_count")

    # 6. Create Report record
    report = Report(
        uploaded_by=user_id,
        original_filename=filename,
        stored_filename=stored_filename,
        file_extension=extension,
        mime_type=detected_mime,
        file_size=len(file_bytes),
        sha256_hash=sha256_hash,
        page_count=page_count,
        upload_status=UploadStatus.UPLOADED,
    )
    db.add(report)
    await db.flush()

    # Create FileValidation record
    validation = FileValidation(
        report_id=report.report_id,
        file_type_valid=True,
        malware_scan_status="SKIPPED",
        duplicate_status="UNIQUE",
        validation_status="PASSED",
        validation_notes="File passed extension and MIME type validation",
    )
    db.add(validation)

    # Create ReportMetadata record
    report_meta = ReportMetadata(
        report_id=report.report_id,
        title=file_metadata.get("title"),
        author=file_metadata.get("author"),
        producer=file_metadata.get("producer"),
        subject=file_metadata.get("subject"),
        keywords=file_metadata.get("keywords"),
        creation_date=file_metadata.get("creation_date"),
        modification_date=file_metadata.get("modification_date"),
        metadata_json=_sanitize_for_json(file_metadata),
    )
    db.add(report_meta)

    # Create FileStorage record
    file_storage = FileStorage(
        report_id=report.report_id,
        encrypted_file_path=file_path,
        encryption_algorithm=None,
        encryption_key_id=None,
        checksum=sha256_hash,
    )
    db.add(file_storage)

    # Update status to VALIDATED
    report.upload_status = UploadStatus.VALIDATED  # type: ignore
    await db.flush()

    # 7. Create audit log
    await _create_audit_log(
        db, user_id, report.report_id, "FILE_UPLOAD", "SUCCESS",  # type: ignore
        {
            "filename": filename,
            "file_size": len(file_bytes),
            "sha256": sha256_hash,
            "mime_type": detected_mime,
        }
    )

    return {
        "report_id": report.report_id,
        "original_filename": filename,
        "upload_status": report.upload_status.value,
        "file_size": len(file_bytes),
        "sha256_hash": sha256_hash,
        "validation_status": "PASSED",
        "message": "File uploaded and validated successfully",
    }


async def get_reports(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 50,
    search: Optional[str] = None,
) -> tuple[List[Report], int]:
    """Get paginated list of reports with optional search."""
    query = select(Report).options(
        joinedload(Report.uploader),
        selectinload(Report.report_metadata),
        selectinload(Report.validation),
    )

    if search:
        query = query.where(
            Report.original_filename.ilike(f"%{search}%")
        )

    # Count total
    count_query = select(func.count(Report.report_id))
    if search:
        count_query = count_query.where(
            Report.original_filename.ilike(f"%{search}%")
        )
    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0

    # Fetch
    result = await db.execute(
        query.order_by(Report.created_at.desc()).offset(skip).limit(limit)
    )
    reports = list(result.scalars().unique().all())

    return reports, total


async def get_report_by_id(
    db: AsyncSession, report_id: uuid.UUID
) -> Optional[Report]:
    """Get a single report with all related data."""
    result = await db.execute(
        select(Report)
        .options(
            joinedload(Report.uploader),
            selectinload(Report.report_metadata),
            selectinload(Report.validation),
            selectinload(Report.storage),
        )
        .where(Report.report_id == report_id)
    )
    return result.unique().scalar_one_or_none()


async def delete_report(
    db: AsyncSession, report_id: uuid.UUID, user_id: uuid.UUID
) -> bool:
    """Delete a report permanently from storage and DB."""
    report = await get_report_by_id(db, report_id)
    if not report:
        return False

    # Delete from storage
    if report.storage and report.storage.encrypted_file_path:
        delete_file_from_disk(report.storage.encrypted_file_path)

    # Delete from database
    await db.delete(report)
    await db.flush()

    await _create_audit_log(
        db, user_id, None, "FILE_DELETE", "SUCCESS",
        {
            "filename": report.original_filename,
            "deleted_report_id": str(report_id)
        }
    )

    return True


async def _create_audit_log(
    db: AsyncSession,
    user_id: uuid.UUID,
    report_id: Optional[uuid.UUID],
    action: str,
    status: str,
    details: Optional[Dict] = None,
):
    """Create an audit log entry."""
    log = AuditLog(
        user_id=user_id,
        report_id=report_id,
        action=action,
        status=status,
        details=details,
    )
    db.add(log)
    await db.flush()
