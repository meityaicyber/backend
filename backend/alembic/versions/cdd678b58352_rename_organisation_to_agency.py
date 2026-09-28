"""rename_organisation_to_agency

Revision ID: cdd678b58352
Revises: bcc598a47241
Create Date: 2026-09-25 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'cdd678b58352'
down_revision = 'bcc598a47241'
branch_labels = None
depends_on = None


def upgrade():
    # Rename column
    op.alter_column('bulk_upload_items', 'matched_organisation_id', new_column_name='matched_agency_id')
    
    # We might need to drop the old foreign key constraint and create a new one matching the new column name
    # But usually Postgres handles column renames smoothly, so the constraint remains intact under the hood.
    # To be safe and clean, let's explicitly rename the constraint if possible, but it's okay to leave it.
    pass


def downgrade():
    op.alter_column('bulk_upload_items', 'matched_agency_id', new_column_name='matched_organisation_id')
    pass
