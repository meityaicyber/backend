import uuid
import os
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update

from app.database import get_db
from app.dependencies import get_current_user, require_roles
from app.models.user import User
from app.models.bulk_upload import BulkUploadJob, BulkUploadItem, BulkJobStatus, BulkItemStatus
from app.schemas.bulk_upload import BulkJobCreate, BulkJobOut, BulkItemOut, PaginatedBulkItems, RetryItemRequest
from app.services.bulk_upload_service import BulkUploadService
from app.config import settings

router = APIRouter(prefix="/api/bulk-upload", tags=["Bulk Upload"])


@router.post("/jobs", response_model=BulkJobOut, status_code=status.HTTP_201_CREATED)
async def create_bulk_job(
    payload: BulkJobCreate,
    current_user: User = Depends(require_roles("ADMIN", "AUDITOR")),
    db: AsyncSession = Depends(get_db),
):
    """Create a new bulk upload job."""
    job = await BulkUploadService.create_job(db, current_user.user_id, payload.total_files)
    return job


@router.post("/jobs/{job_id}/files")
async def upload_job_files(
    job_id: uuid.UUID,
    files: List[UploadFile] = File(...),
    paths: List[str] = Form(default=[]),
    current_user: User = Depends(require_roles("ADMIN", "AUDITOR")),
    db: AsyncSession = Depends(get_db),
):
    """
    Chunked file upload endpoint.
    Accepts multiple files, saves them to a temp directory, and creates BulkUploadItem records.
    If paths are provided, it respects the relative subfolder structure (e.g., for FolderPasswordResolver).
    """
    # Verify job
    job = await db.get(BulkUploadJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    if job.status not in [BulkJobStatus.CREATED, BulkJobStatus.SCANNING]:
        raise HTTPException(status_code=400, detail=f"Cannot add files to job in {job.status} state")
        
    uploaded_items = []
    
    for i, file in enumerate(files):
        # Extract relative path if provided, else just filename
        rel_path = paths[i] if i < len(paths) and paths[i] else file.filename
        
        # Determine the full temp path FLATTENING the relative structure
        basename = os.path.basename(rel_path)
        temp_path = os.path.join(settings.BULK_UPLOAD_TEMP_DIR, str(job_id), basename)
        os.makedirs(os.path.dirname(temp_path), exist_ok=True)
        
        file_bytes = await file.read()
        
        with open(temp_path, "wb") as f:
            f.write(file_bytes)
            
        # Ignore text files (like password.txt or passwords.csv) for database registration
        if file.filename.lower().endswith('.txt') or file.filename.lower().endswith('.csv'):
            job.total_files -= 1
            continue
            
        item = await BulkUploadService.add_item_to_job(
            db=db,
            batch_id=job_id,
            filename=os.path.basename(file.filename),
            file_path=temp_path,
            file_bytes=file_bytes
        )
        uploaded_items.append(item.id)
        
    await db.commit()
    return {"message": f"Successfully uploaded files to job {job_id}", "item_ids": uploaded_items}


@router.post("/jobs/{job_id}/start")
async def start_bulk_job(
    job_id: uuid.UUID,
    current_user: User = Depends(require_roles("ADMIN", "AUDITOR")),
    db: AsyncSession = Depends(get_db),
):
    """Starts processing the queued files in the job."""
    import os
    from app.config import settings
    
    job = await db.get(BulkUploadJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    # Validate flat directory and single txt file
    job_root = os.path.join(settings.BULK_UPLOAD_TEMP_DIR, str(job_id))
    txt_count = 0
    has_subdirs = False
    
    if os.path.exists(job_root):
        for root, dirs, files in os.walk(job_root):
            if root != job_root and len(files) > 0:
                has_subdirs = True
            for f in files:
                if f.lower().endswith('.txt'):
                    txt_count += 1
                    
    if has_subdirs:
        raise HTTPException(status_code=400, detail="Subdirectories found. Bulk upload now expects a flat directory structure.")
    if txt_count > 1:
        raise HTTPException(status_code=400, detail=f"Found {txt_count} password .txt files. Please provide exactly one, or none.")
        
    from datetime import datetime, timezone
    job.status = BulkJobStatus.PROCESSING
    if not job.started_at:
        job.started_at = datetime.now(timezone.utc)
        
    # Set all DISCOVERED items to QUEUED so workers can pick them up
    await db.execute(
        update(BulkUploadItem)
        .where(BulkUploadItem.batch_id == job_id)
        .where(BulkUploadItem.status == BulkItemStatus.DISCOVERED)
        .values(status=BulkItemStatus.QUEUED)
    )
    
    await db.commit()
    return {"message": "Job started. Workers will begin processing files."}


@router.post("/jobs/{job_id}/cancel")
async def cancel_bulk_job(
    job_id: uuid.UUID,
    current_user: User = Depends(require_roles("ADMIN", "AUDITOR")),
    db: AsyncSession = Depends(get_db),
):
    """Cancels a bulk job. Queued items are marked as FAILED/CANCELLED."""
    job = await db.get(BulkUploadJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    job.status = BulkJobStatus.CANCELLED
    from datetime import datetime, timezone
    job.completed_at = datetime.now(timezone.utc)
    
    # Mark queued items as failed
    await db.execute(
        update(BulkUploadItem)
        .where(BulkUploadItem.batch_id == job_id)
        .where(BulkUploadItem.status.in_([BulkItemStatus.QUEUED, BulkItemStatus.DISCOVERED]))
        .values(status=BulkItemStatus.FAILED, error_code="CANCELLED", processing_error="Job was cancelled")
    )
    
    await db.commit()
    return {"message": "Job cancelled."}


@router.get("/jobs/{job_id}", response_model=BulkJobOut)
async def get_bulk_job(
    job_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the current status and metrics of a bulk job."""
    job = await db.get(BulkUploadJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.get("/jobs/{job_id}/items", response_model=PaginatedBulkItems)
async def get_bulk_job_items(
    job_id: uuid.UUID,
    status: Optional[BulkItemStatus] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get paginated items for a job, optionally filtered by status."""
    query = select(BulkUploadItem).where(BulkUploadItem.batch_id == job_id)
    count_query = select(func.count(BulkUploadItem.id)).where(BulkUploadItem.batch_id == job_id)
    
    if status:
        query = query.where(BulkUploadItem.status == status)
        count_query = count_query.where(BulkUploadItem.status == status)
        
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    query = query.order_by(BulkUploadItem.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    items = result.scalars().all()
    
    return PaginatedBulkItems(
        total=total,
        page=page,
        page_size=page_size,
        items=items
    )


@router.post("/items/{item_id}/retry")
async def retry_bulk_item(
    item_id: uuid.UUID,
    payload: RetryItemRequest,
    current_user: User = Depends(require_roles("ADMIN", "AUDITOR")),
    db: AsyncSession = Depends(get_db),
):
    """
    Retry a specific failed or review-required item.
    If the failure was due to missing password, user can supply 'password'.
    If it was due to unmapped agency, user can supply 'agency_id'.
    """
    item = await db.get(BulkUploadItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
        
    if item.status in [BulkItemStatus.COMPLETED, BulkItemStatus.DUPLICATE]:
        raise HTTPException(status_code=400, detail="Cannot retry a completed or duplicate item")
        
    if payload.agency_id:
        item.matched_agency_id = payload.agency_id
        
    # We don't save password in DB, but we could trigger processing right away in background
    # However, since we rely on the worker pool, how do we pass the password to the worker?
    # Simple solution for Phase 8: If password provided, process inline synchronously.
    # If no password, set to QUEUED for workers to pick up.
    
    if payload.password:
        from app.services.password_resolver import BatchPasswordResolver
        import os
        
        if not os.path.exists(item.file_path):
            raise HTTPException(status_code=404, detail="Temporary file missing. Cannot retry.")
            
        with open(item.file_path, "rb") as f:
            file_bytes = f.read()
            
        resolver = BatchPasswordResolver(payload.password)
        # Note: we update retry_count before calling
        item.retry_count += 1
        await db.commit()
        
        await BulkUploadService.process_item(db, item_id, file_bytes, current_user.user_id, resolver)
        
        # After inline processing, return the updated item state
        await db.refresh(item)
        return {"message": "Item retry processed inline", "status": item.status}
    else:
        item.status = BulkItemStatus.QUEUED
        item.retry_count += 1
        item.processing_error = None
        item.error_code = None
        await db.commit()
        return {"message": "Item queued for background retry"}


@router.post("/jobs/{job_id}/retry-failed")
async def retry_failed_job_items(
    job_id: uuid.UUID,
    current_user: User = Depends(require_roles("ADMIN", "AUDITOR")),
    db: AsyncSession = Depends(get_db),
):
    """
    Auto-retry all items in a job that failed with transient errors.
    (e.g. DATABASE_ERROR, TEMPORARY_NETWORK_ERROR, ML_PROCESSING_FAILED)
    Does NOT auto-retry INVALID_PASSWORD, AGENCY_NOT_IDENTIFIED, etc.
    """
    transient_errors = ["DATABASE_ERROR", "TEMPORARY_NETWORK_ERROR", "ML_PROCESSING_FAILED", "UNKNOWN_ERROR", "PROCESSING_FAILED"]
    
    result = await db.execute(
        update(BulkUploadItem)
        .where(BulkUploadItem.batch_id == job_id)
        .where(BulkUploadItem.status == BulkItemStatus.FAILED)
        .where(BulkUploadItem.error_code.in_(transient_errors))
        .values(
            status=BulkItemStatus.QUEUED,
            retry_count=BulkUploadItem.retry_count + 1,
            processing_error=None,
            error_code=None
        )
    )
    
    await db.commit()
    
    job = await db.get(BulkUploadJob, job_id)
    if job:
        job.status = BulkJobStatus.PROCESSING
        await db.commit()
        
    return {"message": f"Queued transient failed items for retry."}
