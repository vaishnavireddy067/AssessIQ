"""
Alembic migration – create Phase 6 tables and columns (AI Proctoring & Sensory Telemetry).
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0006_proctoring_intelligence"
down_revision = "0005_ai_copilot_and_resumes"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Candidate Consent Records Table
    op.create_table(
        "candidate_consent_records",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("attempt_id", sa.Uuid(), sa.ForeignKey("assessment_attempts.id", ondelete="CASCADE"), unique=True, nullable=False, index=True),
        sa.Column("camera_consent_granted", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("audio_consent_granted", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("browser_monitoring_consent", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        sa.Column("device_specs_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    # 2. Add Phase 6 columns to proctoring_sessions
    op.add_column("proctoring_sessions", sa.Column("face_absence_count", sa.Integer(), server_default=sa.text("0"), nullable=False))
    op.add_column("proctoring_sessions", sa.Column("multiple_faces_count", sa.Integer(), server_default=sa.text("0"), nullable=False))
    op.add_column("proctoring_sessions", sa.Column("audio_spikes_count", sa.Integer(), server_default=sa.text("0"), nullable=False))
    op.add_column("proctoring_sessions", sa.Column("risk_level", sa.String(length=50), server_default=sa.text("'NORMAL'"), nullable=False))
    op.add_column("proctoring_sessions", sa.Column("weighted_deductions_json", sa.JSON(), nullable=True))
    op.add_column("proctoring_sessions", sa.Column("review_status", sa.String(length=50), server_default=sa.text("'PENDING'"), nullable=False))
    op.add_column("proctoring_sessions", sa.Column("reviewed_by_user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True))
    op.add_column("proctoring_sessions", sa.Column("recruiter_verdict_notes", sa.Text(), nullable=True))
    op.add_column("proctoring_sessions", sa.Column("retention_expires_at", sa.DateTime(timezone=True), nullable=True))

    # 3. Add severity column to proctoring_events
    op.add_column("proctoring_events", sa.Column("severity", sa.String(length=20), server_default=sa.text("'LOW'"), nullable=False))


def downgrade() -> None:
    op.drop_column("proctoring_events", "severity")
    op.drop_column("proctoring_sessions", "retention_expires_at")
    op.drop_column("proctoring_sessions", "recruiter_verdict_notes")
    op.drop_column("proctoring_sessions", "reviewed_by_user_id")
    op.drop_column("proctoring_sessions", "review_status")
    op.drop_column("proctoring_sessions", "weighted_deductions_json")
    op.drop_column("proctoring_sessions", "risk_level")
    op.drop_column("proctoring_sessions", "audio_spikes_count")
    op.drop_column("proctoring_sessions", "multiple_faces_count")
    op.drop_column("proctoring_sessions", "face_absence_count")
    op.drop_table("candidate_consent_records")
