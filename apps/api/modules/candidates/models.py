"""
Candidate models – global (company_id nullable) because a candidate may belong to multiple companies.
"""
import uuid
from typing import Optional

from sqlalchemy import String, Text, ForeignKey, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base
from core.mixins import UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin


class Candidate(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "candidates"

    # No company_id – candidates are global and can be invited by many companies.
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    resume_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # Additional profile fields can be added later (skills, experience, etc.)

    user = relationship("User", back_populates="candidate_profile", lazy="noload")
    # Relationship to invitations / attempts will be defined in later phases.

    def __repr__(self):
        return f"<Candidate id={self.id} user_id={self.user_id}>"
