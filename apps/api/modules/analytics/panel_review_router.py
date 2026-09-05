"""
Panel Review Workflow API (Phase 9).
Structured multi-recruiter review for borderline candidates (60-75% score).
"""
import uuid
import datetime
from typing import List, Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database import get_db
from dependencies import require_roles, get_current_user, CurrentUser
from core.rbac import RoleName
from core.exceptions import NotFoundError, ForbiddenError
from modules.analytics.models import PanelReviewRequest, PanelReviewVote
from modules.assessments.models import AssessmentAttempt, Assessment

router = APIRouter()

# Borderline score range that triggers panel review
BORDERLINE_MIN = 55.0
BORDERLINE_MAX = 75.0


class VoteRequest(BaseModel):
    verdict: str  # HIRE, REJECT, NEEDS_MORE_INFO
    notes: Optional[str] = None


class PanelVoteResponse(BaseModel):
    id: uuid.UUID
    recruiter_id: uuid.UUID
    verdict: str
    notes: Optional[str] = None
    created_at: datetime.datetime

    class Config:
        from_attributes = True


class PanelReviewResponse(BaseModel):
    id: uuid.UUID
    attempt_id: uuid.UUID
    status: str
    required_votes: int
    votes_cast: int
    final_verdict: Optional[str] = None
    votes: List[PanelVoteResponse]

    class Config:
        from_attributes = True


async def _auto_create_panel_review(attempt: AssessmentAttempt, db: AsyncSession):
    """Auto-triggers a panel review if the attempt score is in the borderline range."""
    if BORDERLINE_MIN <= attempt.percentage <= BORDERLINE_MAX:
        existing = (await db.execute(
            select(PanelReviewRequest).where(PanelReviewRequest.attempt_id == attempt.id)
        )).scalar_one_or_none()
        if not existing:
            ass = (await db.execute(
                select(Assessment).where(Assessment.id == attempt.assessment_id)
            )).scalar_one_or_none()
            if ass:
                review = PanelReviewRequest(
                    attempt_id=attempt.id,
                    company_id=ass.company_id,
                )
                db.add(review)
                await db.flush()


@router.get("/panel-reviews", response_model=List[PanelReviewResponse])
async def list_panel_reviews(
    current_user: CurrentUser = Depends(
        require_roles(RoleName.SUPER_ADMIN, RoleName.COMPANY_ADMIN, RoleName.RECRUITER)
    ),
    db: AsyncSession = Depends(get_db)
):
    """List all pending panel reviews for the company."""
    stmt = select(PanelReviewRequest).where(
        PanelReviewRequest.company_id == current_user.company_id
    ).order_by(PanelReviewRequest.created_at.desc())
    reviews = (await db.execute(stmt)).scalars().all()

    result = []
    for review in reviews:
        vote_stmt = select(PanelReviewVote).where(PanelReviewVote.review_request_id == review.id)
        votes = (await db.execute(vote_stmt)).scalars().all()

        hire_votes = sum(1 for v in votes if v.verdict == "HIRE")
        reject_votes = sum(1 for v in votes if v.verdict == "REJECT")
        final = None
        if len(votes) >= review.required_votes:
            final = "HIRE" if hire_votes > reject_votes else "REJECT"

        result.append(PanelReviewResponse(
            id=review.id,
            attempt_id=review.attempt_id,
            status=review.status,
            required_votes=review.required_votes,
            votes_cast=len(votes),
            final_verdict=final,
            votes=[PanelVoteResponse(
                id=v.id,
                recruiter_id=v.recruiter_id,
                verdict=v.verdict,
                notes=v.notes,
                created_at=v.created_at,
            ) for v in votes],
        ))
    return result


@router.post("/panel-reviews/{review_id}/vote", response_model=PanelReviewResponse)
async def cast_panel_vote(
    review_id: uuid.UUID,
    payload: VoteRequest,
    current_user: CurrentUser = Depends(
        require_roles(RoleName.SUPER_ADMIN, RoleName.COMPANY_ADMIN, RoleName.RECRUITER)
    ),
    db: AsyncSession = Depends(get_db)
):
    """Cast a vote on a panel review. Each recruiter can vote once."""
    if payload.verdict not in ["HIRE", "REJECT", "NEEDS_MORE_INFO"]:
        raise HTTPException(status_code=400, detail="verdict must be HIRE, REJECT, or NEEDS_MORE_INFO")

    review = (await db.execute(
        select(PanelReviewRequest).where(PanelReviewRequest.id == review_id)
    )).scalar_one_or_none()
    if not review:
        raise NotFoundError("Panel Review")
    if review.company_id != current_user.company_id:
        raise ForbiddenError("Not your review")

    # Check for duplicate vote
    dup_stmt = select(PanelReviewVote).where(
        PanelReviewVote.review_request_id == review_id,
        PanelReviewVote.recruiter_id == current_user.id
    )
    if (await db.execute(dup_stmt)).scalar_one_or_none():
        raise HTTPException(status_code=409, detail="You have already voted on this review.")

    vote = PanelReviewVote(
        review_request_id=review_id,
        recruiter_id=current_user.id,
        verdict=payload.verdict,
        notes=payload.notes,
    )
    db.add(vote)
    await db.flush()

    # Load all votes to compute current status
    all_votes = (await db.execute(
        select(PanelReviewVote).where(PanelReviewVote.review_request_id == review_id)
    )).scalars().all()

    hire_votes = sum(1 for v in all_votes if v.verdict == "HIRE")
    reject_votes = sum(1 for v in all_votes if v.verdict == "REJECT")

    if len(all_votes) >= review.required_votes:
        review.status = "APPROVED" if hire_votes > reject_votes else "REJECTED"

    await db.commit()

    final = None
    if len(all_votes) >= review.required_votes:
        final = "HIRE" if hire_votes > reject_votes else "REJECT"

    return PanelReviewResponse(
        id=review.id,
        attempt_id=review.attempt_id,
        status=review.status,
        required_votes=review.required_votes,
        votes_cast=len(all_votes),
        final_verdict=final,
        votes=[PanelVoteResponse(
            id=v.id,
            recruiter_id=v.recruiter_id,
            verdict=v.verdict,
            notes=v.notes,
            created_at=v.created_at,
        ) for v in all_votes],
    )
