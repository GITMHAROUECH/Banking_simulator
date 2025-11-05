"""I11: Add exposures, simulation_runs, balance_sheet_snapshots tables

Revision ID: 1f1d214080aa
Revises: 013af7207755
Create Date: 2025-11-03 16:54:33.513115

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1f1d214080aa'
down_revision: Union[str, Sequence[str], None] = '013af7207755'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - I11: Add tables for run_id pipeline."""
    
    # Table simulation_runs
    op.create_table(
        'simulation_runs',
        sa.Column('run_id', sa.String(36), primary_key=True),
        sa.Column('params_hash', sa.String(64), nullable=False, index=True),
        sa.Column('run_date', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('total_exposures', sa.Integer(), nullable=True),
        sa.Column('total_notional', sa.Numeric(20, 2), nullable=True),
        sa.Column('config_json', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    
    # Table exposures
    op.create_table(
        'exposures',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('run_id', sa.String(36), nullable=False),
        sa.Column('product_type', sa.String(50), nullable=False),
        sa.Column('counterparty_id', sa.String(50), nullable=True),
        sa.Column('booking_date', sa.Date(), nullable=True),
        sa.Column('maturity_date', sa.Date(), nullable=True),
        sa.Column('currency', sa.String(3), nullable=False),
        sa.Column('notional', sa.Numeric(20, 2), nullable=True),
        sa.Column('ead', sa.Numeric(20, 2), nullable=True),
        sa.Column('pd', sa.Numeric(10, 6), nullable=True),
        sa.Column('lgd', sa.Numeric(10, 6), nullable=True),
        sa.Column('ccf', sa.Numeric(10, 6), nullable=True),
        sa.Column('maturity_years', sa.Numeric(10, 2), nullable=True),
        sa.Column('mtm', sa.Numeric(20, 2), nullable=True),
        sa.Column('desk', sa.String(50), nullable=True),
        sa.Column('entity', sa.String(50), nullable=False),
        sa.Column('is_retail', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('exposure_class', sa.String(50), nullable=True),
        sa.Column('netting_set_id', sa.String(50), nullable=True),
        sa.Column('collateral_value', sa.Numeric(20, 2), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    
    # Indexes pour exposures
    op.create_index('ix_exposures_run_id', 'exposures', ['run_id'])
    op.create_index('ix_exposures_product_type', 'exposures', ['product_type'])
    op.create_index('ix_exposures_entity', 'exposures', ['entity'])
    op.create_index('ix_exposures_run_product', 'exposures', ['run_id', 'product_type'])
    
    # Table balance_sheet_snapshots
    op.create_table(
        'balance_sheet_snapshots',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('run_id', sa.String(36), nullable=False),
        sa.Column('item_type', sa.String(20), nullable=False),
        sa.Column('category', sa.String(50), nullable=False),
        sa.Column('entity', sa.String(50), nullable=False),
        sa.Column('currency', sa.String(3), nullable=False),
        sa.Column('amount', sa.Numeric(20, 2), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    
    # Indexes pour balance_sheet_snapshots
    op.create_index('ix_bs_run_id', 'balance_sheet_snapshots', ['run_id'])
    op.create_index('ix_bs_run_entity', 'balance_sheet_snapshots', ['run_id', 'entity'])


def downgrade() -> None:
    """Downgrade schema - I11: Drop tables."""
    op.drop_index('ix_bs_run_entity', 'balance_sheet_snapshots')
    op.drop_index('ix_bs_run_id', 'balance_sheet_snapshots')
    op.drop_table('balance_sheet_snapshots')
    
    op.drop_index('ix_exposures_run_product', 'exposures')
    op.drop_index('ix_exposures_entity', 'exposures')
    op.drop_index('ix_exposures_product_type', 'exposures')
    op.drop_index('ix_exposures_run_id', 'exposures')
    op.drop_table('exposures')
    
    op.drop_table('simulation_runs')

