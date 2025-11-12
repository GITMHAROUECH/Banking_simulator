"""i13_add_run_management_fields

Revision ID: 794da3a2d21b
Revises: 05b4a93fb1ac
Create Date: 2025-11-06 19:07:41.651017

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '794da3a2d21b'
down_revision: Union[str, Sequence[str], None] = '05b4a93fb1ac'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add new columns to simulation_runs
    op.add_column('simulation_runs', sa.Column('duration_seconds', sa.Float(), nullable=True))
    op.add_column('simulation_runs', sa.Column('checksum', sa.String(length=64), nullable=True))
    op.add_column('simulation_runs', sa.Column('is_favorite', sa.Boolean(), nullable=False, server_default='0'))
    op.add_column('simulation_runs', sa.Column('tags', sa.Text(), nullable=True))
    op.add_column('simulation_runs', sa.Column('parent_run_id', sa.String(length=36), nullable=True))
    op.add_column('simulation_runs', sa.Column('notes', sa.Text(), nullable=True))
    
    # Create run_logs table
    op.create_table('run_logs',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('run_id', sa.String(length=36), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('level', sa.String(length=10), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['run_id'], ['simulation_runs.run_id'], ),
    )
    op.create_index('ix_run_logs_run_id', 'run_logs', ['run_id'])
    
    # Create run_comparisons table
    op.create_table('run_comparisons',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('run_ids', sa.Text(), nullable=False),  # JSON array
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_run_comparisons_created_at', 'run_comparisons', ['created_at'])


def downgrade() -> None:
    """Downgrade schema."""
    # Drop tables
    op.drop_index('ix_run_comparisons_created_at', table_name='run_comparisons')
    op.drop_table('run_comparisons')
    op.drop_index('ix_run_logs_run_id', table_name='run_logs')
    op.drop_table('run_logs')
    
    # Drop columns from simulation_runs
    op.drop_column('simulation_runs', 'notes')
    op.drop_column('simulation_runs', 'parent_run_id')
    op.drop_column('simulation_runs', 'tags')
    op.drop_column('simulation_runs', 'is_favorite')
    op.drop_column('simulation_runs', 'checksum')
    op.drop_column('simulation_runs', 'duration_seconds')
