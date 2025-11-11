"""add_correction_category_notes_expected_value_screenshots

Revision ID: f5a72c9e8b3d
Revises: d9d214d3418e
Create Date: 2025-11-06 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'f5a72c9e8b3d'
down_revision: Union[str, None] = 'd9d214d3418e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add correction_category column
    op.add_column('corrections', sa.Column(
        'correction_category',
        sa.String(length=50),
        nullable=False,
        server_default='Other',
        comment='Category: AI Extraction Error, Wrong HS Code, Calculation Error, Missing Data, Format Issue, Other'
    ))

    # Add notes column (required)
    op.add_column('corrections', sa.Column(
        'notes',
        sa.Text(),
        nullable=False,
        server_default='',
        comment='Required user notes explaining why the correction is needed (max 500 chars)'
    ))

    # Add expected_value column (required)
    op.add_column('corrections', sa.Column(
        'expected_value',
        sa.Text(),
        nullable=False,
        server_default='',
        comment='Required field: what the correct value should be (max 500 chars)'
    ))

    # Add screenshots column (optional JSONB array)
    op.add_column('corrections', sa.Column(
        'screenshots',
        sa.dialects.postgresql.JSONB(),
        nullable=True,
        comment='Optional array of screenshot URLs showing where the correct data appears in the document (max 3)'
    ))

    # Create index on correction_category
    op.create_index(
        op.f('ix_corrections_correction_category'),
        'corrections',
        ['correction_category'],
        unique=False
    )

    # Remove server_defaults after initial migration
    op.alter_column('corrections', 'correction_category', server_default=None)
    op.alter_column('corrections', 'notes', server_default=None)
    op.alter_column('corrections', 'expected_value', server_default=None)


def downgrade() -> None:
    # Drop index
    op.drop_index(op.f('ix_corrections_correction_category'), table_name='corrections')

    # Drop columns
    op.drop_column('corrections', 'screenshots')
    op.drop_column('corrections', 'expected_value')
    op.drop_column('corrections', 'notes')
    op.drop_column('corrections', 'correction_category')
