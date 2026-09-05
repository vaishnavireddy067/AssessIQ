"""
Candidate Invitations router — create and manage candidate test invitations.
"""
import uuid
import secrets
from datetime import datetime, timedelta, timezone
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database import get_db
from core.rbac import RoleName
from core.exceptions import NotFoundError, ForbiddenError, BadRequestError
from core.audit import write_audit_log
from dependencies import get_current_user, require_roles, CurrentUser
from modules.assessments.models import Assessment, CandidateInvitation, InvitationStatus, AssessmentStatus
from modules.candidates.models import Candidate
from modules.users.models import User

router = APIRouter()


# ── Schemas ───────────────────────────────────────────────────────────────────
class InviteCandidateRequest(BaseModel):
    candidate_email: EmailStr
    candidate_name: Optional[str] = None
    expires_in_days: int = Field(default=7, ge=1, le=60)


class InvitationResponse(BaseModel):
    id: uuid.UUID
    assessment_id: uuid.UUID
    assessment_title: Optional[str] = None
    candidate_email: str
    candidate_name: Optional[str] = None
    token: str
    test_url: str
    status: InvitationStatus
    expires_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ── Routes ────────────────────────────────────────────────────────────────────
@router.post("/assessments/{assessment_id}/invitations", response_model=InvitationResponse, status_code=status.HTTP_201_CREATED)
async def create_candidate_invitation(
    assessment_id: uuid.UUID,
    payload: InviteCandidateRequest,
    current_user: CurrentUser = Depends(
        require_roles(RoleName.SUPER_ADMIN, RoleName.COMPANY_ADMIN, RoleName.RECRUITER)
    ),
    db: AsyncSession = Depends(get_db),
):
    """Generate a unique secure candidate invitation token for an assessment."""
    stmt = select(Assessment).where(Assessment.id == assessment_id, Assessment.deleted_at.is_(None))
    if not current_user.is_super_admin():
        stmt = stmt.where(Assessment.company_id == current_user.company_id)

    assessment = (await db.execute(stmt)).scalar_one_or_none()
    if not assessment:
        raise NotFoundError("Assessment")

    if assessment.status != AssessmentStatus.PUBLISHED:
        raise BadRequestError("Cannot invite candidates to an assessment that is not yet PUBLISHED")

    # Match candidate account if registered
    cand_stmt = (
        select(Candidate)
        .join(User, Candidate.user_id == User.id)
        .where(User.email == payload.candidate_email.strip().lower())
    )
    cand_match = (await db.execute(cand_stmt)).scalar_one_or_none()
    candidate_id = cand_match.id if cand_match else None

    # Cryptographically secure random hex token
    token = secrets.token_urlsafe(24)
    expires_at = datetime.now(timezone.utc) + timedelta(days=payload.expires_in_days)

    invitation = CandidateInvitation(
        company_id=assessment.company_id,
        assessment_id=assessment.id,
        candidate_id=candidate_id,
        candidate_email=payload.candidate_email.strip().lower(),
        candidate_name=payload.candidate_name,
        token=token,
        status=InvitationStatus.PENDING,
        expires_at=expires_at,
        invited_by=current_user.id,
    )
    db.add(invitation)
    await db.flush()

    await write_audit_log(
        db,
        user_id=current_user.id,
        company_id=assessment.company_id,
        action="candidate.invited",
        resource_type="invitation",
        resource_id=str(invitation.id),
        metadata={"candidate_email": invitation.candidate_email, "assessment_id": str(assessment.id)},
    )

    return InvitationResponse(
        id=invitation.id,
        assessment_id=invitation.assessment_id,
        assessment_title=assessment.title,
        candidate_email=invitation.candidate_email,
        candidate_name=invitation.candidate_name,
        token=invitation.token,
        test_url=f"/exam/{invitation.token}",
        status=invitation.status,
        expires_at=invitation.expires_at,
        created_at=invitation.created_at,
    )


@router.get("/assessments/{assessment_id}/invitations", response_model=List[InvitationResponse])
async def list_assessment_invitations(
    assessment_id: uuid.UUID,
    current_user: CurrentUser = Depends(
        require_roles(RoleName.SUPER_ADMIN, RoleName.COMPANY_ADMIN, RoleName.RECRUITER)
    ),
    db: AsyncSession = Depends(get_db),
):
    """List all candidate invitations generated for this assessment."""
    stmt = select(Assessment).where(Assessment.id == assessment_id, Assessment.deleted_at.is_(None))
    if not current_user.is_super_admin():
        stmt = stmt.where(Assessment.company_id == current_user.company_id)

    assessment = (await db.execute(stmt)).scalar_one_or_none()
    if not assessment:
        raise NotFoundError("Assessment")

    inv_stmt = (
        select(CandidateInvitation)
        .where(CandidateInvitation.assessment_id == assessment_id)
        .order_by(CandidateInvitation.created_at.desc())
    )
    invitations = (await db.execute(inv_stmt)).scalars().all()

    return [
        InvitationResponse(
            id=inv.id,
            assessment_id=inv.assessment_id,
            assessment_title=assessment.title,
            candidate_email=inv.candidate_email,
            candidate_name=inv.candidate_name,
            token=inv.token,
            test_url=f"/exam/{inv.token}",
            status=inv.status,
            expires_at=inv.expires_at,
            created_at=inv.created_at,
        )
        for inv in invitations
    ]


@router.get("/candidates/me/invitations", response_model=List[InvitationResponse])
async def list_my_candidate_invitations(
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all assessments and test invitations assigned to the logged-in candidate."""
    cand_stmt = select(Candidate).where(Candidate.user_id == current_user.id)
    cand = (await db.execute(cand_stmt)).scalar_one_or_none()

    stmt = select(CandidateInvitation, Assessment.title.label("assessment_title")).join(
        Assessment, CandidateInvitation.assessment_id == Assessment.id
    ).where(
        (CandidateInvitation.candidate_email == current_user.email.strip().lower())
        | (CandidateInvitation.candidate_id == (cand.id if cand else None))
    ).order_by(CandidateInvitation.created_at.desc())

    results = (await db.execute(stmt)).all()

    return [
        InvitationResponse(
            id=inv.id,
            assessment_id=inv.assessment_id,
            assessment_title=ass_title,
            candidate_email=inv.candidate_email,
            candidate_name=inv.candidate_name,
            token=inv.token,
            test_url=f"/exam/{inv.token}",
            status=inv.status,
            expires_at=inv.expires_at,
            created_at=inv.created_at,
        )
        for inv, ass_title in results
    ]

