"""
AssessIQ Subscription & Billing domain models.
"""
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional

from sqlalchemy import String, Integer, DateTime, ForeignKey, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base
from core.mixins import UUIDPrimaryKeyMixin, TimestampMixin


class CompanySubscription(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "company_subscriptions"

    company_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), unique=True, nullable=False, index=True
    )
    plan_code: Mapped[str] = mapped_column(String(50), default="STARTER", nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="ACTIVE", nullable=False)  # ACTIVE, TRIALING, PAST_DUE, CANCELED
    monthly_candidate_limit: Mapped[int] = mapped_column(Integer, default=50, nullable=False)
    monthly_candidates_used: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    current_period_start: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )
    current_period_end: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.utcnow() + timedelta(days=30),
        nullable=False,
    )
    payment_provider: Mapped[Optional[str]] = mapped_column(String(50), default="MOCK", nullable=True)
    external_subscription_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
