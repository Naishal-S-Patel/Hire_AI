"""Initial schema

Revision ID: 001_initial
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── candidates ────────────────────────────────────────
    op.create_table(
        "candidates",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("full_name", sa.Text(), nullable=False),
        sa.Column("email", sa.Text(), nullable=False, unique=True),
        sa.Column("phone", sa.Text(), nullable=True),
        sa.Column("location", sa.Text(), nullable=True),
        sa.Column("experience_years", sa.Numeric(), nullable=True),
        sa.Column("skills", postgresql.ARRAY(sa.Text()), default=[]),
        sa.Column("education", postgresql.JSONB(), default=[]),
        sa.Column("source", sa.Text(), nullable=True),
        sa.Column("resume_path", sa.Text(), nullable=True),
        sa.Column("parsed_json", postgresql.JSONB(), default={}),
        sa.Column("ats_score", sa.Numeric(), nullable=True),
        sa.Column("ai_summary", sa.Text(), nullable=True),
        sa.Column("fraud_flags", postgresql.JSONB(), default={}),
        sa.Column("skill_graph_data", postgresql.JSONB(), default={}),
        sa.Column("canonical_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_candidates_email", "candidates", ["email"])
    op.create_index("ix_candidates_full_name", "candidates", ["full_name"])
    op.create_index("ix_candidates_canonical_id", "candidates", ["canonical_id"])

    # ── jobs ──────────────────────────────────────────────
    op.create_table(
        "jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("company", sa.Text(), nullable=True),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("requirements", postgresql.ARRAY(sa.Text()), default=[]),
        sa.Column("preferred_skills", postgresql.ARRAY(sa.Text()), default=[]),
        sa.Column("location", sa.Text(), nullable=True),
        sa.Column("min_experience", sa.Numeric(), nullable=True),
        sa.Column("max_experience", sa.Numeric(), nullable=True),
        sa.Column("salary_range", postgresql.JSONB(), default={}),
        sa.Column("is_active", sa.Boolean(), default=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_jobs_title", "jobs", ["title"])

    # ── applications ──────────────────────────────────────
    op.create_table(
        "applications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("candidate_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("candidates.id"), nullable=False),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("jobs.id"), nullable=False),
        sa.Column("status", sa.Text(), default="applied"),
        sa.Column("ats_score", sa.Numeric(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("metadata", postgresql.JSONB(), default={}),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_applications_candidate_id", "applications", ["candidate_id"])
    op.create_index("ix_applications_job_id", "applications", ["job_id"])

    # ── embeddings_meta ───────────────────────────────────
    op.create_table(
        "embeddings_meta",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("candidate_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("chroma_id", sa.Text(), nullable=False, unique=True),
        sa.Column("source_text", sa.Text(), nullable=True),
        sa.Column("model_name", sa.Text(), default="all-MiniLM-L6-v2"),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_embeddings_meta_candidate_id", "embeddings_meta", ["candidate_id"])

    # ── fraud_reports ─────────────────────────────────────
    op.create_table(
        "fraud_reports",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("candidate_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("risk_score", sa.Numeric(), nullable=True),
        sa.Column("flags", postgresql.JSONB(), default=[]),
        sa.Column("details", sa.Text(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_fraud_reports_candidate_id", "fraud_reports", ["candidate_id"])

    # ── query_sessions ────────────────────────────────────
    op.create_table(
        "query_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("raw_query", sa.Text(), nullable=False),
        sa.Column("parsed_filters", postgresql.JSONB(), default={}),
        sa.Column("results_count", sa.Text(), nullable=True),
        sa.Column("user_id", sa.Text(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("query_sessions")
    op.drop_table("fraud_reports")
    op.drop_table("embeddings_meta")
    op.drop_table("applications")
    op.drop_table("jobs")
    op.drop_table("candidates")
