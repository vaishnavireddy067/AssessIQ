"""Alembic migration – create Phase 4 tables (AI & Proctoring Engine).
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0004_ai_and_proctoring"
down_revision = "0003_coding_sql_engine"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Proctoring Sessions
    op.create_table(
        "proctoring_sessions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("attempt_id", sa.Uuid(), sa.ForeignKey("assessment_attempts.id", ondelete="CASCADE"), unique=True, nullable=False, index=True),
        sa.Column("integrity_score", sa.Float(), server_default=sa.text("100.0"), nullable=False),
        sa.Column("tab_switches_count", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("fullscreen_exits_count", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("paste_count", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("is_flagged", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("summary_notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    # 2. Proctoring Events
    op.create_table(
        "proctoring_events",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("session_id", sa.Uuid(), sa.ForeignKey("proctoring_sessions.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("event_type", sa.String(length=50), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    # 3. AI Evaluation Summaries
    op.create_table(
        "ai_evaluation_summaries",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("attempt_id", sa.Uuid(), sa.ForeignKey("assessment_attempts.id", ondelete="CASCADE"), unique=True, nullable=False, index=True),
        sa.Column("recommendation", sa.String(length=50), nullable=False),
        sa.Column("overall_score_percentage", sa.Float(), server_default=sa.text("0.0"), nullable=False),
        sa.Column("technical_depth_rating", sa.String(length=50), server_default="MID_LEVEL", nullable=False),
        sa.Column("executive_summary", sa.Text(), nullable=False),
        sa.Column("strengths", sa.JSON(), nullable=False),
        sa.Column("weaknesses", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("ai_evaluation_summaries")
    op.drop_table("proctoring_events")
    op.drop_table("proctoring_sessions")
