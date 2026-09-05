"""
Candidates router — candidate profile management and recruiter candidate lookup.
"""
import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, EmailStr

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database import get_db
from core.rbac import RoleName
from core.exceptions import NotFoundError, ForbiddenError
from core.audit import write_audit_log
from dependencies import get_current_user, require_roles, CurrentUser
from modules.candidates.models import Candidate
from modules.users.models import User

router = APIRouter()


# ── Schemas ───────────────────────────────────────────────────────────────────
class CandidateProfileResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    full_name: Optional[str] = None
    resume_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CandidateUpdateRequest(BaseModel):
    resume_url: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None


# ── Helper ────────────────────────────────────────────────────────────────────
async def build_candidate_profile(candidate: Candidate, db: AsyncSession) -> CandidateProfileResponse:
    stmt = select(User).where(User.id == candidate.user_id)
    res = await db.execute(stmt)
    user = res.scalar_one_or_none()

    return CandidateProfileResponse(
        id=candidate.id,
        user_id=candidate.user_id,
        email=user.email if user else "",
        first_name=user.first_name if user else None,
        last_name=user.last_name if user else None,
        full_name=user.full_name if user else None,
        resume_url=candidate.resume_url,
        created_at=candidate.created_at,
        updated_at=candidate.updated_at,
    )


# ── Routes ────────────────────────────────────────────────────────────────────
@router.get("/me", response_model=CandidateProfileResponse)
async def get_candidate_me(
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve the candidate profile for the logged in user."""
    stmt = select(Candidate).where(
        Candidate.user_id == current_user.id,
        Candidate.deleted_at.is_(None),
    )
    result = await db.execute(stmt)
    candidate = result.scalar_one_or_none()

    if not candidate:
        # Create candidate profile automatically if missing
        candidate = Candidate(
            user_id=current_user.id,
            resume_url=None,
        )
        db.add(candidate)
        await db.flush()

    return await build_candidate_profile(candidate, db)


@router.put("/me", response_model=CandidateProfileResponse)
async def update_candidate_me(
    payload: CandidateUpdateRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update candidate profile."""
    stmt = select(Candidate).where(
        Candidate.user_id == current_user.id,
        Candidate.deleted_at.is_(None),
    )
    result = await db.execute(stmt)
    candidate = result.scalar_one_or_none()

    if not candidate:
        candidate = Candidate(user_id=current_user.id)
        db.add(candidate)

    if payload.resume_url is not None:
        candidate.resume_url = payload.resume_url

    # Also update user names if provided
    user_stmt = select(User).where(User.id == current_user.id)
    user = (await db.execute(user_stmt)).scalar_one_or_none()
    if user:
        if payload.first_name is not None:
            user.first_name = payload.first_name
        if payload.last_name is not None:
            user.last_name = payload.last_name

    await db.flush()
    await write_audit_log(
        db,
        user_id=current_user.id,
        company_id=None,
        action="candidate.profile_updated",
        resource_type="candidate",
        resource_id=str(candidate.id),
    )
    return await build_candidate_profile(candidate, db)


@router.get("", response_model=List[CandidateProfileResponse])
async def list_candidates(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: CurrentUser = Depends(
        require_roles(RoleName.SUPER_ADMIN, RoleName.COMPANY_ADMIN, RoleName.RECRUITER)
    ),
    db: AsyncSession = Depends(get_db),
):
    """List candidates (Recruiters, Company Admins, and Super Admins)."""
    stmt = (
        select(Candidate)
        .where(Candidate.deleted_at.is_(None))
        .offset(skip)
        .limit(limit)
        .order_by(Candidate.created_at.desc())
    )
    result = await db.execute(stmt)
    candidates = result.scalars().all()

    responses = []
    for c in candidates:
        responses.append(await build_candidate_profile(c, db))
    return responses


@router.get("/{candidate_id}", response_model=CandidateProfileResponse)
async def get_candidate_by_id(
    candidate_id: uuid.UUID,
    current_user: CurrentUser = Depends(
        require_roles(RoleName.SUPER_ADMIN, RoleName.COMPANY_ADMIN, RoleName.RECRUITER)
    ),
    db: AsyncSession = Depends(get_db),
):
    """Fetch candidate profile by ID."""
    stmt = select(Candidate).where(Candidate.id == candidate_id, Candidate.deleted_at.is_(None))
    result = await db.execute(stmt)
    candidate = result.scalar_one_or_none()
    if not candidate:
        raise NotFoundError("Candidate")
    return await build_candidate_profile(candidate, db)
