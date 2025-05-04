"""add usage tracking

Revision ID: add_usage_tracking
Revises: 
Create Date: 2024-03-21 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_usage_tracking'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Add new columns to users table
    op.add_column('users', sa.Column('usage_count', sa.Integer(), nullable=True, server_default='0'))
    op.add_column('users', sa.Column('last_usage_time', sa.DateTime(timezone=True), nullable=True))
    op.add_column('users', sa.Column('cooldown_start_time', sa.DateTime(timezone=True), nullable=True))

def downgrade():
    # Remove the columns
    op.drop_column('users', 'usage_count')
    op.drop_column('users', 'last_usage_time')
    op.drop_column('users', 'cooldown_start_time') 