"""
Alembic migration – create Phase 8 tables (API Keys, Webhooks, SSO, Branding).
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0008_enterprise_readiness"
down_revision = "0007_subscriptions_and_billing"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Add branding fields to companies
    op.add_column("companies", sa.Column("logo_url", sa.String(length=2048), nullable=True))
    op.add_column("companies", sa.Column("primary_color", sa.String(length=7), nullable=True))

    # 2. Create API Keys table
    op.create_table(
        "api_keys",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("company_id", sa.Uuid(), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("key_hash", sa.String(length=255), unique=True, nullable=False),
        sa.Column("prefix", sa.String(length=10), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    # 3. Create Webhooks table
    op.create_table(
        "webhook_endpoints",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("company_id", sa.Uuid(), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("url", sa.String(length=2048), nullable=False),
        sa.Column("secret_key", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("events", sa.JSON(), server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    # 4. Create SSO Configs table
    op.create_table(
        "enterprise_sso_configs",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("company_id", sa.Uuid(), sa.ForeignKey("companies.id", ondelete="CASCADE"), unique=True, nullable=False, index=True),
        sa.Column("provider_type", sa.String(length=50), nullable=False),
        sa.Column("idp_entity_id", sa.String(length=255), nullable=True),
        sa.Column("idp_sso_url", sa.String(length=2048), nullable=True),
        sa.Column("idp_x509_cert", sa.String(length=4096), nullable=True),
        sa.Column("oidc_client_id", sa.String(length=255), nullable=True),
        sa.Column("oidc_client_secret", sa.String(length=255), nullable=True),
        sa.Column("oidc_issuer", sa.String(length=2048), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("enterprise_sso_configs")
    op.drop_table("webhook_endpoints")
    op.drop_table("api_keys")
    op.drop_column("companies", "primary_color")
    op.drop_column("companies", "logo_url")
