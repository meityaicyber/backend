import uuid
from datetime import datetime
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field

from app.models.bulk_upload import BulkJobStatus, BulkItemStatus

class BulkJobCreate(BaseModel):
    total_files: int = Field(..., gt=0)

class BulkJobOut(BaseModel):
    id: uuid.UUID
    created_by: Optional[uuid.UUID]
    total_files: int
    queued_files: int
    processing_files: int
    completed_files: int
    failed_files: int
    duplicate_files: int
    needs_review_files: int
    status: BulkJobStatus
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True

class BulkItemOut(BaseModel):
    id: uuid.UUID
    batch_id: uuid.UUID
    filename: str
    file_hash: Optional[str]
    status: BulkItemStatus
    password_status: Optional[str]
    extracted_agency_name: Optional[str]
    matched_agency_id: Optional[uuid.UUID]
    matching_confidence: Optional[float]
    candidate_matches: Optional[List[Dict[str, Any]]]
    processing_error: Optional[str]
    error_code: Optional[str]
    retry_count: int
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True

class PaginatedBulkItems(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[BulkItemOut]

class RetryItemRequest(BaseModel):
    password: Optional[str] = None
    agency_id: Optional[uuid.UUID] = None
