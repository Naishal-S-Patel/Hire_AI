"""add missing candidate integrity columns

Revision ID: 005_add_missing_candidate_columns
Revises: 004_add_video_screening_fields
Create Date: 2026-03-14
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = '005_missing_cols'
down_revision = '004_add_video_screening_fields'
branch_labels = None
depends_on = None


def column_exists(table, column):
    from alembic import op as _op
    from sqlalchemy import inspect, text
    conn = _op.get_bind()
    result = conn.execute(text(
        f"SELECT column_name FROM information_schema.columns "
        f"WHERE table_name='{table}' AND column_name='{column}'"
    ))
    return result.fetchone() is not None


def upgrade():
    cols = [
        ('is_duplicate',          sa.Boolean(),        {'server_default': 'false'}),
        ('fraud_score',           sa.Numeric(),        {'nullable': True}),
        ('fraud_reason',          sa.Text(),           {'nullable': True}),
        ('application_attempts',  sa.Integer(),        {'server_default': '1'}),
        ('is_flagged',            sa.Boolean(),        {'server_default': 'false'}),
        ('verification_status',   sa.String(50),       {'server_default': 'pending'}),
        ('status',                sa.String(50),       {'server_default': 'applied'}),
        ('canonical_id',          UUID(as_uuid=True),  {'nullable': True}),
    ]
    for col_name, col_type, kwargs in cols:
        if not column_exists('candidates', col_name):
            op.add_column('candidates', sa.Column(col_name, col_type, **kwargs))


def downgrade():
    for col in ['is_duplicate', 'fraud_score', 'fraud_reason', 'application_attempts',
                'is_flagged', 'verification_status', 'status', 'canonical_id']:
        op.drop_column('candidates', col)
