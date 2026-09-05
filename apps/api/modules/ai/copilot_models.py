"""
AssessIQ AI Copilot, Proposal Management, and Resume Intelligence Domain Models.
"""
import uuid
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any

from sqlalchemy import String, Boolean, Integer, Float, Text, ForeignKey, JSON, DateTime, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base
from core.mixins import UUIDPrimaryKeyMixin, TimestampMixin


class ProposalStatus(str, Enum):
    DRAFT = "DRAFT"
    IN_REVIEW = "IN_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class CopilotProposal(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    AI Copilot assessment generation proposal.
    Stores draft questions in IN_REVIEW state requiring human question manager approval.
    """
    __tablename__ = "copilot_proposals"

    company_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    created_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    role_title: Mapped[str] = mapped_column(String(255), nullable=False)
    seniority: Mapped[str] = mapped_column(String(50), default="MID", nullable=False)  # JUNIOR, MID, SENIOR
    target_skills: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    duration_minutes: Mapped[int] = mapped_column(Integer, default=60, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default=ProposalStatus.IN_REVIEW, nullable=False)
    
    # Structure: list of questions with status, duplicate_warning, type, options/starter_code
    proposed_items: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)
    review_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class ResumeAnalysis(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Candidate resume analysis results.
    Provides advisory-only skill extractions and assessment recommendations.
    """
    __tablename__ = "resume_analyses"

    company_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    candidate_name: Mapped[str] = mapped_column(String(255), nullable=False)
    candidate_email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    raw_resume_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Extracted metadata
    extracted_skills: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    years_experience: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    education_level: Mapped[str] = mapped_column(String(100), default="Bachelor's", nullable=False)
    domain_tags: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    
    # Recommendations (Advisory Only - never auto-rejects/auto-assigns)
    recommended_assessments: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)
    advisory_summary: Mapped[str] = mapped_column(Text, nullable=False)
