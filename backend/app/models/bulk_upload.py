import uuid
import enum
from datetime import datetime, timezone

from sqlalchemy import (
    Column, String, DateTime, ForeignKey, Integer, JSON, Enum, Text, Float
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class BulkJobStatus(str, enum.Enum):
    CREATED = "CREATED"
    SCANNING = "SCANNING"
    QUEUED = "QUEUED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    COMPLETED_WITH_ERRORS = "COMPLETED_WITH_ERRORS"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class BulkItemStatus(str, enum.Enum):
    DISCOVERED = "DISCOVERED"
    PASSWORD_REQUIRED = "PASSWORD_REQUIRED"
    PASSWORD_RESOLVED = "PASSWORD_RESOLVED"
    DECRYPTED = "DECRYPTED"
    AGENCY_IDENTIFIED = "AGENCY_IDENTIFIED"
    AGENCY_REVIEW_REQUIRED = "AGENCY_REVIEW_REQUIRED"
    QUEUED = "QUEUED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    DUPLICATE = "DUPLICATE"
    FAILED = "FAILED"


class BulkUploadJob(Base):
    __tablename__ = "bulk_upload_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_by = Column(
        UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True
    )
    
    total_files = Column(Integer, default=0, nullable=False)
    queued_files = Column(Integer, default=0, nullable=False)
    processing_files = Column(Integer, default=0, nullable=False)
    completed_files = Column(Integer, default=0, nullable=False)
    failed_files = Column(Integer, default=0, nullable=False)
    duplicate_files = Column(Integer, default=0, nullable=False)
    needs_review_files = Column(Integer, default=0, nullable=False)
    
    status = Column(
        Enum(BulkJobStatus, name="bulk_job_status_enum", create_constraint=True),
        default=BulkJobStatus.CREATED,
        nullable=False,
    )

    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User", lazy="joined")
    items = relationship(
        "BulkUploadItem", back_populates="job", lazy="noload", cascade="all, delete-orphan"
    )


class BulkUploadItem(Base):
    __tablename__ = "bulk_upload_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    batch_id = Column(
        UUID(as_uuid=True), ForeignKey("bulk_upload_jobs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    
    filename = Column(String(500), nullable=False)
    file_path = Column(String(1000), nullable=False)  # Temporary storage path (e.g. SeaweedFS temp bucket)
    file_hash = Column(String(64), nullable=True, index=True)
    
    status = Column(
        Enum(BulkItemStatus, name="bulk_item_status_enum", create_constraint=True),
        default=BulkItemStatus.DISCOVERED,
        nullable=False,
    )
    password_status = Column(String(50), nullable=True)
    
    extracted_agency_name = Column(String(500), nullable=True)
    matched_agency_id = Column(
        UUID(as_uuid=True), ForeignKey("agencies.agency_id", ondelete="SET NULL"), nullable=True
    )
    matching_confidence = Column(Float, nullable=True)
    
    # JSON containing top-N candidate agencies + scores for review UI
    candidate_matches = Column(JSON, nullable=True)
    
    processing_error = Column(Text, nullable=True)
    error_code = Column(String(100), nullable=True)
    
    retry_count = Column(Integer, default=0, nullable=False)

    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    job = relationship("BulkUploadJob", back_populates="items")
    agency = relationship("Agency", lazy="joined")
