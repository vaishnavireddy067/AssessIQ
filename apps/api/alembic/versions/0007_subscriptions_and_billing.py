"""
Alembic migration – create Phase 7 tables (Company Subscriptions & Billing).
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0007_subscriptions_and_billing"
down_revision = "0006_proctoring_intelligence"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "company_subscriptions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("company_id", sa.Uuid(), sa.ForeignKey("companies.id", ondelete="CASCADE"), unique=True, nullable=False, index=True),
        sa.Column("plan_code", sa.String(length=50), server_default=sa.text("'STARTER'"), nullable=False),
        sa.Column("status", sa.String(length=50), server_default=sa.text("'ACTIVE'"), nullable=False),
        sa.Column("monthly_candidate_limit", sa.Integer(), server_default=sa.text("50"), nullable=False),
        sa.Column("monthly_candidates_used", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("current_period_start", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("current_period_end", sa.DateTime(timezone=True), server_default=sa.text("now() + interval '30 days'"), nullable=False),
        sa.Column("payment_provider", sa.String(length=50), server_default=sa.text("'MOCK'"), nullable=True),
        sa.Column("external_subscription_id", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("company_subscriptions")
