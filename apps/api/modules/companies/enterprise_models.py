"""
AssessIQ Enterprise Readiness Models (Phase 8).
Contains models for Webhooks, API Keys, and SSO configurations.
"""
import uuid
import secrets
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import String, Integer, DateTime, ForeignKey, Uuid, Boolean, JSON, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from database import Base
from core.mixins import UUIDPrimaryKeyMixin, TimestampMixin


class WebhookEvent(str, enum.Enum):
    CANDIDATE_SUBMITTED = "candidate.submitted"
    ASSESSMENT_PUBLISHED = "assessment.published"
    PROCTORING_FLAGGED = "proctoring.flagged"


class ApiKey(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Programmatic API keys for ATS integrations."""
    __tablename__ = "api_keys"

    company_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    # The hashed API key. Raw key is only shown once at creation.
    key_hash: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    prefix: Mapped[str] = mapped_column(String(10), nullable=False)  # First few chars for identification
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    company = relationship("Company")


class WebhookEndpoint(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """External endpoints to receive event payloads."""
    __tablename__ = "webhook_endpoints"

    company_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    url: Mapped[str] = mapped_column(String(2048), nullable=False)
    secret_key: Mapped[str] = mapped_column(String(255), nullable=False, default=lambda: secrets.token_hex(32))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    events: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)

    company = relationship("Company")


class EnterpriseSSOConfig(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """SSO Identity Provider configuration (SAML/OIDC)."""
    __tablename__ = "enterprise_sso_configs"

    company_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), unique=True, nullable=False, index=True
    )
    provider_type: Mapped[str] = mapped_column(String(50), nullable=False) # e.g. "SAML", "OIDC"
    idp_entity_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    idp_sso_url: Mapped[Optional[str]] = mapped_column(String(2048), nullable=True)
    idp_x509_cert: Mapped[Optional[str]] = mapped_column(String(4096), nullable=True)
    oidc_client_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    oidc_client_secret: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    oidc_issuer: Mapped[Optional[str]] = mapped_column(String(2048), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    company = relationship("Company")
