"""
Alembic migration – create Phase 9 tables (Proctoring Mode, AI Ranking Rationale).
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0009_phase9_analytics"
down_revision = "0008_enterprise_readiness"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add proctoring_mode to assessments
    op.add_column("assessments", sa.Column("proctoring_mode", sa.String(length=50), server_default=sa.text("'STANDARD'"), nullable=False))
    
    # Add ai_ranking_rationale to assessment_attempts
    op.add_column("assessment_attempts", sa.Column("ai_ranking_rationale", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("assessment_attempts", "ai_ranking_rationale")
    op.drop_column("assessments", "proctoring_mode")
