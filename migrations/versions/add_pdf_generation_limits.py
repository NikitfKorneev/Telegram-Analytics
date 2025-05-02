"""add pdf generation limits

Revision ID: add_pdf_generation_limits
Revises: 
Create Date: 2024-03-19 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime

# revision identifiers, used by Alembic.
revision = 'add_pdf_generation_limits'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Add new columns to users table
    op.add_column('users', sa.Column('pdf_generation_count', sa.Integer(), nullable=True, server_default='0'))
    op.add_column('users', sa.Column('last_pdf_generation', sa.DateTime(timezone=True), nullable=True))

def downgrade():
    # Remove the columns if we need to rollback
    op.drop_column('users', 'pdf_generation_count')
    op.drop_column('users', 'last_pdf_generation') 