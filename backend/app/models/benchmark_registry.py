import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, CheckConstraint, Column, Date, DateTime, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.database import Base


class BenchmarkRegistry(Base):
    __tablename__ = "benchmark_registry"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    benchmark_name = Column(String(150), nullable=False)
    version = Column(String(20), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    benchmark_rules = Column(JSONB, nullable=False)
    scoring_rules = Column(JSONB, nullable=False)
    recommendation_rules = Column(JSONB, nullable=False)
    methodology_rules = Column(JSONB, nullable=False)
    scoring_weights = Column(JSONB, nullable=True)
    thresholds = Column(JSONB, nullable=True)
    approval_status = Column(String(30), nullable=False, default="Draft")
    effective_date = Column(Date, nullable=True)
    expiry_date = Column(Date, nullable=True)
    created_by = Column(String(100), nullable=True)
    approved_by = Column(String(100), nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    approved_at = Column(DateTime(timezone=True), nullable=True)
    change_summary = Column(Text, nullable=True)
    change_history = Column(JSONB, nullable=True)
    checksum_sha256 = Column(String(64), nullable=True)
    package_name = Column(String(255), nullable=True)
    package_path = Column(Text, nullable=True)
    is_active = Column(Boolean, default=False, nullable=False)

    __table_args__ = (
        CheckConstraint(
            "approval_status IN ('Draft','Pending','Approved','Rejected','Deprecated')",
            name="benchmark_registry_approval_status_check",
        ),
    )
