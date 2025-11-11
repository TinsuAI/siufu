"""add_celery_task_id_and_processing_statuses

Revision ID: bf08a1fb57b7
Revises: e3061fd0812f
Create Date: 2025-10-18 05:39:07.318374

"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'bf08a1fb57b7'
down_revision: Union[str, None] = 'e3061fd0812f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add new status values to DeclarationStatus enum
    op.execute("ALTER TYPE declarationstatus ADD VALUE IF NOT EXISTS 'PROCESSING_OCR'")
    op.execute("ALTER TYPE declarationstatus ADD VALUE IF NOT EXISTS 'PROCESSING_LLM'")

    # Add celery_task_id column with index
    op.add_column('declarations', sa.Column('celery_task_id', sa.String(length=255), nullable=True))
    op.create_index(op.f('ix_declarations_celery_task_id'), 'declarations', ['celery_task_id'], unique=False)


def downgrade() -> None:
    # Remove index and column
    op.drop_index(op.f('ix_declarations_celery_task_id'), table_name='declarations')
    op.drop_column('declarations', 'celery_task_id')

    # Note: PostgreSQL does not support removing values from ENUMs directly
    # Manual intervention would be required to remove 'PROCESSING_OCR' and 'PROCESSING_LLM'
