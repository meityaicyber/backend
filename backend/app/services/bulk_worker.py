import asyncio
import logging
import os
import uuid
from typing import Optional
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.config import settings
from app.models.bulk_upload import BulkUploadItem, BulkItemStatus, BulkUploadJob, BulkJobStatus
from app.services.bulk_upload_service import BulkUploadService
from app.services.password_resolver import BatchPasswordResolver, FolderPasswordResolver

logger = logging.getLogger(__name__)

class BulkWorkerManager:
    def __init__(self):
        self.workers = []
        self.fallback_workers = []
        self.is_running = False
        self.job_passwords = {}
        self.fallback_queue = asyncio.Queue()

    async def start_workers(self):
        self.is_running = True
        concurrency = settings.BULK_UPLOAD_CONCURRENCY
        logger.info(f"Starting {concurrency} bulk upload workers and 2 fallback workers...")
        
        # Pre-populate fallback queue with any pending reports on startup
        async with AsyncSessionLocal() as db:
            from app.models.report import Report
            result = await db.execute(select(Report.report_id).where(Report.agency_status == 'AGENCY_PENDING'))
            for r_id in result.scalars().all():
                self.fallback_queue.put_nowait(str(r_id))
                
        for i in range(concurrency):
            worker_task = asyncio.create_task(self.worker_loop(i))
            self.workers.append(worker_task)
            
        for i in range(2):
            fallback_task = asyncio.create_task(self.agency_fallback_loop(i))
            self.fallback_workers.append(fallback_task)

    async def stop_workers(self):
        logger.info("Stopping bulk upload workers...")
        self.is_running = False
        self.job_passwords = {}
        for task in self.workers:
            task.cancel()
        for task in self.fallback_workers:
            task.cancel()
        await asyncio.gather(*self.workers, *self.fallback_workers, return_exceptions=True)
        self.workers.clear()
        self.fallback_workers.clear()

    async def worker_loop(self, worker_id: int):
        while self.is_running:
            try:
                processed_any = await self.process_next_item(worker_id)
                if not processed_any:
                    # If no items were found, sleep before polling again
                    await asyncio.sleep(2.0)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Worker {worker_id} encountered an error: {e}")
                await asyncio.sleep(5.0)

    async def process_next_item(self, worker_id: int) -> bool:
        """
        Polls the database for the next QUEUED item, processes it, and updates job stats.
        Returns True if an item was processed, False otherwise.
        """
        async with AsyncSessionLocal() as db:
            # PostgreSQL specific: SKIP LOCKED to allow concurrent workers to pull different rows
            from sqlalchemy.orm import lazyload
            query = (
                select(BulkUploadItem)
                .options(lazyload("*"))
                .where(BulkUploadItem.status == BulkItemStatus.QUEUED)
                .with_for_update(skip_locked=True)
                .limit(1)
            )
            
            result = await db.execute(query)
            item = result.scalar_one_or_none()
            
            if not item:
                return False

            # Mark as processing
            item.status = BulkItemStatus.PROCESSING
            await db.commit()
            
            item_id = item.id
            batch_id = item.batch_id
            file_path = item.file_path
            
            # Fetch job to get user_id and maybe batch password if we implement it that way
            # We assume password is not stored in DB directly for security, but the API will pass it
            # Wait, if password is required and provided in the batch, where is it? 
            # We don't store passwords. If password is required, status becomes PASSWORD_REQUIRED and UI handles it.
            # So password_resolver is Empty by default in the worker.
            
            job_res = await db.execute(select(BulkUploadJob).where(BulkUploadJob.id == batch_id))
            job = job_res.scalar_one_or_none()
            if not job:
                logger.error(f"Job {batch_id} not found for item {item_id}")
                return True

            user_id = job.created_by
            
        # Release the lock by closing the session, then process in a new transaction
        
        # Read the file bytes
        print(f"WORKER {worker_id} CHECKING PATH: {file_path}", flush=True)
        if not os.path.exists(file_path):
            print(f"WORKER {worker_id} PATH DOES NOT EXIST", flush=True)
            async with AsyncSessionLocal() as db:
                print(f"WORKER {worker_id} CALLING FAIL_ITEM", flush=True)
                await BulkUploadService._fail_item(
                    db, await self._get_item(db, item_id), "FILE_NOT_FOUND", "Temporary file missing."
                )
                print(f"WORKER {worker_id} UPDATING STATS", flush=True)
                await self._update_job_stats(db, batch_id)
            print(f"WORKER {worker_id} DONE FAILING", flush=True)
            return True
            
        with open(file_path, "rb") as f:
            file_bytes = f.read()
            
        async with AsyncSessionLocal() as db:
            logger.info(f"Worker {worker_id} processing item {item_id} from job {batch_id}")
            
            # Call the service
            try:
                job_root = os.path.join(settings.BULK_UPLOAD_TEMP_DIR, str(batch_id))
                
                finished_item = await BulkUploadService.process_item(
                    db=db,
                    item_id=item_id,
                    file_bytes=file_bytes,
                    user_id=user_id,
                    password_resolver=FolderPasswordResolver(job_root=job_root),
                    last_successful_password=self.job_passwords.get(str(batch_id))
                )
                if getattr(finished_item, 'successful_password', None):
                    self.job_passwords[str(batch_id)] = finished_item.successful_password
                
                # If finished successfully or failed permanently, we can delete the temp file
                # EXCEPT if it requires password or review, we might need the file again!
                # Wait, if it fails due to PASSWORD_REQUIRED, the retry will need the file.
                # So we only delete if it's COMPLETED, DUPLICATE, or terminal FAILED (not retryable).
                if finished_item.status in [BulkItemStatus.COMPLETED, BulkItemStatus.DUPLICATE]:
                    self._safe_delete_file(file_path)
                elif finished_item.status == BulkItemStatus.FAILED and finished_item.error_code in [
                    "INVALID_FILE", "UNSUPPORTED_FILE_TYPE", "UNSUPPORTED_ENCRYPTION"
                ]:
                    self._safe_delete_file(file_path)
                    
            except Exception as e:
                logger.error(f"Worker {worker_id} failed to process item {item_id}: {e}")
                
            await self._update_job_stats(db, batch_id)
            
        return True

    async def _get_item(self, db: AsyncSession, item_id: uuid.UUID) -> BulkUploadItem:
        res = await db.execute(select(BulkUploadItem).where(BulkUploadItem.id == item_id))
        return res.scalar_one()

    def _safe_delete_file(self, path: str):
        try:
            if os.path.exists(path):
                os.remove(path)
        except Exception as e:
            logger.warning(f"Failed to delete temp file {path}: {e}")

    async def _update_job_stats(self, db: AsyncSession, batch_id: uuid.UUID):
        """Recalculate stats for the job based on items."""
        from sqlalchemy import func
        
        # Aggregate statuses
        query = (
            select(BulkUploadItem.status, func.count(BulkUploadItem.id))
            .where(BulkUploadItem.batch_id == batch_id)
            .group_by(BulkUploadItem.status)
        )
        result = await db.execute(query)
        counts = {status: count for status, count in result.all()}
        
        queued = counts.get(BulkItemStatus.QUEUED, 0)
        processing = counts.get(BulkItemStatus.PROCESSING, 0)
        completed = counts.get(BulkItemStatus.COMPLETED, 0)
        failed = counts.get(BulkItemStatus.FAILED, 0)
        duplicates = counts.get(BulkItemStatus.DUPLICATE, 0)
        needs_review = counts.get(BulkItemStatus.AGENCY_REVIEW_REQUIRED, 0) + counts.get(BulkItemStatus.PASSWORD_REQUIRED, 0)
        
        job_res = await db.execute(select(BulkUploadJob).where(BulkUploadJob.id == batch_id))
        job = job_res.scalar_one()
        
        job.queued_files = queued
        job.processing_files = processing
        job.completed_files = completed
        job.failed_files = failed
        job.duplicate_files = duplicates
        job.needs_review_files = needs_review
        
        if queued == 0 and processing == 0:
            if failed > 0 or needs_review > 0:
                job.status = BulkJobStatus.COMPLETED_WITH_ERRORS
            else:
                job.status = BulkJobStatus.COMPLETED
            if not job.completed_at:
                job.completed_at = datetime.now(timezone.utc)
        else:
            job.status = BulkJobStatus.PROCESSING
            
        await db.commit()

    async def agency_fallback_loop(self, worker_id: int):
        from app.models.report import Report
        from app.services.objective1_service import Objective1Service
        from app.utils.storage import download_file
        from app.utils.encryption_utils import decrypt_file
        from sqlalchemy import update
        
        while self.is_running:
            try:
                report_id = await self.fallback_queue.get()
                logger.info(f"Fallback worker {worker_id} processing report {report_id} for agency extraction")
                
                async with AsyncSessionLocal() as db:
                    report = await db.get(Report, report_id)
                    if not report or report.agency_status not in ['AGENCY_PENDING', 'AGENCY_NOT_FOUND', 'AGENCY_REVIEW_REQUIRED']:
                        self.fallback_queue.task_done()
                        continue
                        
                    # 1. Download file from SeaweedFS
                    encrypted_bytes = download_file(report.stored_filename)
                    if not encrypted_bytes:
                        continue
                        
                    # Decrypt it since Objective 1 needs the actual PDF
                    file_bytes = decrypt_file(encrypted_bytes)
                    
                    # 2. Call Objective 1
                    extracted_name, matched_agency_id, match_status, candidates = await Objective1Service.extract_and_match_agency(
                        db, file_bytes, report.original_filename, report.mime_type
                    )
                    
                    agency_confidence = candidates[0]['score'] if candidates else None
                    agency_match_method = candidates[0].get('match_method', 'UNKNOWN') if candidates else None
                    
                    # 3. Update report
                    await db.execute(
                        update(Report)
                        .where(Report.report_id == report_id)
                        .values(
                            agency_id=matched_agency_id,
                            extracted_agency_name=extracted_name or report.extracted_agency_name,
                            agency_detection_method="OBJECTIVE_1_ML" if extracted_name else report.agency_detection_method,
                            agency_match_method=agency_match_method or report.agency_match_method,
                            agency_confidence=agency_confidence or report.agency_confidence,
                            agency_status=match_status
                        )
                    )
                    await db.commit()
                    
                self.fallback_queue.task_done()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Fallback worker {worker_id} encountered an error: {e}")
                await asyncio.sleep(5.0)


# Global instance
bulk_worker_manager = BulkWorkerManager()

def queue_fallback_agency_detection(report_id: uuid.UUID):
    bulk_worker_manager.fallback_queue.put_nowait(str(report_id))
