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
        self.is_running = False
        self.job_passwords = {}

    async def start_workers(self):
        self.is_running = True
        concurrency = settings.BULK_UPLOAD_CONCURRENCY
        logger.info(f"Starting {concurrency} bulk upload workers...")
        for i in range(concurrency):
            worker_task = asyncio.create_task(self.worker_loop(i))
            self.workers.append(worker_task)

    async def stop_workers(self):
        logger.info("Stopping bulk upload workers...")
        self.is_running = False
        self.job_passwords = {}
        for task in self.workers:
            task.cancel()
        await asyncio.gather(*self.workers, return_exceptions=True)
        self.workers.clear()

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

# Global instance
bulk_worker_manager = BulkWorkerManager()
