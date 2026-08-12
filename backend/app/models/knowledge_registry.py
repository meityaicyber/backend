import uuid
from datetime import datetime, timezone

from sqlalchemy import BigInteger, Boolean, Column, Date, DateTime, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID

from app.database import Base


class KnowledgeRegistry(Base):
    """Normalized cyber-threat and audit knowledge packages."""

    __tablename__ = "knowledge_registry"

    knowledge_id = Column(BigInteger, primary_key=True, autoincrement=True)
    knowledge_uuid = Column(UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4)
    registry_version = Column(String(20), nullable=True)
    status = Column(String(20), nullable=True)

    source_name = Column(String(200), nullable=True)
    source_type = Column(String(50), nullable=True)
    source_url = Column(Text, nullable=True)
    publisher = Column(String(200), nullable=True)
    publication_date = Column(Date, nullable=True)
    ingestion_date = Column(DateTime(timezone=True), nullable=True)
    language = Column(String(20), nullable=True)

    title = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)
    original_text = Column(Text, nullable=True)
    keywords = Column(ARRAY(Text), nullable=True)

    threat_type = Column(String(100), nullable=True)
    threat_name = Column(String(200), nullable=True)
    threat_actor = Column(String(200), nullable=True)
    campaign_name = Column(String(200), nullable=True)
    attack_vector = Column(String(100), nullable=True)
    attack_stage = Column(String(100), nullable=True)
    exploitation_status = Column(String(50), nullable=True)

    vendor = Column(String(200), nullable=True)
    product = Column(String(200), nullable=True)
    product_version = Column(String(100), nullable=True)
    operating_system = Column(String(100), nullable=True)
    affected_assets = Column(ARRAY(Text), nullable=True)
    industry_targets = Column(ARRAY(Text), nullable=True)

    cve_ids = Column(ARRAY(Text), nullable=True)
    cwe_ids = Column(ARRAY(Text), nullable=True)
    cvss_score = Column(Numeric(3, 1), nullable=True)
    severity = Column(String(20), nullable=True)
    exploit_available = Column(Boolean, nullable=True)
    exploit_type = Column(String(100), nullable=True)

    mitre_tactics = Column(ARRAY(Text), nullable=True)
    mitre_techniques = Column(ARRAY(Text), nullable=True)
    malware_family = Column(String(200), nullable=True)
    indicators_of_compromise = Column(JSONB, nullable=True)
    yara_rules = Column(JSONB, nullable=True)
    sigma_rules = Column(JSONB, nullable=True)

    business_impact = Column(Text, nullable=True)
    likelihood = Column(String(20), nullable=True)
    risk_level = Column(String(20), nullable=True)
    exploit_maturity = Column(String(50), nullable=True)

    recommended_actions = Column(JSONB, nullable=True)
    patch_available = Column(Boolean, nullable=True)
    patch_reference = Column(Text, nullable=True)
    workaround = Column(Text, nullable=True)

    nist_controls = Column(ARRAY(Text), nullable=True)
    iso27001_controls = Column(ARRAY(Text), nullable=True)
    certin_guidelines = Column(ARRAY(Text), nullable=True)
    cis_controls = Column(ARRAY(Text), nullable=True)
    benchmark_category = Column(String(100), nullable=True)

    audit_questions = Column(JSONB, nullable=True)
    expected_controls = Column(JSONB, nullable=True)
    required_evidence = Column(JSONB, nullable=True)
    expected_artifacts = Column(JSONB, nullable=True)
    audit_priority = Column(Integer, nullable=True)

    confidence_score = Column(Numeric(4, 3), nullable=True)
    extraction_model = Column(String(100), nullable=True)
    normalization_model = Column(String(100), nullable=True)
    reviewed_by_analyst = Column(Boolean, nullable=True)

    tags = Column(ARRAY(Text), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
