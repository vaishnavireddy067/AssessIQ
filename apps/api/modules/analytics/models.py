"""
Phase 9 Advanced Models:
- CandidateSkillPassport / SkillPassportEntry (Verified Skill Passport)
- PanelReviewRequest / PanelReviewVote (Panel Review Workflow)
- CandidateEmploymentOutcome (Post-Hire Outcome Loop)
"""
import uuid
import datetime
from typing import Optional, List
from sqlalchemy import String, Float, Integer, Boolean, DateTime, Text, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy import Uuid
from database import Base
from core.mixins import UUIDPrimaryKeyMixin, TimestampMixin


class CandidateSkillPassport(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    A portable, candidate-owned global skill profile built from all their assessments.
    Scoped by email (cross-company), not by company_id.
    """
    __tablename__ = "candidate_skill_passports"

    candidate_email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    display_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Overall statistics
    total_assessments_taken: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    avg_overall_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    
    # The passport is publicly shareable via a unique token
    share_token: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    entries = relationship("SkillPassportEntry", back_populates="passport", cascade="all, delete-orphan")


class SkillPassportEntry(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    One skill dimension in a candidate's passport (e.g. Python: 91%).
    Aggregated from all their attempts across all companies.
    """
    __tablename__ = "skill_passport_entries"

    passport_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("candidate_skill_passports.id", ondelete="CASCADE"), nullable=False, index=True)
    skill_name: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g. "Python", "SQL", "DSA"
    avg_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    best_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    attempts_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    last_assessed_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    passport = relationship("CandidateSkillPassport", back_populates="entries")


class PanelReviewRequest(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Triggered when a borderline candidate (60-75%) needs multi-recruiter review.
    """
    __tablename__ = "panel_review_requests"

    attempt_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("assessment_attempts.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    company_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(50), default="PENDING", nullable=False)  # PENDING, APPROVED, REJECTED, ESCALATED
    required_votes: Mapped[int] = mapped_column(Integer, default=2, nullable=False)
    
    votes = relationship("PanelReviewVote", back_populates="review_request", cascade="all, delete-orphan")


class PanelReviewVote(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    A single recruiter's vote on a panel review.
    """
    __tablename__ = "panel_review_votes"

    review_request_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("panel_review_requests.id", ondelete="CASCADE"), nullable=False, index=True)
    recruiter_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    verdict: Mapped[str] = mapped_column(String(20), nullable=False)  # HIRE, REJECT, NEEDS_MORE_INFO
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    review_request = relationship("PanelReviewRequest", back_populates="votes")


class CandidateEmploymentOutcome(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Post-hire performance feedback to close the assessment loop.
    Optional: company HR tags a hired candidate's 6-month performance rating back.
    """
    __tablename__ = "candidate_employment_outcomes"

    attempt_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("assessment_attempts.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    company_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    candidate_email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    
    # Performance rating 1-5 (1=Poor, 5=Exceptional)
    performance_rating: Mapped[int] = mapped_column(Integer, nullable=False)
    review_period_months: Mapped[int] = mapped_column(Integer, default=6, nullable=False)
    role_title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    submitted_by: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
