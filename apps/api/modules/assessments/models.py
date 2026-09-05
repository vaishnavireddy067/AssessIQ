"""
AssessIQ Assessment Engine Models
Includes QuestionBanks, Questions, Options, Assessments, Invitations, Attempts, and Answers.
"""
import uuid
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any

from sqlalchemy import String, Boolean, Integer, Float, Text, ForeignKey, JSON, DateTime, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base
from core.mixins import UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin


# ── Enums ─────────────────────────────────────────────────────────────────────
class QuestionType(str, Enum):
    MCQ_SINGLE = "MCQ_SINGLE"
    MCQ_MULTIPLE = "MCQ_MULTIPLE"
    TRUE_FALSE = "TRUE_FALSE"


class DifficultyLevel(str, Enum):
    EASY = "EASY"
    MEDIUM = "MEDIUM"
    HARD = "HARD"


class AssessmentStatus(str, Enum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    ARCHIVED = "ARCHIVED"


class InvitationStatus(str, Enum):
    PENDING = "PENDING"
    STARTED = "STARTED"
    COMPLETED = "COMPLETED"
    EXPIRED = "EXPIRED"


class AttemptStatus(str, Enum):
    IN_PROGRESS = "IN_PROGRESS"
    SUBMITTED = "SUBMITTED"
    EVALUATED = "EVALUATED"
    TIMED_OUT = "TIMED_OUT"


# ── Question Bank & Questions ─────────────────────────────────────────────────
class QuestionBank(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "question_banks"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    category: Mapped[str] = mapped_column(String(100), default="General", nullable=False)
    company_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=True, index=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    questions = relationship("Question", back_populates="bank", cascade="all, delete-orphan", lazy="noload")


class Question(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "questions"

    bank_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("question_banks.id", ondelete="CASCADE"), nullable=False, index=True
    )
    company_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=True, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content_markdown: Mapped[str] = mapped_column(Text, nullable=False)
    question_type: Mapped[QuestionType] = mapped_column(String(50), default=QuestionType.MCQ_SINGLE, nullable=False)
    difficulty: Mapped[DifficultyLevel] = mapped_column(String(50), default=DifficultyLevel.MEDIUM, nullable=False)
    points: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    explanation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tags: Mapped[Optional[List[str]]] = mapped_column(JSON, default=list, nullable=True)

    # Phase 9: Leak Radar
    usage_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    leak_risk_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    leak_last_checked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    is_suspected_leaked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    bank = relationship("QuestionBank", back_populates="questions", lazy="noload")
    options = relationship("QuestionOption", back_populates="question", cascade="all, delete-orphan", lazy="noload")
    assessment_links = relationship("AssessmentQuestion", back_populates="question", cascade="all, delete-orphan", lazy="noload")


class QuestionOption(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "question_options"

    question_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("questions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    option_text: Mapped[str] = mapped_column(Text, nullable=False)
    is_correct: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    question = relationship("Question", back_populates="options", lazy="noload")


# ── Assessment & Assessment Questions ─────────────────────────────────────────
class Assessment(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "assessments"

    company_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    instructions: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    duration_minutes: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    passing_score_percentage: Mapped[float] = mapped_column(Float, default=60.0, nullable=False)
    shuffle_questions: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    shuffle_options: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    proctoring_mode: Mapped[str] = mapped_column(String(50), default="STANDARD", nullable=False)
    company_pattern: Mapped[str] = mapped_column(String(50), default="CUSTOM", nullable=False)
    drive_start_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    drive_end_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    sections_config: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default=dict, nullable=True)
    allow_section_switching: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    status: Mapped[AssessmentStatus] = mapped_column(String(50), default=AssessmentStatus.DRAFT, nullable=False)
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    questions = relationship("AssessmentQuestion", back_populates="assessment", cascade="all, delete-orphan", lazy="noload")
    invitations = relationship("CandidateInvitation", back_populates="assessment", cascade="all, delete-orphan", lazy="noload")
    attempts = relationship("AssessmentAttempt", back_populates="assessment", cascade="all, delete-orphan", lazy="noload")


class AssessmentQuestion(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "assessment_questions"
    __table_args__ = (UniqueConstraint("assessment_id", "question_id", name="uq_assessment_question"),)

    assessment_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False, index=True
    )
    question_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("questions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    section_name: Mapped[Optional[str]] = mapped_column(String(100), default="General", nullable=True)
    order_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    points_override: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    assessment = relationship("Assessment", back_populates="questions", lazy="noload")
    question = relationship("Question", back_populates="assessment_links", lazy="noload")


# ── Invitations & Attempts ───────────────────────────────────────────────────
class CandidateInvitation(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "candidate_invitations"

    company_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    assessment_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False, index=True
    )
    candidate_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("candidates.id", ondelete="SET NULL"), nullable=True, index=True
    )
    candidate_email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    candidate_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    token: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    status: Mapped[InvitationStatus] = mapped_column(String(50), default=InvitationStatus.PENDING, nullable=False)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    invited_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    assessment = relationship("Assessment", back_populates="invitations", lazy="noload")
    attempts = relationship("AssessmentAttempt", back_populates="invitation", lazy="noload")


class AssessmentAttempt(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "assessment_attempts"

    invitation_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("candidate_invitations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    assessment_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False, index=True
    )
    candidate_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("candidates.id", ondelete="SET NULL"), nullable=True, index=True
    )
    candidate_email: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[AttemptStatus] = mapped_column(String(50), default=AttemptStatus.IN_PROGRESS, nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    submitted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    total_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    max_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    percentage: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    passed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Phase 9: AI ranking rationale
    ai_ranking_rationale: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    assessment = relationship("Assessment", back_populates="attempts", lazy="noload")
    invitation = relationship("CandidateInvitation", back_populates="attempts", lazy="noload")
    answers = relationship("CandidateAnswer", back_populates="attempt", cascade="all, delete-orphan", lazy="noload")


class CandidateAnswer(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "candidate_answers"
    __table_args__ = (UniqueConstraint("attempt_id", "question_id", name="uq_attempt_question_answer"),)

    attempt_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("assessment_attempts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    question_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("questions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    selected_option_ids: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    is_correct: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    score_awarded: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    answered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    attempt = relationship("AssessmentAttempt", back_populates="answers", lazy="noload")
    question = relationship("Question", lazy="noload")


# ── Assessment Pattern Templates ──────────────────────────────────────────────
class AssessmentTemplate(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "assessment_templates"

    company_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=True, index=True
    )
    key: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(50), default="CUSTOM", nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    icon: Mapped[str] = mapped_column(String(50), default="Layers", nullable=False)
    color: Mapped[str] = mapped_column(String(50), default="#6366F1", nullable=False)
    duration_minutes: Mapped[int] = mapped_column(Integer, default=60, nullable=False)
    passing_score_percentage: Mapped[float] = mapped_column(Float, default=60.0, nullable=False)
    allow_section_switching: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    sections_config: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default=dict, nullable=True)
    features: Mapped[Optional[List[str]]] = mapped_column(JSON, default=list, nullable=True)
    usage_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_public: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
