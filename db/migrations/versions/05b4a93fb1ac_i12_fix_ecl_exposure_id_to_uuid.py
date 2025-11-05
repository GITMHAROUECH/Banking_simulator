"""i12_fix_ecl_exposure_id_to_uuid

Revision ID: 05b4a93fb1ac
Revises: 7406337b364a
Create Date: 2025-11-03 19:35:58.832462

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '05b4a93fb1ac'
down_revision: Union[str, Sequence[str], None] = '7406337b364a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # SQLite ne supporte pas ALTER COLUMN, donc on doit recréer la table
    op.execute('DROP TABLE IF EXISTS ecl_results')
    
    op.create_table(
        'ecl_results',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('run_id', sa.String(50), nullable=False, index=True),
        sa.Column('scenario_id', sa.String(50), nullable=False, index=True),
        sa.Column('exposure_id', sa.String(36), nullable=False, index=True),
        sa.Column('stage', sa.String(2), nullable=False),
        sa.Column('pd_12m', sa.Numeric(10, 6), nullable=True),
        sa.Column('pd_lifetime', sa.Numeric(10, 6), nullable=True),
        sa.Column('lgd', sa.Numeric(10, 6), nullable=False),
        sa.Column('ead', sa.Numeric(20, 2), nullable=False),
        sa.Column('ecl_amount', sa.Numeric(20, 2), nullable=False),
        sa.Column('ecl_currency', sa.String(3), nullable=False),
        sa.Column('segment_id', sa.String(50), nullable=True),
        sa.Column('calculation_date', sa.DateTime, nullable=False),
        sa.Column('created_at', sa.DateTime, nullable=False),
    )
    
    op.create_index('ix_ecl_run_scenario', 'ecl_results', ['run_id', 'scenario_id'])
    op.create_index('ix_ecl_stage', 'ecl_results', ['stage'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('ecl_results')
