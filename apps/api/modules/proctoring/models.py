"""
AssessIQ Proctoring & AI Evaluation domain models.
Extended with Phase 6 sensory events, risk tiers, explainable breakdown, and retention.
"""
import uuid
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, List, Dict, Any

from sqlalchemy import String, Boolean, Integer, Float, Text, ForeignKey, JSON, DateTime, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base
from core.mixins import UUIDPrimaryKeyMixin, TimestampMixin


class RiskLevel(str, Enum):
    NORMAL = "NORMAL"
    LOW_RISK = "LOW_RISK"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    HIGH_RISK = "HIGH_RISK"


class EventSeverity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ReviewStatus(str, Enum):
    PENDING = "PENDING"
    RESOLVED_CLEAN = "RESOLVED_CLEAN"
    RESOLVED_FLAGGED = "RESOLVED_FLAGGED"


class CandidateConsentRecord(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Explicit pre-exam candidate consent record for audio/video monitoring.
    """
    __tablename__ = "candidate_consent_records"

    attempt_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("assessment_attempts.id", ondelete="CASCADE"), unique=True, nullable=False, index=True
    )
    camera_consent_granted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    audio_consent_granted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    browser_monitoring_consent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    device_specs_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default=dict, nullable=True)


class ProctoringSession(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "proctoring_sessions"

    attempt_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("assessment_attempts.id", ondelete="CASCADE"), unique=True, nullable=False, index=True
    )
    integrity_score: Mapped[float] = mapped_column(Float, default=100.0, nullable=False)
    
    # Event Counters
    tab_switches_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    fullscreen_exits_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    paste_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    face_absence_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    multiple_faces_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    audio_spikes_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Risk Classification & Explainability
    risk_level: Mapped[str] = mapped_column(String(50), default=RiskLevel.NORMAL, nullable=False)
    is_flagged: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    weighted_deductions_json: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(JSON, default=list, nullable=True)
    summary_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Human Review Gate
    review_status: Mapped[str] = mapped_column(String(50), default=ReviewStatus.PENDING, nullable=False)
    reviewed_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    recruiter_verdict_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Data Retention (defaults to 90 days from creation)
    retention_expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    events = relationship("ProctoringEvent", back_populates="session", cascade="all, delete-orphan", lazy="noload")


class ProctoringEvent(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "proctoring_events"

    session_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("proctoring_sessions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), default=EventSeverity.LOW, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    metadata_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default=dict, nullable=True)

    session = relationship("ProctoringSession", back_populates="events", lazy="noload")


class AiEvaluationSummary(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "ai_evaluation_summaries"

    attempt_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("assessment_attempts.id", ondelete="CASCADE"), unique=True, nullable=False, index=True
    )
    recommendation: Mapped[str] = mapped_column(String(50), nullable=False)  # STRONG_HIRE, HIRE, BORDERLINE, REJECT
    overall_score_percentage: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    technical_depth_rating: Mapped[str] = mapped_column(String(50), default="MID_LEVEL", nullable=False)
    executive_summary: Mapped[str] = mapped_column(Text, nullable=False)
    strengths: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    weaknesses: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
