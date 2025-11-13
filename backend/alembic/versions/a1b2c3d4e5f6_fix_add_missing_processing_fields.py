"""fix: add missing processing fields to declarations

Revision ID: a1b2c3d4e5f6
Revises: 2e5400006f94
Create Date: 2025-11-13 00:40:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '2e5400006f94'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add missing processing fields that were skipped in d9d214d3418e migration"""
    # Check if columns exist before adding (to make migration idempotent)
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_columns = {col['name'] for col in inspector.get_columns('declarations')}

    if 'processing_log' not in existing_columns:
        op.add_column('declarations', sa.Column('processing_log', JSONB, nullable=True))

    if 'processing_progress' not in existing_columns:
        op.add_column('declarations', sa.Column('processing_progress', sa.Float(), nullable=True))

    if 'processing_error' not in existing_columns:
        op.add_column('declarations', sa.Column('processing_error', sa.Text(), nullable=True))


def downgrade() -> None:
    """Remove the processing fields"""
    op.drop_column('declarations', 'processing_error')
    op.drop_column('declarations', 'processing_progress')
    op.drop_column('declarations', 'processing_log')
