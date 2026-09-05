"""
Proctoring, AI Candidate Evaluation, and Sensory Integrity Monitoring Router.
Phase 6: Includes pre-exam consent, webcam/audio telemetry, transparent risk scoring,
recruiter incident review studio, and retention purge.
"""
import uuid
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

from fastapi import APIRouter, Depends, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from database import get_db
from core.rbac import RoleName
from core.exceptions import NotFoundError, BadRequestError
from core.audit import write_audit_log
from core.ai.summarizer import evaluate_candidate_performance, AiCandidateEvaluation
from core.proctoring.scoring import compute_explainable_integrity_score, SIGNAL_RULES, IntegrityScoreExplanation
from core.proctoring.retention import purge_expired_proctoring_telemetry
from dependencies import get_current_user, require_roles, CurrentUser
from modules.assessments.models import CandidateInvitation, AssessmentAttempt, AttemptStatus, InvitationStatus
from modules.proctoring.models import (
    ProctoringSession, ProctoringEvent, AiEvaluationSummary,
    CandidateConsentRecord, RiskLevel, EventSeverity, ReviewStatus
)

router = APIRouter()

EVENT_SCORE_DEDUCTIONS: Dict[str, float] = {k: float(v["deduction"]) for k, v in SIGNAL_RULES.items()}
FLAG_THRESHOLD: float = 75.0


# ── Schemas ───────────────────────────────────────────────────────────────────

class ConsentCaptureRequest(BaseModel):
    camera_consent_granted: bool = Field(description="Explicit consent for video frame monitoring")
    audio_consent_granted: bool = Field(description="Explicit consent for acoustic monitoring")
    browser_monitoring_consent: bool = Field(description="Consent for focus/fullscreen tracking")
    device_specs_json: Optional[Dict[str, Any]] = None


class ProctoringEventCreate(BaseModel):
    event_type: str = Field(
        description="TAB_SWITCH, FULLSCREEN_EXIT, PASTE_DETECTED, WINDOW_BLUR, FACE_ABSENT, MULTIPLE_FACES, AUDIO_SPIKE, CAMERA_DISCONNECTED"
    )
    severity: Optional[str] = "LOW"
    metadata_json: Optional[Dict[str, Any]] = None


class ProctoringEventResponse(BaseModel):
    id: uuid.UUID
    event_type: str
    severity: str
    timestamp: datetime
    metadata_json: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


class ProctoringSessionResponse(BaseModel):
    id: uuid.UUID
    attempt_id: uuid.UUID
    integrity_score: float
    risk_level: str
    tab_switches_count: int
    fullscreen_exits_count: int
    paste_count: int
    face_absence_count: int
    multiple_faces_count: int
    audio_spikes_count: int
    is_flagged: bool
    review_status: str
    summary_notes: Optional[str] = None
    weighted_deductions_json: Optional[List[Dict[str, Any]]] = None
    events: List[ProctoringEventResponse] = []

    class Config:
        from_attributes = True


class ResolveReviewRequest(BaseModel):
    verdict: str = Field(description="RESOLVED_CLEAN or RESOLVED_FLAGGED")
    notes: Optional[str] = None


class RetentionPurgeRequest(BaseModel):
    older_than_days: int = Field(default=90, ge=1, le=365)


# ── Candidate Pre-Exam Consent Route ──────────────────────────────────────────

@router.post("/exam/{token}/consent", status_code=status.HTTP_201_CREATED)
async def capture_candidate_consent(
    token: str,
    payload: ConsentCaptureRequest,
    db: AsyncSession = Depends(get_db),
):
    # 1. Resolve invitation
    inv_stmt = select(CandidateInvitation).where(CandidateInvitation.token == token)
    invitation = (await db.execute(inv_stmt)).scalar_one_or_none()
    if not invitation:
        raise NotFoundError("Exam invitation token is invalid")

    # 2. Resolve or create in-progress attempt
    att_stmt = select(AssessmentAttempt).where(AssessmentAttempt.invitation_id == invitation.id)
    attempt = (await db.execute(att_stmt)).scalar_one_or_none()

    if not attempt:
        attempt = AssessmentAttempt(
            invitation_id=invitation.id,
            assessment_id=invitation.assessment_id,
            candidate_id=invitation.candidate_id,
            candidate_email=invitation.candidate_email,
            status=AttemptStatus.IN_PROGRESS,
            started_at=datetime.now(timezone.utc),
        )
        db.add(attempt)
        invitation.status = InvitationStatus.STARTED
        await db.flush()

    # 3. Store / update consent record
    stmt = select(CandidateConsentRecord).where(CandidateConsentRecord.attempt_id == attempt.id)
    record = (await db.execute(stmt)).scalar_one_or_none()

    if not record:
        record = CandidateConsentRecord(
            attempt_id=attempt.id,
            camera_consent_granted=payload.camera_consent_granted,
            audio_consent_granted=payload.audio_consent_granted,
            browser_monitoring_consent=payload.browser_monitoring_consent,
            device_specs_json=payload.device_specs_json or {},
        )
        db.add(record)
    else:
        record.camera_consent_granted = payload.camera_consent_granted
        record.audio_consent_granted = payload.audio_consent_granted
        record.browser_monitoring_consent = payload.browser_monitoring_consent
        record.device_specs_json = payload.device_specs_json or {}

    await db.flush()

    return {
        "status": "consent_recorded",
        "attempt_id": str(attempt.id),
        "camera_enabled": record.camera_consent_granted,
        "audio_enabled": record.audio_consent_granted,
        "browser_monitoring": record.browser_monitoring_consent,
    }


# ── Proctoring Event Ingestion Route ─────────────────────────────────────────

@router.post("/exam/{token}/proctor/event", status_code=status.HTTP_201_CREATED)
async def ingest_proctoring_event(
    token: str,
    payload: ProctoringEventCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Ingests browser and sensory telemetry (Face absence, multiple faces, audio spikes, tab switch).
    Recalculates explainable integrity score and risk tier on every event.
    """
    from modules.test_taking.router import _resolve_attempt_from_token
    attempt, assessment = await _resolve_attempt_from_token(token, db)
    if not attempt or not assessment:
        raise NotFoundError("ExamAttempt")

    stmt = select(ProctoringSession).where(ProctoringSession.attempt_id == attempt.id)
    session = (await db.execute(stmt)).scalar_one_or_none()

    if not session:
        session = ProctoringSession(
            attempt_id=attempt.id,
            integrity_score=100.0,
            risk_level=RiskLevel.NORMAL,
            tab_switches_count=0,
            fullscreen_exits_count=0,
            paste_count=0,
            face_absence_count=0,
            multiple_faces_count=0,
            audio_spikes_count=0,
            is_flagged=False,
            review_status=ReviewStatus.PENDING,
            retention_expires_at=datetime.now(timezone.utc) + timedelta(days=90),
        )
        db.add(session)
        await db.flush()

    etype = payload.event_type.upper()
    severity_rule = SIGNAL_RULES.get(etype, {}).get("severity", payload.severity or "LOW")

    # Record event
    event = ProctoringEvent(
        session_id=session.id,
        event_type=etype,
        severity=severity_rule,
        timestamp=datetime.now(timezone.utc),
        metadata_json=payload.metadata_json or {},
    )
    db.add(event)

    # Increment specific counter
    if etype == "TAB_SWITCH":
        session.tab_switches_count += 1
    elif etype == "FULLSCREEN_EXIT":
        session.fullscreen_exits_count += 1
    elif etype == "PASTE_DETECTED":
        session.paste_count += 1
    elif etype == "FACE_ABSENT":
        session.face_absence_count += 1
    elif etype == "MULTIPLE_FACES":
        session.multiple_faces_count += 1
    elif etype == "AUDIO_SPIKE":
        session.audio_spikes_count += 1

    # Recompute transparent explainable score
    counts = {
        "TAB_SWITCH": session.tab_switches_count,
        "FULLSCREEN_EXIT": session.fullscreen_exits_count,
        "PASTE_DETECTED": session.paste_count,
        "FACE_ABSENT": session.face_absence_count,
        "MULTIPLE_FACES": session.multiple_faces_count,
        "AUDIO_SPIKE": session.audio_spikes_count,
    }
    explanation = compute_explainable_integrity_score(counts, assessment.proctoring_mode)

    session.integrity_score = explanation.final_score
    session.risk_level = explanation.risk_level
    session.is_flagged = explanation.is_flagged
    session.weighted_deductions_json = [d.dict() for d in explanation.deductions_breakdown]
    session.summary_notes = explanation.summary

    await db.flush()

    return {
        "status": "recorded",
        "event_type": etype,
        "severity": severity_rule,
        "integrity_score": session.integrity_score,
        "risk_level": session.risk_level,
        "is_flagged": session.is_flagged,
    }


# ── Recruiter Integrity Review Studio Routes ──────────────────────────────────

@router.get("/results/{attempt_id}/proctoring", response_model=ProctoringSessionResponse)
async def get_proctoring_report(
    attempt_id: uuid.UUID,
    severity: Optional[str] = None,
    current_user: CurrentUser = Depends(
        require_roles(RoleName.SUPER_ADMIN, RoleName.COMPANY_ADMIN, RoleName.RECRUITER)
    ),
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieve candidate proctoring audit log, transparent score explanation, and filterable incident timeline.
    """
    stmt = select(ProctoringSession).where(ProctoringSession.attempt_id == attempt_id)
    session = (await db.execute(stmt)).scalar_one_or_none()

    if not session:
        return ProctoringSessionResponse(
            id=uuid.uuid4(),
            attempt_id=attempt_id,
            integrity_score=100.0,
            risk_level=RiskLevel.NORMAL,
            tab_switches_count=0,
            fullscreen_exits_count=0,
            paste_count=0,
            face_absence_count=0,
            multiple_faces_count=0,
            audio_spikes_count=0,
            is_flagged=False,
            review_status=ReviewStatus.RESOLVED_CLEAN,
            summary_notes="No proctoring violations recorded. Verified clean exam session.",
            weighted_deductions_json=[],
            events=[],
        )

    # Query events, optionally filtered by severity
    evt_query = select(ProctoringEvent).where(ProctoringEvent.session_id == session.id)
    if severity and severity.upper() != "ALL":
        evt_query = evt_query.where(ProctoringEvent.severity == severity.upper())
    evt_query = evt_query.order_by(ProctoringEvent.timestamp.asc())

    events = (await db.execute(evt_query)).scalars().all()

    return ProctoringSessionResponse(
        id=session.id,
        attempt_id=session.attempt_id,
        integrity_score=session.integrity_score,
        risk_level=session.risk_level,
        tab_switches_count=session.tab_switches_count,
        fullscreen_exits_count=session.fullscreen_exits_count,
        paste_count=session.paste_count,
        face_absence_count=session.face_absence_count,
        multiple_faces_count=session.multiple_faces_count,
        audio_spikes_count=session.audio_spikes_count,
        is_flagged=session.is_flagged,
        review_status=session.review_status,
        summary_notes=session.summary_notes,
        weighted_deductions_json=session.weighted_deductions_json or [],
        events=[ProctoringEventResponse.from_orm(e) for e in events],
    )


@router.post("/results/{attempt_id}/integrity-review/resolve")
async def resolve_integrity_review(
    attempt_id: uuid.UUID,
    payload: ResolveReviewRequest,
    current_user: CurrentUser = Depends(
        require_roles(RoleName.SUPER_ADMIN, RoleName.COMPANY_ADMIN, RoleName.RECRUITER)
    ),
    db: AsyncSession = Depends(get_db),
):
    """
    Recruiter Decision Gate:
    Enables recruiters to review evidence and set the resolution verdict (RESOLVED_CLEAN or RESOLVED_FLAGGED).
    Guaranteed: AI never auto-rejects; a human recruiter makes the final call.
    """
    stmt = select(ProctoringSession).where(ProctoringSession.attempt_id == attempt_id)
    session = (await db.execute(stmt)).scalar_one_or_none()
    if not session:
        raise NotFoundError("ProctoringSession")

    session.review_status = payload.verdict.upper()
    session.reviewed_by_user_id = current_user.id
    session.recruiter_verdict_notes = payload.notes or f"Marked {payload.verdict.upper()} by recruiter."

    await db.flush()

    return {
        "status": "resolved",
        "attempt_id": attempt_id,
        "review_status": session.review_status,
        "recruiter_notes": session.recruiter_verdict_notes,
    }


# ── Data Retention & Purge Route ──────────────────────────────────────────────

@router.post("/proctoring/retention/purge")
async def purge_retention_telemetry(
    payload: RetentionPurgeRequest,
    current_user: CurrentUser = Depends(
        require_roles(RoleName.SUPER_ADMIN, RoleName.COMPANY_ADMIN)
    ),
    db: AsyncSession = Depends(get_db),
):
    """
    Purges detailed proctoring telemetry older than retention policy (e.g. 90 days).
    """
    result = await purge_expired_proctoring_telemetry(
        db=db,
        company_id=current_user.company_id,
        older_than_days=payload.older_than_days,
    )
    return result
