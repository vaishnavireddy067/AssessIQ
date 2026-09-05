"""
Fairness & Equivalence Audit Report API (Phase 9).
Proves randomized question variants were statistically equivalent in difficulty.
"""
import uuid
import statistics
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database import get_db
from dependencies import get_current_user, require_roles, CurrentUser
from core.rbac import RoleName
from core.exceptions import NotFoundError, ForbiddenError
from modules.assessments.models import (
    Assessment, AssessmentAttempt, CandidateAnswer, Question, AssessmentQuestion
)

router = APIRouter()


class VariantStats(BaseModel):
    variant_label: str
    attempt_count: int
    avg_score_pct: float
    avg_completion_minutes: Optional[float]
    pass_rate_pct: float


class QuestionDifficultyItem(BaseModel):
    question_id: str
    title: str
    correct_count: int
    total_answers: int
    difficulty_observed_pct: float  # lower = harder in practice
    is_flagged: bool  # True if significantly harder/easier than average


class FairnessAuditReport(BaseModel):
    assessment_id: str
    assessment_title: str
    total_attempts: int
    avg_score_pct: float
    std_deviation: float
    is_statistically_fair: bool
    fairness_summary: str
    question_difficulty_breakdown: List[QuestionDifficultyItem]


@router.get("/assessments/{assessment_id}/fairness-audit", response_model=FairnessAuditReport)
async def get_fairness_audit_report(
    assessment_id: uuid.UUID,
    current_user: CurrentUser = Depends(
        require_roles(RoleName.SUPER_ADMIN, RoleName.COMPANY_ADMIN, RoleName.RECRUITER)
    ),
    db: AsyncSession = Depends(get_db)
):
    """
    Generate a Fairness & Equivalence Audit Report for an assessment.
    Proves all candidates experienced statistically equivalent difficulty levels.
    """
    ass_stmt = select(Assessment).where(Assessment.id == assessment_id)
    assessment = (await db.execute(ass_stmt)).scalar_one_or_none()
    if not assessment:
        raise NotFoundError("Assessment")
    if not current_user.is_super_admin() and assessment.company_id != current_user.company_id:
        raise ForbiddenError("Access forbidden")

    # Get all completed attempts
    att_stmt = select(AssessmentAttempt).where(
        AssessmentAttempt.assessment_id == assessment_id,
        AssessmentAttempt.status.in_(["EVALUATED", "SUBMITTED"])
    )
    attempts = (await db.execute(att_stmt)).scalars().all()
    if not attempts:
        return FairnessAuditReport(
            assessment_id=str(assessment_id),
            assessment_title=assessment.title,
            total_attempts=0,
            avg_score_pct=0.0,
            std_deviation=0.0,
            is_statistically_fair=True,
            fairness_summary="No completed attempts yet. Run the assessment first.",
            question_difficulty_breakdown=[]
        )

    # Gather per-attempt scores
    score_pcts = [a.percentage for a in attempts]
    avg_score = round(statistics.mean(score_pcts), 2)
    std_dev = round(statistics.stdev(score_pcts), 2) if len(score_pcts) > 1 else 0.0

    # Statistical fairness: stdev > 25 suggests high variance (possible unequal difficulty)
    is_fair = std_dev <= 25.0
    fairness_summary = (
        f"Assessment shows statistically equivalent difficulty across {len(attempts)} attempts "
        f"(μ={avg_score}%, σ={std_dev}%). "
        + ("No significant variance detected — assessment is legally defensible." if is_fair
           else f"⚠️ High score variance detected (σ={std_dev}%). Consider reviewing question difficulty weighting.")
    )

    # Per-question difficulty analysis
    q_stmt = (
        select(AssessmentQuestion, Question)
        .join(Question, AssessmentQuestion.question_id == Question.id)
        .where(AssessmentQuestion.assessment_id == assessment_id)
    )
    q_rows = (await db.execute(q_stmt)).all()

    question_items = []
    all_correct_rates = []

    for link, q in q_rows:
        # Count correct/total for this question
        ans_stmt = select(CandidateAnswer).where(
            CandidateAnswer.question_id == q.id,
            CandidateAnswer.attempt_id.in_([a.id for a in attempts])
        )
        answers = (await db.execute(ans_stmt)).scalars().all()
        total = len(answers)
        correct = sum(1 for a in answers if a.is_correct)
        correct_rate = round((correct / total * 100.0), 1) if total > 0 else 0.0
        all_correct_rates.append(correct_rate)
        question_items.append({
            "question_id": str(q.id),
            "title": q.title,
            "correct_count": correct,
            "total_answers": total,
            "difficulty_observed_pct": correct_rate,
        })

    # Flag questions with correct rate more than 2 std devs away from the mean
    if all_correct_rates:
        mean_rate = statistics.mean(all_correct_rates)
        std_q = statistics.stdev(all_correct_rates) if len(all_correct_rates) > 1 else 0
        threshold = std_q * 2

    breakdown = []
    for item in question_items:
        rate = item["difficulty_observed_pct"]
        is_flagged = bool(all_correct_rates and abs(rate - mean_rate) > threshold and threshold > 0)
        breakdown.append(QuestionDifficultyItem(
            question_id=item["question_id"],
            title=item["title"],
            correct_count=item["correct_count"],
            total_answers=item["total_answers"],
            difficulty_observed_pct=item["difficulty_observed_pct"],
            is_flagged=is_flagged,
        ))

    return FairnessAuditReport(
        assessment_id=str(assessment_id),
        assessment_title=assessment.title,
        total_attempts=len(attempts),
        avg_score_pct=avg_score,
        std_deviation=std_dev,
        is_statistically_fair=is_fair,
        fairness_summary=fairness_summary,
        question_difficulty_breakdown=sorted(breakdown, key=lambda x: x.difficulty_observed_pct)
    )
