"""Add knowledge registry table.

Revision ID: d2a4f89b6c01
Revises: c18c4df9790b
Create Date: 2026-08-06
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "d2a4f89b6c01"
down_revision: Union[str, None] = "c18c4df9790b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")
    op.create_table(
        "knowledge_registry",
        sa.Column("knowledge_id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("knowledge_uuid", postgresql.UUID(as_uuid=True), nullable=False, unique=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("registry_version", sa.String(20)), sa.Column("status", sa.String(20)),
        sa.Column("source_name", sa.String(200)), sa.Column("source_type", sa.String(50)), sa.Column("source_url", sa.Text()), sa.Column("publisher", sa.String(200)), sa.Column("publication_date", sa.Date()), sa.Column("ingestion_date", sa.DateTime(timezone=True)), sa.Column("language", sa.String(20)),
        sa.Column("title", sa.Text()), sa.Column("summary", sa.Text()), sa.Column("original_text", sa.Text()), sa.Column("keywords", postgresql.ARRAY(sa.Text())),
        sa.Column("threat_type", sa.String(100)), sa.Column("threat_name", sa.String(200)), sa.Column("threat_actor", sa.String(200)), sa.Column("campaign_name", sa.String(200)), sa.Column("attack_vector", sa.String(100)), sa.Column("attack_stage", sa.String(100)), sa.Column("exploitation_status", sa.String(50)),
        sa.Column("vendor", sa.String(200)), sa.Column("product", sa.String(200)), sa.Column("product_version", sa.String(100)), sa.Column("operating_system", sa.String(100)), sa.Column("affected_assets", postgresql.ARRAY(sa.Text())), sa.Column("industry_targets", postgresql.ARRAY(sa.Text())),
        sa.Column("cve_ids", postgresql.ARRAY(sa.Text())), sa.Column("cwe_ids", postgresql.ARRAY(sa.Text())), sa.Column("cvss_score", sa.Numeric(3, 1)), sa.Column("severity", sa.String(20)), sa.Column("exploit_available", sa.Boolean()), sa.Column("exploit_type", sa.String(100)),
        sa.Column("mitre_tactics", postgresql.ARRAY(sa.Text())), sa.Column("mitre_techniques", postgresql.ARRAY(sa.Text())), sa.Column("malware_family", sa.String(200)), sa.Column("indicators_of_compromise", postgresql.JSONB()), sa.Column("yara_rules", postgresql.JSONB()), sa.Column("sigma_rules", postgresql.JSONB()),
        sa.Column("business_impact", sa.Text()), sa.Column("likelihood", sa.String(20)), sa.Column("risk_level", sa.String(20)), sa.Column("exploit_maturity", sa.String(50)),
        sa.Column("recommended_actions", postgresql.JSONB()), sa.Column("patch_available", sa.Boolean()), sa.Column("patch_reference", sa.Text()), sa.Column("workaround", sa.Text()),
        sa.Column("nist_controls", postgresql.ARRAY(sa.Text())), sa.Column("iso27001_controls", postgresql.ARRAY(sa.Text())), sa.Column("certin_guidelines", postgresql.ARRAY(sa.Text())), sa.Column("cis_controls", postgresql.ARRAY(sa.Text())), sa.Column("benchmark_category", sa.String(100)),
        sa.Column("audit_questions", postgresql.JSONB()), sa.Column("expected_controls", postgresql.JSONB()), sa.Column("required_evidence", postgresql.JSONB()), sa.Column("expected_artifacts", postgresql.JSONB()), sa.Column("audit_priority", sa.Integer()),
        sa.Column("confidence_score", sa.Numeric(4, 3)), sa.Column("extraction_model", sa.String(100)), sa.Column("normalization_model", sa.String(100)), sa.Column("reviewed_by_analyst", sa.Boolean()),
        sa.Column("tags", postgresql.ARRAY(sa.Text())),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.CheckConstraint("cvss_score IS NULL OR cvss_score BETWEEN 0 AND 10", name="knowledge_registry_cvss_score_check"),
        sa.CheckConstraint("confidence_score IS NULL OR confidence_score BETWEEN 0 AND 1", name="knowledge_registry_confidence_score_check"),
        sa.CheckConstraint("audit_priority IS NULL OR audit_priority BETWEEN 1 AND 5", name="knowledge_registry_audit_priority_check"),
    )
    op.create_index("ix_knowledge_registry_status", "knowledge_registry", ["status"])
    op.create_index("ix_knowledge_registry_source_name", "knowledge_registry", ["source_name"])
    op.create_index("ix_knowledge_registry_severity", "knowledge_registry", ["severity"])
    op.create_index("ix_knowledge_registry_risk_level", "knowledge_registry", ["risk_level"])


def downgrade() -> None:
    op.drop_index("ix_knowledge_registry_risk_level", table_name="knowledge_registry")
    op.drop_index("ix_knowledge_registry_severity", table_name="knowledge_registry")
    op.drop_index("ix_knowledge_registry_source_name", table_name="knowledge_registry")
    op.drop_index("ix_knowledge_registry_status", table_name="knowledge_registry")
    op.drop_table("knowledge_registry")
