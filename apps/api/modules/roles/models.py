"""
Role and UserRole models for RBAC.
"""
import uuid
from typing import Optional

from sqlalchemy import String, ForeignKey, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base
from core.mixins import UUIDPrimaryKeyMixin, TimestampMixin


class Role(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "roles"

    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    user_roles = relationship("UserRole", back_populates="role", lazy="noload")

    def __repr__(self):
        return f"<Role id={self.id} name={self.name}>"


class UserRole(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "user_roles"
    __table_args__ = (UniqueConstraint("user_id", "role_id", "company_id", name="uq_user_role_company"),)

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    role_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("roles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # Nullable – NULL for GLOBAL roles like CANDIDATE
    company_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=True, index=True
    )

    user = relationship("User", back_populates="user_roles", lazy="noload")
    role = relationship("Role", back_populates="user_roles", lazy="noload")
    company = relationship("Company", back_populates="user_roles", lazy="noload")

    def __repr__(self):
        return f"<UserRole user_id={self.user_id} role_id={self.role_id} company_id={self.company_id}>"
