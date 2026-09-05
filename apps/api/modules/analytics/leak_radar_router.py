"""
Leak Radar — Question Integrity Monitoring (Phase 9).
Detects if question text has appeared on public platforms (Chegg, GitHub, forums).
Uses a lightweight web-search heuristic (simulated for local dev).
"""
import uuid
import hashlib
import datetime
from typing import List
from pydantic import BaseModel
from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_

from database import get_db
from dependencies import require_roles, CurrentUser
from core.rbac import RoleName
from core.exceptions import NotFoundError, ForbiddenError
from modules.assessments.models import Question

router = APIRouter()


class LeakRadarResult(BaseModel):
    question_id: str
    title: str
    usage_count: int
    leak_risk_score: float
    is_suspected_leaked: bool
    leak_last_checked_at: datetime.datetime | None
    recommendation: str


class LeakRadarReport(BaseModel):
    total_questions_checked: int
    high_risk_count: int
    questions: List[LeakRadarResult]


def _compute_leak_risk(q: Question) -> float:
    """
    Heuristic leak risk scoring without an actual web search.
    Bases risk on:
      - Usage count (more uses = more exposure)
      - Age of question (older = higher risk)
    In production, this would call a Search API (e.g., Bing/Google Custom Search).
    """
    usage_score = min(q.usage_count * 5.0, 50.0)  # max 50 pts from usage
    
    # Age factor: questions older than 90 days get additional risk
    age_days = 0
    if q.created_at:
        age_days = (datetime.datetime.now(datetime.timezone.utc) - q.created_at).days
    age_score = min(age_days / 3.0, 40.0)  # max 40 pts from age
    
    # Difficulty factor: easier questions get shared more
    difficulty_bonus = {"EASY": 10.0, "MEDIUM": 5.0, "HARD": 0.0}.get(str(q.difficulty).upper(), 0.0)
    
    total = usage_score + age_score + difficulty_bonus
    return round(min(total, 100.0), 1)


def _get_recommendation(score: float, is_flagged: bool) -> str:
    if is_flagged or score >= 75.0:
        return "⛔ RETIRE or ROTATE — High leak risk. Replace with fresh questions immediately."
    elif score >= 50.0:
        return "⚠️ REVIEW — Moderate exposure. Consider retiring after next assessment cycle."
    else:
        return "✅ SAFE — Low leak risk. No action required."


async def _run_leak_scan_for_company(company_id: uuid.UUID, db: AsyncSession):
    """
    Background task: scans all company questions and updates leak risk scores.
    """
    q_stmt = select(Question).where(Question.company_id == company_id, Question.deleted_at.is_(None))
    questions = (await db.execute(q_stmt)).scalars().all()

    for q in questions:
        risk_score = _compute_leak_risk(q)
        q.leak_risk_score = risk_score
        q.is_suspected_leaked = risk_score >= 75.0
        q.leak_last_checked_at = datetime.datetime.now(datetime.timezone.utc)

    await db.commit()


@router.post("/questions/leak-scan")
async def trigger_leak_scan(
    background_tasks: BackgroundTasks,
    current_user: CurrentUser = Depends(
        require_roles(RoleName.SUPER_ADMIN, RoleName.COMPANY_ADMIN)
    ),
    db: AsyncSession = Depends(get_db)
):
    """Trigger a background Leak Radar scan for the company's question bank."""
    background_tasks.add_task(_run_leak_scan_for_company, current_user.company_id, db)
    return {"status": "Leak Radar scan triggered. Results will be available in a few seconds."}


@router.get("/questions/leak-radar", response_model=LeakRadarReport)
async def get_leak_radar_report(
    current_user: CurrentUser = Depends(
        require_roles(RoleName.SUPER_ADMIN, RoleName.COMPANY_ADMIN, RoleName.RECRUITER)
    ),
    db: AsyncSession = Depends(get_db)
):
    """
    Returns the Leak Radar report for all questions — sorted by leak risk score (highest first).
    """
    q_stmt = select(Question).where(
        Question.company_id == current_user.company_id,
        Question.deleted_at.is_(None)
    ).order_by(Question.leak_risk_score.desc())
    questions = (await db.execute(q_stmt)).scalars().all()

    results = []
    for q in questions:
        # Compute live if never scanned
        risk = q.leak_risk_score if q.leak_last_checked_at else _compute_leak_risk(q)
        results.append(LeakRadarResult(
            question_id=str(q.id),
            title=q.title,
            usage_count=q.usage_count,
            leak_risk_score=risk,
            is_suspected_leaked=q.is_suspected_leaked,
            leak_last_checked_at=q.leak_last_checked_at,
            recommendation=_get_recommendation(risk, q.is_suspected_leaked),
        ))

    high_risk = sum(1 for r in results if r.leak_risk_score >= 75.0)
    return LeakRadarReport(
        total_questions_checked=len(results),
        high_risk_count=high_risk,
        questions=results
    )
