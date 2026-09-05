"""
AssessIQ Public REST API Router (Phase 8).
Exposes ATS integration endpoints authenticated via programmatic API Keys.
"""
import uuid
from typing import Dict, Any, List
from pydantic import BaseModel, EmailStr

from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database import get_db
from core.api_keys import get_company_id_from_api_key
from modules.assessments.models import Assessment
from modules.candidates.models import Candidate
from modules.assessments.models import AssessmentAttempt

router = APIRouter()


class AtsInviteRequest(BaseModel):
    candidate_email: EmailStr
    candidate_name: str
    job_role: str = ""
    ats_candidate_id: str = ""


class AtsInviteResponse(BaseModel):
    attempt_id: str
    magic_link: str
    status: str


class PublicCandidateResultResponse(BaseModel):
    attempt_id: str
    candidate_email: str
    status: str
    total_score: int
    percentage: float
    integrity_score: float
    is_flagged: bool


@router.post("/assessments/{assessment_id}/invite", response_model=AtsInviteResponse)
async def invite_candidate_via_api(
    assessment_id: uuid.UUID,
    payload: AtsInviteRequest,
    background_tasks: BackgroundTasks,
    company_id: str = Depends(get_company_id_from_api_key),
    db: AsyncSession = Depends(get_db)
):
    """
    Public API: Invites a candidate to an assessment from an external ATS platform.
    Returns the magic exam link.
    """
    # 1. Verify Assessment belongs to company
    stmt = select(Assessment).where(
        Assessment.id == assessment_id, 
        Assessment.company_id == uuid.UUID(company_id)
    )
    assessment = (await db.execute(stmt)).scalar_one_or_none()
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found or not owned by your company.")

    # 2. Find or create candidate
    c_stmt = select(Candidate).where(
        Candidate.email == payload.candidate_email,
        Candidate.company_id == uuid.UUID(company_id)
    )
    candidate = (await db.execute(c_stmt)).scalar_one_or_none()
    if not candidate:
        candidate = Candidate(
            company_id=uuid.UUID(company_id),
            email=payload.candidate_email,
            full_name=payload.candidate_name,
            ats_candidate_id=payload.ats_candidate_id
        )
        db.add(candidate)
        await db.flush()

    # 3. Create Attempt
    attempt = AssessmentAttempt(
        assessment_id=assessment.id,
        candidate_id=candidate.id,
        status="INVITED",
        magic_token=str(uuid.uuid4())
    )
    db.add(attempt)
    await db.commit()

    # 4. Trigger Webhook Event for external integrations
    from core.webhooks.dispatcher import dispatch_webhook_event, WebhookEvent
    
    # In a real app we would use background tasks
    # background_tasks.add_task(dispatch_webhook_event, ...)

    exam_url = f"https://assessiq.example.com/exam/{attempt.magic_token}"
    return AtsInviteResponse(
        attempt_id=str(attempt.id),
        magic_link=exam_url,
        status="INVITED"
    )


@router.get("/results/{attempt_id}", response_model=PublicCandidateResultResponse)
async def get_candidate_results_via_api(
    attempt_id: uuid.UUID,
    company_id: str = Depends(get_company_id_from_api_key),
    db: AsyncSession = Depends(get_db)
):
    """
    Public API: Retrieves a completed candidate's score and integrity status.
    """
    stmt = select(AssessmentAttempt).where(AssessmentAttempt.id == attempt_id)
    attempt = (await db.execute(stmt)).scalar_one_or_none()
    if not attempt:
        raise HTTPException(status_code=404, detail="Attempt not found.")

    # Validate company ownership via candidate
    c_stmt = select(Candidate).where(Candidate.id == attempt.candidate_id)
    candidate = (await db.execute(c_stmt)).scalar_one_or_none()
    if not candidate or str(candidate.company_id) != company_id:
        raise HTTPException(status_code=404, detail="Attempt not found.")

    # Gather proctoring data if available
    from modules.proctoring.models import ProctoringSession
    p_stmt = select(ProctoringSession).where(ProctoringSession.attempt_id == attempt_id)
    p_session = (await db.execute(p_stmt)).scalar_one_or_none()

    integrity_score = 100.0
    is_flagged = False
    if p_session:
        integrity_score = float(p_session.trust_score)
        is_flagged = p_session.is_flagged

    return PublicCandidateResultResponse(
        attempt_id=str(attempt.id),
        candidate_email=candidate.email,
        status=attempt.status,
        total_score=attempt.total_score,
        percentage=attempt.percentage,
        integrity_score=integrity_score,
        is_flagged=is_flagged
    )
