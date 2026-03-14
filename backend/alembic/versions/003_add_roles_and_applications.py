"""Add role to users, update applications table, add job fields

Revision ID: 003_add_roles_and_applications
Revises: 002_add_resume_storage_fields
Create Date: 2026-03-14 12:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "003_add_roles_and_applications"
down_revision: Union[str, None] = "002_add_resume_storage_fields"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add role to users table
    op.add_column("users", sa.Column("role", sa.Text(), nullable=False, server_default="USER"))
    
    # Add created_by_hr to jobs table
    op.add_column("jobs", sa.Column("created_by_hr", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("jobs", sa.Column("experience_required", sa.Numeric(), nullable=True))
    op.add_column("jobs", sa.Column("required_skills", sa.ARRAY(sa.Text()), nullable=True))
    
    # Update applications table structure
    op.add_column("applications", sa.Column("candidate_name", sa.Text(), nullable=True))
    op.add_column("applications", sa.Column("candidate_email", sa.Text(), nullable=True))
    op.add_column("applications", sa.Column("candidate_phone", sa.Text(), nullable=True))
    op.add_column("applications", sa.Column("resume_file_url", sa.Text(), nullable=True))
    op.add_column("applications", sa.Column("resume_text", sa.Text(), nullable=True))
    op.add_column("applications", sa.Column("experience_years", sa.Numeric(), nullable=True))
    op.add_column("applications", sa.Column("skills", sa.ARRAY(sa.Text()), nullable=True))
    op.add_column("applications", sa.Column("education", sa.dialects.postgresql.JSONB(), nullable=True))
    op.add_column("applications", sa.Column("ai_summary", sa.Text(), nullable=True))
    op.add_column("applications", sa.Column("risk_score", sa.Numeric(), nullable=True))
    op.add_column("applications", sa.Column("source", sa.Text(), nullable=True))
    op.add_column("applications", sa.Column("hr_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True))
    
    # Update status column to use new values
    op.execute("UPDATE applications SET status = 'PENDING' WHERE status = 'applied'")


def downgrade() -> None:
    op.drop_column("users", "role")
    op.drop_column("jobs", "created_by_hr")
    op.drop_column("jobs", "experience_required")
    op.drop_column("jobs", "required_skills")
    op.drop_column("applications", "candidate_name")
    op.drop_column("applications", "candidate_email")
    op.drop_column("applications", "candidate_phone")
    op.drop_column("applications", "resume_file_url")
    op.drop_column("applications", "resume_text")
    op.drop_column("applications", "experience_years")
    op.drop_column("applications", "skills")
    op.drop_column("applications", "education")
    op.drop_column("applications", "ai_summary")
    op.drop_column("applications", "risk_score")
    op.drop_column("applications", "source")
    op.drop_column("applications", "hr_id")
