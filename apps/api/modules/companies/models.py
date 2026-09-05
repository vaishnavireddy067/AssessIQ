"""Companies domain models."""
import uuid
from enum import Enum
from typing import Optional

from sqlalchemy import String, Boolean, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from database import Base
from core.mixins import UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin


class CompanyPlan(str, Enum):
    STARTER = "STARTER"
    BUSINESS = "BUSINESS"
    ENTERPRISE = "ENTERPRISE"


class Company(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "companies"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    domain: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    logo_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    website: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    industry: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    size: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    plan: Mapped[CompanyPlan] = mapped_column(
        String(50), default=CompanyPlan.STARTER, nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Enterprise Branding
    primary_color: Mapped[Optional[str]] = mapped_column(String(7), nullable=True)  # HEX color e.g., #FF0000

    # Relationships
    users: Mapped[list["User"]] = relationship(
        "User", back_populates="company", cascade="all, delete-orphan"
    )
    user_roles = relationship("UserRole", back_populates="company", lazy="noload")

    def __repr__(self):
        return f"<Company id={self.id} name={self.name} plan={self.plan}>"
