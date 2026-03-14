"""Add resume_file_url, resume_text, resume_hash columns

Revision ID: 002_add_resume_storage_fields
Revises: 001_initial
Create Date: 2026-03-14 00:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "002_add_resume_storage_fields"
down_revision: Union[str, None] = "001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("candidates", sa.Column("resume_file_url", sa.Text(), nullable=True))
    op.add_column("candidates", sa.Column("resume_text", sa.Text(), nullable=True))
    op.add_column("candidates", sa.Column("resume_hash", sa.Text(), nullable=True))
    op.create_index("ix_candidates_resume_hash", "candidates", ["resume_hash"])


def downgrade() -> None:
    op.drop_index("ix_candidates_resume_hash", table_name="candidates")
    op.drop_column("candidates", "resume_hash")
    op.drop_column("candidates", "resume_text")
    op.drop_column("candidates", "resume_file_url")
