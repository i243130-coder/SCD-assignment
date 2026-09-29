"""Create complaints table with indexes and constraints.

Revision ID: 001
Revises: 
Create Date: 2024-01-01 00:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "complaints",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("location", sa.String(200), nullable=False),
        sa.Column("reporter_contact", sa.String(200), nullable=True),
        sa.Column("category", sa.String(20), nullable=False),
        sa.Column("priority", sa.String(10), nullable=False),
        sa.Column(
            "status", sa.String(20), nullable=False, server_default="open"
        ),
        sa.Column("ai_summary", sa.String(140), nullable=True),
        sa.Column("triaged_by", sa.String(50), nullable=False),
        sa.Column("triage_latency_ms", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            postgresql.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            postgresql.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        # Check constraints enforced at database level
        sa.CheckConstraint(
            "length(text) >= 10 AND length(text) <= 2000",
            name="ck_complaint_text_length",
        ),
        sa.CheckConstraint(
            "length(location) >= 3 AND length(location) <= 200",
            name="ck_complaint_location_length",
        ),
    )

    # Required indexes from assignment specification
    op.create_index(
        "ix_complaints_status_priority",
        "complaints",
        ["status", "priority"],
    )
    op.create_index(
        "ix_complaints_created_at",
        "complaints",
        ["created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_complaints_created_at")
    op.drop_index("ix_complaints_status_priority")
    op.drop_table("complaints")
