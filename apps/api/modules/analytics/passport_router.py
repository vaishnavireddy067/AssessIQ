"""
Verified Skill Passport API (Phase 9).
Candidate-owned, portable skill profile built from all their assessments.
"""
import uuid
import secrets
import datetime
from typing import List, Optional, Dict
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from database import get_db
from dependencies import get_current_user, CurrentUser
from modules.analytics.models import CandidateSkillPassport, SkillPassportEntry
from modules.assessments.models import AssessmentAttempt, CandidateAnswer, Question, AssessmentQuestion

router = APIRouter()


class SkillEntryResponse(BaseModel):
    skill_name: str
    avg_score: float
    best_score: float
    attempts_count: int
    last_assessed_at: Optional[datetime.datetime] = None


class PassportResponse(BaseModel):
    id: uuid.UUID
    candidate_email: str
    display_name: Optional[str] = None
    total_assessments_taken: int
    avg_overall_score: float
    share_token: str
    is_public: bool
    skills: List[SkillEntryResponse]

    class Config:
        from_attributes = True


async def _build_skill_matrix_from_attempts(
    candidate_email: str, db: AsyncSession
) -> Dict[str, Dict]:
    """
    Scans all completed attempts for a candidate email and derives a skill matrix
    from question tags. Groups scores by tag/skill.
    """
    att_stmt = select(AssessmentAttempt).where(
        AssessmentAttempt.candidate_email == candidate_email,
        AssessmentAttempt.status.in_(["EVALUATED", "SUBMITTED"])
    )
    attempts = (await db.execute(att_stmt)).scalars().all()

    skill_data: Dict[str, List[float]] = {}

    for attempt in attempts:
        ans_stmt = select(CandidateAnswer).where(CandidateAnswer.attempt_id == attempt.id)
        answers = (await db.execute(ans_stmt)).scalars().all()

        for answer in answers:
            q_stmt = select(Question).where(Question.id == answer.question_id)
            q = (await db.execute(q_stmt)).scalar_one_or_none()
            if not q or not q.tags:
                continue

            score_pct = (answer.score_awarded / q.points * 100.0) if q.points > 0 else 0.0
            for tag in q.tags:
                tag_clean = tag.strip().title()
                if tag_clean:
                    skill_data.setdefault(tag_clean, []).append(score_pct)

    # Aggregate
    aggregated = {}
    for skill, scores in skill_data.items():
        aggregated[skill] = {
            "avg_score": round(sum(scores) / len(scores), 1),
            "best_score": round(max(scores), 1),
            "attempts_count": len(scores),
        }
    return aggregated


@router.get("/passport/me", response_model=PassportResponse)
async def get_my_passport(
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Retrieve the calling user's verified skill passport."""
    stmt = select(CandidateSkillPassport).where(
        CandidateSkillPassport.candidate_email == current_user.email
    )
    passport = (await db.execute(stmt)).scalar_one_or_none()

    if not passport:
        # Auto-create on first access
        passport = CandidateSkillPassport(
            candidate_email=current_user.email,
            display_name=current_user.full_name,
            share_token=secrets.token_urlsafe(24),
        )
        db.add(passport)
        await db.flush()

    # Rebuild skill entries from all attempts
    skill_matrix = await _build_skill_matrix_from_attempts(current_user.email, db)

    # Delete old entries and recreate
    for entry in list(passport.entries):
        await db.delete(entry)

    entries = []
    for skill_name, data in skill_matrix.items():
        entry = SkillPassportEntry(
            passport_id=passport.id,
            skill_name=skill_name,
            avg_score=data["avg_score"],
            best_score=data["best_score"],
            attempts_count=data["attempts_count"],
            last_assessed_at=datetime.datetime.now(datetime.timezone.utc),
        )
        db.add(entry)
        entries.append(entry)

    passport.total_assessments_taken = len(
        (await db.execute(
            select(AssessmentAttempt.id).where(
                AssessmentAttempt.candidate_email == current_user.email,
                AssessmentAttempt.status.in_(["EVALUATED", "SUBMITTED"])
            )
        )).scalars().all()
    )

    await db.commit()
    await db.refresh(passport)

    return PassportResponse(
        id=passport.id,
        candidate_email=passport.candidate_email,
        display_name=passport.display_name,
        total_assessments_taken=passport.total_assessments_taken,
        avg_overall_score=passport.avg_overall_score,
        share_token=passport.share_token,
        is_public=passport.is_public,
        skills=[
            SkillEntryResponse(
                skill_name=s.skill_name,
                avg_score=s.avg_score,
                best_score=s.best_score,
                attempts_count=s.attempts_count,
                last_assessed_at=s.last_assessed_at,
            ) for s in entries
        ]
    )


@router.get("/passport/public/{share_token}", response_model=PassportResponse)
async def get_public_passport(share_token: str, db: AsyncSession = Depends(get_db)):
    """View a candidate's public passport via share token (no auth required)."""
    stmt = select(CandidateSkillPassport).where(
        CandidateSkillPassport.share_token == share_token,
        CandidateSkillPassport.is_public == True
    )
    passport = (await db.execute(stmt)).scalar_one_or_none()
    if not passport:
        raise HTTPException(status_code=404, detail="Passport not found or not public")

    # Load entries
    entry_stmt = select(SkillPassportEntry).where(SkillPassportEntry.passport_id == passport.id)
    entries = (await db.execute(entry_stmt)).scalars().all()

    return PassportResponse(
        id=passport.id,
        candidate_email=passport.candidate_email,
        display_name=passport.display_name,
        total_assessments_taken=passport.total_assessments_taken,
        avg_overall_score=passport.avg_overall_score,
        share_token=passport.share_token,
        is_public=passport.is_public,
        skills=[
            SkillEntryResponse(
                skill_name=e.skill_name,
                avg_score=e.avg_score,
                best_score=e.best_score,
                attempts_count=e.attempts_count,
                last_assessed_at=e.last_assessed_at,
            ) for e in entries
        ]
    )


@router.patch("/passport/me/visibility")
async def toggle_passport_visibility(
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Toggle whether the passport is publicly shareable."""
    stmt = select(CandidateSkillPassport).where(
        CandidateSkillPassport.candidate_email == current_user.email
    )
    passport = (await db.execute(stmt)).scalar_one_or_none()
    if not passport:
        raise HTTPException(status_code=404, detail="Passport not found. Access /passport/me first.")
    passport.is_public = not passport.is_public
    await db.commit()
    return {"is_public": passport.is_public, "share_token": passport.share_token if passport.is_public else None}
