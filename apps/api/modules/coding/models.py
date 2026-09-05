"""
AssessIQ Coding & SQL Problem domain models.
"""
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any

from sqlalchemy import String, Boolean, Integer, Float, Text, ForeignKey, JSON, DateTime, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base
from core.mixins import UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin
from modules.assessments.models import DifficultyLevel


class CodingProblem(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "coding_problems"

    company_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=True, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    description_markdown: Mapped[str] = mapped_column(Text, nullable=False)
    difficulty: Mapped[DifficultyLevel] = mapped_column(String(50), default=DifficultyLevel.MEDIUM, nullable=False)
    time_limit_ms: Mapped[int] = mapped_column(Integer, default=2000, nullable=False)
    memory_limit_mb: Mapped[int] = mapped_column(Integer, default=256, nullable=False)
    starter_code: Mapped[Dict[str, str]] = mapped_column(JSON, default=dict, nullable=False)
    solution_code: Mapped[Optional[Dict[str, str]]] = mapped_column(JSON, nullable=True)
    points: Mapped[float] = mapped_column(Float, default=10.0, nullable=False)
    tags: Mapped[Optional[List[str]]] = mapped_column(JSON, default=list, nullable=True)

    test_cases = relationship("CodingTestCase", back_populates="problem", cascade="all, delete-orphan", lazy="noload")
    submissions = relationship("CandidateCodeSubmission", back_populates="problem", cascade="all, delete-orphan", lazy="noload")


class CodingTestCase(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "coding_test_cases"

    problem_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("coding_problems.id", ondelete="CASCADE"), nullable=False, index=True
    )
    input_data: Mapped[str] = mapped_column(Text, nullable=False)
    expected_output: Mapped[str] = mapped_column(Text, nullable=False)
    is_hidden: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    explanation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    problem = relationship("CodingProblem", back_populates="test_cases", lazy="noload")


class SqlProblem(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "sql_problems"

    company_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=True, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    description_markdown: Mapped[str] = mapped_column(Text, nullable=False)
    difficulty: Mapped[DifficultyLevel] = mapped_column(String(50), default=DifficultyLevel.MEDIUM, nullable=False)
    schema_sql: Mapped[str] = mapped_column(Text, nullable=False)
    solution_sql: Mapped[str] = mapped_column(Text, nullable=False)
    points: Mapped[float] = mapped_column(Float, default=10.0, nullable=False)
    tags: Mapped[Optional[List[str]]] = mapped_column(JSON, default=list, nullable=True)

    submissions = relationship("CandidateSqlSubmission", back_populates="problem", cascade="all, delete-orphan", lazy="noload")


class CandidateCodeSubmission(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "candidate_code_submissions"

    attempt_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("assessment_attempts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    problem_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("coding_problems.id", ondelete="CASCADE"), nullable=False, index=True
    )
    language: Mapped[str] = mapped_column(String(50), default="python", nullable=False)
    code: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="PENDING", nullable=False)
    passed_test_cases: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_test_cases: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    execution_time_ms: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    output_logs: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    score_awarded: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    problem = relationship("CodingProblem", back_populates="submissions", lazy="noload")


class CandidateSqlSubmission(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "candidate_sql_submissions"

    attempt_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("assessment_attempts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    problem_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("sql_problems.id", ondelete="CASCADE"), nullable=False, index=True
    )
    query: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="PENDING", nullable=False)
    execution_time_ms: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    output_preview: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    score_awarded: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    problem = relationship("SqlProblem", back_populates="submissions", lazy="noload")
