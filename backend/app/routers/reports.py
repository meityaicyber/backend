import uuid
import os

from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user, require_roles
from app.models.user import User
from app.schemas.report import ReportOut, ReportListOut, UploadResponse
from app.services import report_service
from app.config import settings

router = APIRouter(prefix="/api/reports", tags=["Reports"])


@router.post("/upload", response_model=UploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_report(
    file: UploadFile = File(...),
    current_user: User = Depends(require_roles("ADMIN", "AUDITOR")),
    db: AsyncSession = Depends(get_db),
):
    """Upload a report file (PDF, DOCX, or TXT)."""
    # Check file size
    file_bytes = await file.read()
    max_size = settings.MAX_FILE_SIZE_MB * 1024 * 1024
    if len(file_bytes) > max_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size exceeds maximum allowed size of {settings.MAX_FILE_SIZE_MB}MB",
        )

    try:
        result = await report_service.upload_report(
            db, file_bytes, file.filename, current_user.user_id
        )
        return UploadResponse(**result)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("", response_model=ReportListOut)
async def list_reports(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    search: str = Query(None, max_length=200),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all reports with optional search."""
    reports, total = await report_service.get_reports(
        db, skip=skip, limit=limit, search=search
    )
    return ReportListOut(
        reports=[ReportOut.from_orm_with_uploader(r) for r in reports],
        total=total,
    )


@router.get("/{report_id}", response_model=ReportOut)
async def get_report(
    report_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a single report with metadata."""
    report = await report_service.get_report_by_id(db, report_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found",
        )
    return ReportOut.from_orm_with_uploader(report)


@router.get("/{report_id}/download")
async def download_report(
    report_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Download a report file."""
    report = await report_service.get_report_by_id(db, report_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found",
        )

    if not report.storage:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File storage record not found",
        )

    file_path = report.storage.encrypted_file_path
    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found on disk",
        )

    return FileResponse(
        path=file_path,
        filename=report.original_filename,
        media_type=report.mime_type,
    )


@router.delete("/{report_id}")
async def delete_report(
    report_id: uuid.UUID,
    current_user: User = Depends(require_roles("ADMIN")),
    db: AsyncSession = Depends(get_db),
):
    """Delete a report (admin only)."""
    success = await report_service.delete_report(db, report_id, current_user.user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found",
        )
    return {"message": "Report deleted successfully"}
