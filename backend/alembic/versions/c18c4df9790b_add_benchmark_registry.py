"""Add benchmark registry table

Revision ID: c18c4df9790b
Revises: faa6699324f2
Create Date: 2026-08-05

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

# revision identifiers, used by Alembic.
revision: str = "c18c4df9790b"
down_revision: Union[str, None] = "e1cdc4cfd568"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")
    op.create_table(
        "benchmark_registry",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("benchmark_name", sa.String(150), nullable=False),
        sa.Column("version", sa.String(20), nullable=False, unique=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("benchmark_rules", JSONB, nullable=False),
        sa.Column("scoring_rules", JSONB, nullable=False),
        sa.Column("recommendation_rules", JSONB, nullable=False),
        sa.Column("methodology_rules", JSONB, nullable=False),
        sa.Column("scoring_weights", JSONB, nullable=True),
        sa.Column("thresholds", JSONB, nullable=True),
        sa.Column("approval_status", sa.String(30), nullable=False),
        sa.Column("effective_date", sa.Date(), nullable=True),
        sa.Column("expiry_date", sa.Date(), nullable=True),
        sa.Column("created_by", sa.String(100), nullable=True),
        sa.Column("approved_by", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("change_summary", sa.Text(), nullable=True),
        sa.Column("change_history", JSONB, nullable=True),
        sa.Column("checksum_sha256", sa.String(64), nullable=True),
        sa.Column("package_name", sa.String(255), nullable=True),
        sa.Column("package_path", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("FALSE")),
        sa.CheckConstraint(
            "approval_status IN ('Draft','Pending','Approved','Rejected','Deprecated')",
            name="benchmark_registry_approval_status_check",
        ),
    )


def downgrade() -> None:
    op.drop_table("benchmark_registry")
