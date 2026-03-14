"""add video screening fields

Revision ID: 004_add_video_screening_fields
Revises: 003_add_roles_and_applications
Create Date: 2024-01-15

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '004_add_video_screening_fields'
down_revision = '003_add_roles_and_applications'
branch_labels = None
depends_on = None


def upgrade():
    # Add new fields to candidates table
    op.add_column('candidates', sa.Column('first_name', sa.Text(), nullable=True))
    op.add_column('candidates', sa.Column('last_name', sa.Text(), nullable=True))
    op.add_column('candidates', sa.Column('mobile_number', sa.Text(), nullable=True))
    op.add_column('candidates', sa.Column('place_of_residence', sa.Text(), nullable=True))
    op.add_column('candidates', sa.Column('confidence_score', sa.Numeric(), nullable=True))
    op.add_column('candidates', sa.Column('technical_score', sa.Numeric(), nullable=True))
    op.add_column('candidates', sa.Column('video_screening_completed', sa.String(), nullable=True, server_default='pending'))
    
    # Add index for duplicate detection
    op.create_index('ix_candidates_mobile_number', 'candidates', ['mobile_number'])


def downgrade():
    op.drop_index('ix_candidates_mobile_number', 'candidates')
    op.drop_column('candidates', 'video_screening_completed')
    op.drop_column('candidates', 'technical_score')
    op.drop_column('candidates', 'confidence_score')
    op.drop_column('candidates', 'place_of_residence')
    op.drop_column('candidates', 'mobile_number')
    op.drop_column('candidates', 'last_name')
    op.drop_column('candidates', 'first_name')
