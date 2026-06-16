import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Column, String, Boolean, DateTime, ForeignKey, BigInteger, Integer, Text, Enum
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import enum

from app.database import Base


class UploadStatus(str, enum.Enum):
    UPLOADED = "UPLOADED"
    VALIDATED = "VALIDATED"
    REJECTED = "REJECTED"
    QUARANTINED = "QUARANTINED"


class Report(Base):
    __tablename__ = "reports"

    report_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    uploaded_by = Column(
        UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True
    )
    original_filename = Column(String(500), nullable=False)
    stored_filename = Column(String(500), nullable=False)
    file_extension = Column(String(20), nullable=False)
    mime_type = Column(String(100), nullable=False)
    file_size = Column(BigInteger, nullable=False)
    sha256_hash = Column(String(64), nullable=False, index=True)
    simhash = Column(String(64), nullable=True, index=True)
    page_count = Column(Integer, nullable=True)
    upload_status = Column(
        Enum(UploadStatus, name="upload_status_enum", create_constraint=True),
        default=UploadStatus.UPLOADED,
        nullable=False,
    )
    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    uploader = relationship("User", back_populates="reports", lazy="joined")
    report_metadata = relationship(
        "ReportMetadata", back_populates="report", uselist=False, lazy="joined",
        cascade="all, delete-orphan"
    )
    validation = relationship(
        "FileValidation", back_populates="report", uselist=False, lazy="joined",
        cascade="all, delete-orphan"
    )
    storage = relationship(
        "FileStorage", back_populates="report", uselist=False, lazy="joined",
        cascade="all, delete-orphan"
    )
    partial_duplicate = relationship(
        "PartialDuplicate", foreign_keys="PartialDuplicate.report_id", back_populates="report", uselist=False, lazy="joined",
        cascade="all, delete-orphan"
    )
    audit_logs = relationship("AuditLog", back_populates="report", lazy="noload")


class ReportMetadata(Base):
    __tablename__ = "report_metadata"

    metadata_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    report_id = Column(
        UUID(as_uuid=True),
        ForeignKey("reports.report_id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    title = Column(String(500), nullable=True)
    author = Column(String(255), nullable=True)
    producer = Column(String(255), nullable=True)
    subject = Column(Text, nullable=True)
    keywords = Column(Text, nullable=True)
    creation_date = Column(DateTime(timezone=True), nullable=True)
    modification_date = Column(DateTime(timezone=True), nullable=True)
    metadata_json = Column(JSONB, nullable=True)
    extracted_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    # Relationships
    report = relationship("Report", back_populates="report_metadata")


class FileValidation(Base):
    __tablename__ = "file_validation"

    validation_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    report_id = Column(
        UUID(as_uuid=True),
        ForeignKey("reports.report_id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    file_type_valid = Column(Boolean, default=False, nullable=False)
    malware_scan_status = Column(String(50), default="SKIPPED", nullable=False)
    duplicate_status = Column(String(50), default="UNIQUE", nullable=False)
    validation_status = Column(String(50), default="PENDING", nullable=False)
    validation_notes = Column(Text, nullable=True)
    validated_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    # Relationships
    report = relationship("Report", back_populates="validation")


class FileStorage(Base):
    __tablename__ = "file_storage"

    storage_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    report_id = Column(
        UUID(as_uuid=True),
        ForeignKey("reports.report_id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    encrypted_file_path = Column(String(1000), nullable=False)
    encryption_algorithm = Column(String(50), nullable=True)
    encryption_key_id = Column(String(255), nullable=True)
    checksum = Column(String(64), nullable=True)
    stored_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    # Relationships
    report = relationship("Report", back_populates="storage")


class PartialDuplicate(Base):
    __tablename__ = "partial_duplicates"

    duplicate_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    report_id = Column(
        UUID(as_uuid=True),
        ForeignKey("reports.report_id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    original_report_id = Column(
        UUID(as_uuid=True),
        ForeignKey("reports.report_id", ondelete="SET NULL"),
        nullable=True,
    )
    original_filename = Column(String(500), nullable=True)
    hamming_distance = Column(Integer, nullable=True)
    detected_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    # Relationships
    report = relationship("Report", foreign_keys=[report_id], back_populates="partial_duplicate")
    original_report = relationship("Report", foreign_keys=[original_report_id])
