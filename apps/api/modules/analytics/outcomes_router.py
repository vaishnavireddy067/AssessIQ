"""
Post-Hire Outcome Loop API (Phase 9).
Lets companies tag hired candidates' performance ratings back into AssessIQ
to correlate assessment scores with real on-the-job outcomes.
"""
import uuid
import datetime
import statistics
from typing import List, Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database import get_db
from dependencies import require_roles, CurrentUser
from core.rbac import RoleName
from core.exceptions import NotFoundError, ForbiddenError
from modules.analytics.models import CandidateEmploymentOutcome
from modules.assessments.models import AssessmentAttempt, Assessment

router = APIRouter()


class OutcomeCreateRequest(BaseModel):
    attempt_id: uuid.UUID
    performance_rating: int = Field(ge=1, le=5, description="1=Poor, 2=Below Average, 3=Average, 4=Good, 5=Exceptional")
    review_period_months: int = Field(default=6, ge=1, le=24)
    role_title: Optional[str] = None
    notes: Optional[str] = None


class OutcomeResponse(BaseModel):
    id: uuid.UUID
    attempt_id: uuid.UUID
    candidate_email: str
    assessment_score_pct: float
    performance_rating: int
    review_period_months: int
    role_title: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime.datetime

    class Config:
        from_attributes = True


class OutcomeCorrelationReport(BaseModel):
    total_outcomes: int
    avg_assessment_score: float
    avg_performance_rating: float
    correlation_summary: str
    high_scorers_avg_performance: float   # avg performance of candidates who scored >= 80%
    low_scorers_avg_performance: float    # avg performance of candidates who scored < 60%
    outcomes: List[OutcomeResponse]


RATING_LABELS = {1: "Poor", 2: "Below Average", 3: "Average", 4: "Good", 5: "Exceptional"}


@router.post("/outcomes", response_model=OutcomeResponse)
async def submit_employment_outcome(
    payload: OutcomeCreateRequest,
    current_user: CurrentUser = Depends(
        require_roles(RoleName.SUPER_ADMIN, RoleName.COMPANY_ADMIN)
    ),
    db: AsyncSession = Depends(get_db)
):
    """Tag a hired candidate's post-hire performance rating into AssessIQ."""
    att_stmt = select(AssessmentAttempt).where(AssessmentAttempt.id == payload.attempt_id)
    attempt = (await db.execute(att_stmt)).scalar_one_or_none()
    if not attempt:
        raise NotFoundError("AssessmentAttempt")

    ass_stmt = select(Assessment).where(Assessment.id == attempt.assessment_id)
    assessment = (await db.execute(ass_stmt)).scalar_one_or_none()
    if not assessment or (not current_user.is_super_admin() and assessment.company_id != current_user.company_id):
        raise ForbiddenError("Access forbidden")

    existing = (await db.execute(
        select(CandidateEmploymentOutcome).where(CandidateEmploymentOutcome.attempt_id == payload.attempt_id)
    )).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=409, detail="Outcome already recorded for this attempt.")

    outcome = CandidateEmploymentOutcome(
        attempt_id=payload.attempt_id,
        company_id=assessment.company_id,
        candidate_email=attempt.candidate_email,
        performance_rating=payload.performance_rating,
        review_period_months=payload.review_period_months,
        role_title=payload.role_title or assessment.title,
        notes=payload.notes,
        submitted_by=current_user.id,
    )
    db.add(outcome)
    await db.commit()
    await db.refresh(outcome)

    return OutcomeResponse(
        id=outcome.id,
        attempt_id=outcome.attempt_id,
        candidate_email=outcome.candidate_email,
        assessment_score_pct=attempt.percentage,
        performance_rating=outcome.performance_rating,
        review_period_months=outcome.review_period_months,
        role_title=outcome.role_title,
        notes=outcome.notes,
        created_at=outcome.created_at,
    )


@router.get("/outcomes/correlation", response_model=OutcomeCorrelationReport)
async def get_outcome_correlation_report(
    current_user: CurrentUser = Depends(
        require_roles(RoleName.SUPER_ADMIN, RoleName.COMPANY_ADMIN)
    ),
    db: AsyncSession = Depends(get_db)
):
    """
    Correlate assessment scores against post-hire performance ratings.
    Proves (or disproves) that high assessment scorers perform better on the job.
    """
    outcome_stmt = select(CandidateEmploymentOutcome).where(
        CandidateEmploymentOutcome.company_id == current_user.company_id
    ).order_by(CandidateEmploymentOutcome.created_at.desc())
    outcomes = (await db.execute(outcome_stmt)).scalars().all()

    if not outcomes:
        return OutcomeCorrelationReport(
            total_outcomes=0,
            avg_assessment_score=0.0,
            avg_performance_rating=0.0,
            correlation_summary="No post-hire outcomes recorded yet. Submit some outcomes first.",
            high_scorers_avg_performance=0.0,
            low_scorers_avg_performance=0.0,
            outcomes=[]
        )

    # Fetch attempt scores
    enriched = []
    for o in outcomes:
        att = (await db.execute(select(AssessmentAttempt).where(AssessmentAttempt.id == o.attempt_id))).scalar_one_or_none()
        enriched.append((o, att.percentage if att else 0.0))

    scores = [pct for _, pct in enriched]
    ratings = [o.performance_rating for o, _ in enriched]
    avg_score = round(statistics.mean(scores), 1)
    avg_rating = round(statistics.mean(ratings), 2)

    high_scorers = [o.performance_rating for o, pct in enriched if pct >= 80.0]
    low_scorers = [o.performance_rating for o, pct in enriched if pct < 60.0]
    high_avg = round(statistics.mean(high_scorers), 2) if high_scorers else 0.0
    low_avg = round(statistics.mean(low_scorers), 2) if low_scorers else 0.0

    if high_avg > low_avg + 0.5:
        summary = (
            f"✅ Positive correlation detected: High scorers (≥80%) averaged {high_avg}/5 performance "
            f"vs. {low_avg}/5 for low scorers (<60%). Your assessment is a strong predictor of job success."
        )
    elif high_avg < low_avg - 0.5:
        summary = (
            f"⚠️ Inverse correlation detected: Low scorers averaged better performance ({low_avg}/5). "
            f"Consider re-evaluating your question weighting or role alignment."
        )
    else:
        summary = (
            f"📊 Neutral correlation: Assessment scores show no strong predictor effect on performance "
            f"(avg score: {avg_score}%, avg rating: {avg_rating}/5). "
            f"More data points recommended for statistical significance."
        )

    outcome_responses = [
        OutcomeResponse(
            id=o.id,
            attempt_id=o.attempt_id,
            candidate_email=o.candidate_email,
            assessment_score_pct=pct,
            performance_rating=o.performance_rating,
            review_period_months=o.review_period_months,
            role_title=o.role_title,
            notes=o.notes,
            created_at=o.created_at,
        ) for o, pct in enriched
    ]

    return OutcomeCorrelationReport(
        total_outcomes=len(outcomes),
        avg_assessment_score=avg_score,
        avg_performance_rating=avg_rating,
        correlation_summary=summary,
        high_scorers_avg_performance=high_avg,
        low_scorers_avg_performance=low_avg,
        outcomes=outcome_responses,
    )
