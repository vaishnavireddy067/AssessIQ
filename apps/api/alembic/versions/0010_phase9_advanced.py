"""
Alembic migration – Phase 9 Advanced Analytics tables.
Creates: candidate_skill_passports, skill_passport_entries,
         panel_review_requests, panel_review_votes,
         candidate_employment_outcomes
Also adds question-level leak_risk_score and usage_count.
"""
from alembic import op
import sqlalchemy as sa

revision = "0010_phase9_advanced"
down_revision = "0009_phase9_analytics"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── Verified Skill Passport ───────────────────────────────────────────────
    op.create_table(
        "candidate_skill_passports",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True)),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
        sa.Column("candidate_email", sa.String(255), nullable=False, unique=True),
        sa.Column("display_name", sa.String(100), nullable=True),
        sa.Column("total_assessments_taken", sa.Integer(), server_default="0"),
        sa.Column("avg_overall_score", sa.Float(), server_default="0.0"),
        sa.Column("share_token", sa.String(100), nullable=False, unique=True),
        sa.Column("is_public", sa.Boolean(), server_default=sa.text("false")),
    )
    op.create_table(
        "skill_passport_entries",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True)),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
        sa.Column("passport_id", sa.Uuid(), sa.ForeignKey("candidate_skill_passports.id", ondelete="CASCADE"), nullable=False),
        sa.Column("skill_name", sa.String(100), nullable=False),
        sa.Column("avg_score", sa.Float(), server_default="0.0"),
        sa.Column("best_score", sa.Float(), server_default="0.0"),
        sa.Column("attempts_count", sa.Integer(), server_default="1"),
        sa.Column("last_assessed_at", sa.DateTime(timezone=True), nullable=True),
    )

    # ── Panel Review Workflow ─────────────────────────────────────────────────
    op.create_table(
        "panel_review_requests",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True)),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
        sa.Column("attempt_id", sa.Uuid(), sa.ForeignKey("assessment_attempts.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("company_id", sa.Uuid(), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.String(50), server_default=sa.text("'PENDING'")),
        sa.Column("required_votes", sa.Integer(), server_default="2"),
    )
    op.create_table(
        "panel_review_votes",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True)),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
        sa.Column("review_request_id", sa.Uuid(), sa.ForeignKey("panel_review_requests.id", ondelete="CASCADE"), nullable=False),
        sa.Column("recruiter_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("verdict", sa.String(20), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
    )

    # ── Post-Hire Outcome Loop ────────────────────────────────────────────────
    op.create_table(
        "candidate_employment_outcomes",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True)),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
        sa.Column("attempt_id", sa.Uuid(), sa.ForeignKey("assessment_attempts.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("company_id", sa.Uuid(), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("candidate_email", sa.String(255), nullable=False),
        sa.Column("performance_rating", sa.Integer(), nullable=False),
        sa.Column("review_period_months", sa.Integer(), server_default="6"),
        sa.Column("role_title", sa.String(255), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("submitted_by", sa.Uuid(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
    )

    # ── Leak Radar fields on questions ───────────────────────────────────────
    op.add_column("questions", sa.Column("usage_count", sa.Integer(), server_default="0", nullable=False))
    op.add_column("questions", sa.Column("leak_risk_score", sa.Float(), server_default="0.0", nullable=False))
    op.add_column("questions", sa.Column("leak_last_checked_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("questions", sa.Column("is_suspected_leaked", sa.Boolean(), server_default=sa.text("false"), nullable=False))


def downgrade() -> None:
    op.drop_column("questions", "is_suspected_leaked")
    op.drop_column("questions", "leak_last_checked_at")
    op.drop_column("questions", "leak_risk_score")
    op.drop_column("questions", "usage_count")
    op.drop_table("candidate_employment_outcomes")
    op.drop_table("panel_review_votes")
    op.drop_table("panel_review_requests")
    op.drop_table("skill_passport_entries")
    op.drop_table("candidate_skill_passports")
