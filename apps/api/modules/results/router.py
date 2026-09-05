"""
Results & Scorecards router — candidate assessment performance reports and question analysis for recruiters.
"""
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database import get_db
from core.rbac import RoleName
from core.exceptions import NotFoundError, ForbiddenError
from dependencies import get_current_user, require_roles, CurrentUser
from modules.assessments.models import (
    Assessment, AssessmentAttempt, CandidateAnswer, Question, QuestionOption,
    AttemptStatus
)

router = APIRouter()


# ── Schemas ───────────────────────────────────────────────────────────────────
class CandidateAttemptSummary(BaseModel):
    id: uuid.UUID
    candidate_email: str
    candidate_id: Optional[uuid.UUID] = None
    status: AttemptStatus
    total_score: float
    max_score: float
    percentage: float
    passed: bool
    started_at: datetime
    submitted_at: Optional[datetime] = None
    # Phase 9: Explainable AI Ranking
    ai_ranking_rationale: Optional[str] = None

    class Config:
        from_attributes = True


class QuestionScorecardItem(BaseModel):
    question_id: uuid.UUID
    title: str
    content_markdown: str
    points: float
    score_awarded: float
    is_correct: bool
    explanation: Optional[str] = None
    selected_option_ids: List[str]
    options: List[Dict[str, Any]]  # id, option_text, is_correct


class ScorecardDetailResponse(BaseModel):
    attempt_id: uuid.UUID
    assessment_id: uuid.UUID
    assessment_title: str
    candidate_email: str
    status: AttemptStatus
    total_score: float
    max_score: float
    percentage: float
    passed: bool
    passing_score_percentage: float
    started_at: datetime
    submitted_at: Optional[datetime] = None
    questions: List[QuestionScorecardItem]
    # Phase 9: AI rationale
    ai_ranking_rationale: Optional[str] = None


# ── Routes ────────────────────────────────────────────────────────────────────
@router.get("/assessments/{assessment_id}/results", response_model=List[CandidateAttemptSummary])
async def list_assessment_results(
    assessment_id: uuid.UUID,
    current_user: CurrentUser = Depends(
        require_roles(RoleName.SUPER_ADMIN, RoleName.COMPANY_ADMIN, RoleName.RECRUITER)
    ),
    db: AsyncSession = Depends(get_db),
):
    """List all candidate test attempts for an assessment."""
    stmt = select(Assessment).where(Assessment.id == assessment_id, Assessment.deleted_at.is_(None))
    if not current_user.is_super_admin():
        stmt = stmt.where(Assessment.company_id == current_user.company_id)

    assessment = (await db.execute(stmt)).scalar_one_or_none()
    if not assessment:
        raise NotFoundError("Assessment")

    att_stmt = (
        select(AssessmentAttempt)
        .where(AssessmentAttempt.assessment_id == assessment_id)
        .order_by(AssessmentAttempt.created_at.desc())
    )
    attempts = (await db.execute(att_stmt)).scalars().all()
    return attempts


@router.get("/results/{attempt_id}", response_model=ScorecardDetailResponse)
async def get_attempt_scorecard(
    attempt_id: uuid.UUID,
    current_user: CurrentUser = Depends(
        require_roles(RoleName.SUPER_ADMIN, RoleName.COMPANY_ADMIN, RoleName.RECRUITER)
    ),
    db: AsyncSession = Depends(get_db),
):
    """View detailed candidate scorecard with question-by-question breakdown."""
    att_stmt = select(AssessmentAttempt).where(AssessmentAttempt.id == attempt_id)
    attempt = (await db.execute(att_stmt)).scalar_one_or_none()
    if not attempt:
        raise NotFoundError("AssessmentAttempt")

    ass_stmt = select(Assessment).where(Assessment.id == attempt.assessment_id)
    assessment = (await db.execute(ass_stmt)).scalar_one_or_none()
    if not assessment:
        raise NotFoundError("Assessment")

    if not current_user.is_super_admin() and assessment.company_id != current_user.company_id:
        raise ForbiddenError("Access to this scorecard is forbidden")

    # Load candidate answers
    ans_stmt = select(CandidateAnswer).where(CandidateAnswer.attempt_id == attempt.id)
    answers = (await db.execute(ans_stmt)).scalars().all()
    ans_map = {str(a.question_id): a for a in answers}

    # Load questions
    scorecard_items = []
    for q_id_str, ans in ans_map.items():
        q_stmt = select(Question).where(Question.id == uuid.UUID(q_id_str))
        q = (await db.execute(q_stmt)).scalar_one_or_none()
        if not q:
            continue

        opt_stmt = select(QuestionOption).where(QuestionOption.question_id == q.id).order_by(QuestionOption.order_index.asc())
        options = (await db.execute(opt_stmt)).scalars().all()

        scorecard_items.append(
            QuestionScorecardItem(
                question_id=q.id,
                title=q.title,
                content_markdown=q.content_markdown,
                points=q.points,
                score_awarded=ans.score_awarded,
                is_correct=ans.is_correct,
                explanation=q.explanation,
                selected_option_ids=ans.selected_option_ids,
                options=[
                    {
                        "id": str(o.id),
                        "option_text": o.option_text,
                        "is_correct": o.is_correct,
                    }
                    for o in options
                ],
            )
        )

    return ScorecardDetailResponse(
        attempt_id=attempt.id,
        assessment_id=assessment.id,
        assessment_title=assessment.title,
        candidate_email=attempt.candidate_email,
        status=attempt.status,
        total_score=attempt.total_score,
        max_score=attempt.max_score,
        percentage=attempt.percentage,
        passed=attempt.passed,
        passing_score_percentage=assessment.passing_score_percentage,
        started_at=attempt.started_at,
        submitted_at=attempt.submitted_at,
        questions=scorecard_items,
        ai_ranking_rationale=attempt.ai_ranking_rationale,
    )
