"""
Pipeline Router
---------------
Proxy endpoint that downloads a report from storage,
forwards it to the AI Pipeline service, and returns the results.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
import httpx

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.services import report_service
from app.config import settings

router = APIRouter(prefix="/api/reports", tags=["Pipeline"])


@router.post("/{report_id}/run-pipeline")
async def run_pipeline(
    report_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Run the AI pipeline on a report.
    Downloads the report file from SeaweedFS, forwards it to the
    AI Pipeline microservice, and returns the analysis results.
    """
    from app.utils.seaweedfs_utils import get_file_bytes

    # 1. Fetch the report record
    report = await report_service.get_report_by_id(db, report_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found",
        )

    if not report.storage or not report.storage.encrypted_file_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File storage record not found",
        )

    # 2. Download file from SeaweedFS
    object_name = report.storage.encrypted_file_path
    try:
        encrypted_data = get_file_bytes(object_name)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File not found in storage: {e}",
        )

    # 3. Decrypt if needed
    if report.storage.encryption_algorithm == "Fernet":
        from app.utils.encryption_utils import decrypt_file
        file_data = decrypt_file(encrypted_data)
    else:
        file_data = encrypted_data

    # 4. Forward to AI Pipeline service
    pipeline_url = f"{settings.AI_PIPELINE_URL}/run"
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                pipeline_url,
                data={"report_id": str(report_id)},
                files={"file": (report.original_filename, file_data, report.mime_type)},
            )
            response.raise_for_status()
            return response.json()
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="AI Pipeline service timed out",
        )
    except httpx.ConnectError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI Pipeline service is not available",
        )
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"AI Pipeline service returned an error: {e.response.text}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to communicate with AI Pipeline service: {str(e)}",
        )
