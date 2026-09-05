"""
Alembic migration – create Phase 5 tables (AI Copilot & Resume Intelligence).
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0005_ai_copilot_and_resumes"
down_revision = "0004_ai_and_proctoring"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Copilot Proposals Table
    op.create_table(
        "copilot_proposals",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("company_id", sa.Uuid(), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("created_by_user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("role_title", sa.String(length=255), nullable=False),
        sa.Column("seniority", sa.String(length=50), server_default=sa.text("'MID'"), nullable=False),
        sa.Column("target_skills", sa.JSON(), nullable=False),
        sa.Column("duration_minutes", sa.Integer(), server_default=sa.text("60"), nullable=False),
        sa.Column("status", sa.String(length=50), server_default=sa.text("'IN_REVIEW'"), nullable=False),
        sa.Column("proposed_items", sa.JSON(), nullable=False),
        sa.Column("review_notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    # 2. Resume Analyses Table
    op.create_table(
        "resume_analyses",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("company_id", sa.Uuid(), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("candidate_name", sa.String(length=255), nullable=False),
        sa.Column("candidate_email", sa.String(length=255), nullable=False, index=True),
        sa.Column("raw_resume_text", sa.Text(), nullable=True),
        sa.Column("extracted_skills", sa.JSON(), nullable=False),
        sa.Column("years_experience", sa.Float(), server_default=sa.text("0.0"), nullable=False),
        sa.Column("education_level", sa.String(length=100), server_default=sa.text("'Bachelor\'s'"), nullable=False),
        sa.Column("domain_tags", sa.JSON(), nullable=False),
        sa.Column("recommended_assessments", sa.JSON(), nullable=False),
        sa.Column("advisory_summary", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("resume_analyses")
    op.drop_table("copilot_proposals")
