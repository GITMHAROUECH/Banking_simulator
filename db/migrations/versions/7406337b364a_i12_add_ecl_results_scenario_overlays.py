"""i12_add_ecl_results_scenario_overlays

Revision ID: 7406337b364a
Revises: 1f1d214080aa
Create Date: 2025-11-03 19:02:08.157207

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7406337b364a'
down_revision: Union[str, Sequence[str], None] = '1f1d214080aa'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create ecl_results table
    op.create_table(
        'ecl_results',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('run_id', sa.String(50), nullable=False, index=True),
        sa.Column('scenario_id', sa.String(50), nullable=False, index=True),
        sa.Column('exposure_id', sa.Integer(), nullable=False, index=True),
        sa.Column('stage', sa.String(2), nullable=False),
        sa.Column('pd_12m', sa.Numeric(10, 6), nullable=True),
        sa.Column('pd_lifetime', sa.Numeric(10, 6), nullable=True),
        sa.Column('lgd', sa.Numeric(10, 6), nullable=False),
        sa.Column('ead', sa.Numeric(20, 2), nullable=False),
        sa.Column('ecl_amount', sa.Numeric(20, 2), nullable=False),
        sa.Column('ecl_currency', sa.String(3), nullable=False),
        sa.Column('segment_id', sa.String(50), nullable=True),
        sa.Column('calculation_date', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    
    # Create indexes for ecl_results
    op.create_index('ix_ecl_run_scenario', 'ecl_results', ['run_id', 'scenario_id'])
    op.create_index('ix_ecl_stage', 'ecl_results', ['stage'])
    
    # Create scenario_overlays table
    op.create_table(
        'scenario_overlays',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('scenario_id', sa.String(50), nullable=False, unique=True, index=True),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('pd_shift', sa.Numeric(10, 2), nullable=True),
        sa.Column('lgd_floor_by_class', sa.Text(), nullable=True),
        sa.Column('sicr_threshold_abs', sa.Numeric(10, 2), nullable=True),
        sa.Column('sicr_threshold_rel', sa.Numeric(10, 2), nullable=True),
        sa.Column('backstop_days', sa.Integer(), nullable=True, server_default='30'),
        sa.Column('discount_rate_mode', sa.String(20), nullable=True, server_default='EIR'),
        sa.Column('discount_rate_value', sa.Numeric(10, 6), nullable=True),
        sa.Column('horizon_months', sa.Integer(), nullable=True, server_default='12'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('scenario_overlays')
    op.drop_index('ix_ecl_stage', 'ecl_results')
    op.drop_index('ix_ecl_run_scenario', 'ecl_results')
    op.drop_table('ecl_results')
