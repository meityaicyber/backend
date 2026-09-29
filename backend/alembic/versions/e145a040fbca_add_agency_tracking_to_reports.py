"""add_agency_tracking_to_reports

Revision ID: e145a040fbca
Revises: cdd678b58352
Create Date: 2026-09-29 09:58:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e145a040fbca'
down_revision: Union[str, None] = 'cdd678b58352'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('reports', sa.Column('extracted_agency_name', sa.String(), nullable=True))
    op.add_column('reports', sa.Column('agency_detection_method', sa.String(), nullable=True))
    op.add_column('reports', sa.Column('agency_match_method', sa.String(), nullable=True))
    op.add_column('reports', sa.Column('agency_confidence', sa.Float(), nullable=True))
    op.add_column('reports', sa.Column('agency_status', sa.String(), nullable=True, server_default='AGENCY_PENDING'))


def downgrade() -> None:
    op.drop_column('reports', 'agency_status')
    op.drop_column('reports', 'agency_confidence')
    op.drop_column('reports', 'agency_match_method')
    op.drop_column('reports', 'agency_detection_method')
    op.drop_column('reports', 'extracted_agency_name')
