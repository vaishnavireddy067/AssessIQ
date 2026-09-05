"""
Test Taking & Auto-Grading Engine router.
Public / Token-authenticated endpoints for candidates to take assessments with server-enforced anti-leak protections.
"""
import uuid
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

from fastapi import APIRouter, Depends, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert

from database import get_db
from core.exceptions import NotFoundError, ForbiddenError, BadRequestError
from core.audit import write_audit_log
from modules.assessments.models import (
    Assessment, AssessmentQuestion, Question, QuestionOption, 
    CandidateInvitation, AssessmentAttempt, CandidateAnswer,
    InvitationStatus, AttemptStatus, QuestionType
)

router = APIRouter()


# ── Schemas (Sanitized for Test Takers) ────────────────────────────────────────
class ExamOptionSanitized(BaseModel):
    id: uuid.UUID
    option_text: str
    order_index: int


class ExamQuestionSanitized(BaseModel):
    id: uuid.UUID
    title: str
    content_markdown: str
    question_type: QuestionType
    points: float
    section_name: Optional[str] = "General"
    order_index: int
    options: List[ExamOptionSanitized]


class ExamMetaResponse(BaseModel):
    title: str
    description: Optional[str] = None
    instructions: Optional[str] = None
    duration_minutes: int
    total_questions: int
    candidate_email: str
    candidate_name: Optional[str] = None
    status: str
    already_started: bool
    is_completed: bool
    proctoring_mode: str = "STANDARD"
    company_pattern: str = "CUSTOM"
    drive_start_time: Optional[datetime] = None
    drive_end_time: Optional[datetime] = None
    sections_config: Optional[Dict[str, Any]] = None
    allow_section_switching: bool = True


class ExamSessionResponse(BaseModel):
    attempt_id: uuid.UUID
    title: str
    duration_minutes: int
    started_at: datetime
    ends_at: datetime
    company_pattern: str = "CUSTOM"
    sections_config: Optional[Dict[str, Any]] = None
    allow_section_switching: bool = True
    questions: List[ExamQuestionSanitized]
    saved_answers: Dict[str, List[str]] = {}  # {question_id_str: [selected_option_ids]}


class SaveAnswerRequest(BaseModel):
    question_id: uuid.UUID
    selected_option_ids: List[str]


class ExamSubmissionResponse(BaseModel):
    attempt_id: uuid.UUID
    status: str
    total_score: float
    max_score: float
    percentage: float
    passed: bool
    submitted_at: datetime
    message: str


def _as_utc(dt: Optional[datetime]) -> Optional[datetime]:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


async def _resolve_attempt_from_token(token: str, db: AsyncSession):
    inv_stmt = select(CandidateInvitation).where(CandidateInvitation.token == token)
    invitation = (await db.execute(inv_stmt)).scalar_one_or_none()
    if not invitation:
        return None, None
    att_stmt = select(AssessmentAttempt).where(AssessmentAttempt.invitation_id == invitation.id)
    attempt = (await db.execute(att_stmt)).scalar_one_or_none()
    if not attempt:
        return None, None
    ass_stmt = select(Assessment).where(Assessment.id == attempt.assessment_id)
    assessment = (await db.execute(ass_stmt)).scalar_one_or_none()
    return attempt, assessment


# ── Endpoints ─────────────────────────────────────────────────────────────────
@router.get("/{token}/meta", response_model=ExamMetaResponse)
async def get_exam_metadata(
    token: str,
    db: AsyncSession = Depends(get_db),
):
    """Retrieve exam instructions and rules prior to candidate starting."""
    inv_stmt = select(CandidateInvitation).where(CandidateInvitation.token == token)
    invitation = (await db.execute(inv_stmt)).scalar_one_or_none()
    if not invitation:
        raise NotFoundError("Exam invitation link is invalid")

    if invitation.expires_at:
        exp = _as_utc(invitation.expires_at)
        if exp < datetime.now(timezone.utc):
            raise BadRequestError("This exam invitation link has expired")

    ass_stmt = select(Assessment).where(Assessment.id == invitation.assessment_id)
    assessment = (await db.execute(ass_stmt)).scalar_one_or_none()
    if not assessment:
        raise NotFoundError("Assessment")

    q_count_res = await db.execute(
        select(AssessmentQuestion.id).where(AssessmentQuestion.assessment_id == assessment.id)
    )
    total_q = len(q_count_res.scalars().all())

    # Check if existing attempt
    att_stmt = select(AssessmentAttempt).where(AssessmentAttempt.invitation_id == invitation.id)
    existing_attempt = (await db.execute(att_stmt)).scalar_one_or_none()

    # Drive start & end time validation
    now_utc = datetime.now(timezone.utc)
    if assessment.drive_start_time:
        d_start = _as_utc(assessment.drive_start_time)
        if now_utc < d_start:
            raise BadRequestError(f"Assessment drive has not opened yet. Starts at {d_start.strftime('%Y-%m-%d %H:%M UTC')}")

    if assessment.drive_end_time:
        d_end = _as_utc(assessment.drive_end_time)
        if now_utc > d_end:
            raise BadRequestError(f"Assessment drive validity window closed on {d_end.strftime('%Y-%m-%d %H:%M UTC')}")

    inv_status = invitation.status.value if hasattr(invitation.status, "value") else str(invitation.status)
    att_status = (existing_attempt.status.value if hasattr(existing_attempt.status, "value") else str(existing_attempt.status)) if existing_attempt else None

    return ExamMetaResponse(
        title=assessment.title,
        description=assessment.description,
        instructions=assessment.instructions,
        duration_minutes=assessment.duration_minutes,
        total_questions=total_q,
        candidate_email=invitation.candidate_email,
        candidate_name=invitation.candidate_name,
        status=inv_status,
        already_started=existing_attempt is not None and att_status == "IN_PROGRESS",
        is_completed=inv_status == "COMPLETED" or att_status in ["SUBMITTED", "EVALUATED"],
        proctoring_mode=assessment.proctoring_mode,
        company_pattern=getattr(assessment, "company_pattern", "CUSTOM"),
        drive_start_time=_as_utc(assessment.drive_start_time),
        drive_end_time=_as_utc(assessment.drive_end_time),
        sections_config=assessment.sections_config,
        allow_section_switching=assessment.allow_section_switching,
    )


@router.post("/{token}/start", response_model=ExamSessionResponse)
async def start_exam_session(
    token: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Initialize attempt session and load sanitized questions (with correct answers stripped!)."""
    inv_stmt = select(CandidateInvitation).where(CandidateInvitation.token == token)
    invitation = (await db.execute(inv_stmt)).scalar_one_or_none()
    if not invitation:
        raise NotFoundError("Exam invitation link is invalid")

    inv_status = invitation.status.value if hasattr(invitation.status, "value") else str(invitation.status)
    if inv_status == "COMPLETED":
        raise BadRequestError("This assessment has already been completed and submitted")

    if invitation.expires_at:
        exp = invitation.expires_at
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)
        if exp < datetime.now(timezone.utc):
            raise BadRequestError("This exam invitation link has expired")

    ass_stmt = select(Assessment).where(Assessment.id == invitation.assessment_id)
    assessment = (await db.execute(ass_stmt)).scalar_one_or_none()
    if not assessment:
        raise NotFoundError("Assessment")

    now_utc = datetime.now(timezone.utc)

    # Validate drive validity window
    if assessment.drive_start_time:
        d_start = _as_utc(assessment.drive_start_time)
        if now_utc < d_start:
            raise BadRequestError(f"Assessment drive has not opened yet. Starts at {d_start.strftime('%Y-%m-%d %H:%M UTC')}")

    if assessment.drive_end_time:
        d_end = _as_utc(assessment.drive_end_time)
        if now_utc > d_end:
            raise BadRequestError(f"Assessment drive validity window closed on {d_end.strftime('%Y-%m-%d %H:%M UTC')}")

    # Check for existing in-progress attempt
    att_stmt = select(AssessmentAttempt).where(AssessmentAttempt.invitation_id == invitation.id)
    attempt = (await db.execute(att_stmt)).scalar_one_or_none()

    if not attempt:
        attempt = AssessmentAttempt(
            invitation_id=invitation.id,
            assessment_id=assessment.id,
            candidate_id=invitation.candidate_id,
            candidate_email=invitation.candidate_email,
            status=AttemptStatus.IN_PROGRESS,
            started_at=now_utc,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
        db.add(attempt)
        invitation.status = InvitationStatus.STARTED
        await db.flush()

    # Calculate remaining time (ensure UTC-aware)
    started_utc = _as_utc(attempt.started_at)
    ends_at = started_utc + timedelta(minutes=assessment.duration_minutes)

    # Fetch sanitized questions
    q_stmt = (
        select(AssessmentQuestion, Question)
        .join(Question, AssessmentQuestion.question_id == Question.id)
        .where(AssessmentQuestion.assessment_id == assessment.id, Question.deleted_at.is_(None))
        .order_by(AssessmentQuestion.order_index.asc())
    )
    q_rows = (await db.execute(q_stmt)).all()

    sanitized_questions = []
    for link, q in q_rows:
        opt_stmt = select(QuestionOption).where(QuestionOption.question_id == q.id).order_by(QuestionOption.order_index.asc())
        opts = (await db.execute(opt_stmt)).scalars().all()

        sanitized_opts = [
            ExamOptionSanitized(id=o.id, option_text=o.option_text, order_index=o.order_index)
            for o in opts
        ]

        sanitized_questions.append(
            ExamQuestionSanitized(
                id=q.id,
                title=q.title,
                content_markdown=q.content_markdown,
                question_type=q.question_type,
                points=link.points_override if link.points_override is not None else q.points,
                section_name=link.section_name or "General",
                order_index=link.order_index,
                options=sanitized_opts,
            )
        )

    # Load saved answers if resuming
    ans_stmt = select(CandidateAnswer).where(CandidateAnswer.attempt_id == attempt.id)
    answers = (await db.execute(ans_stmt)).scalars().all()
    saved_answers = {str(a.question_id): a.selected_option_ids for a in answers}

    return ExamSessionResponse(
        attempt_id=attempt.id,
        title=assessment.title,
        duration_minutes=assessment.duration_minutes,
        started_at=started_utc,
        ends_at=ends_at,
        company_pattern=getattr(assessment, "company_pattern", "CUSTOM"),
        sections_config=assessment.sections_config,
        allow_section_switching=assessment.allow_section_switching,
        questions=sanitized_questions,
        saved_answers=saved_answers,
    )


@router.post("/{token}/save-answer")
async def save_draft_answer(
    token: str,
    payload: SaveAnswerRequest,
    db: AsyncSession = Depends(get_db),
):
    """Auto-save candidate response during exam session."""
    inv_stmt = select(CandidateInvitation).where(CandidateInvitation.token == token)
    invitation = (await db.execute(inv_stmt)).scalar_one_or_none()
    if not invitation:
        raise NotFoundError("Invalid token")

    att_stmt = select(AssessmentAttempt).where(AssessmentAttempt.invitation_id == invitation.id)
    attempt = (await db.execute(att_stmt)).scalar_one_or_none()
    if not attempt or attempt.status != AttemptStatus.IN_PROGRESS:
        raise BadRequestError("Exam attempt is not actively in progress")

    ans_stmt = select(CandidateAnswer).where(
        CandidateAnswer.attempt_id == attempt.id,
        CandidateAnswer.question_id == payload.question_id,
    )
    answer = (await db.execute(ans_stmt)).scalar_one_or_none()

    if not answer:
        answer = CandidateAnswer(
            attempt_id=attempt.id,
            question_id=payload.question_id,
            selected_option_ids=payload.selected_option_ids,
            answered_at=datetime.now(timezone.utc),
        )
        db.add(answer)
    else:
        answer.selected_option_ids = payload.selected_option_ids
        answer.answered_at = datetime.now(timezone.utc)

    await db.flush()
    return {"status": "saved", "question_id": str(payload.question_id)}


@router.post("/{token}/submit", response_model=ExamSubmissionResponse)
async def submit_exam(
    token: str,
    db: AsyncSession = Depends(get_db),
):
    """Final exam submission and immediate deterministic auto-grading."""
    inv_stmt = select(CandidateInvitation).where(CandidateInvitation.token == token)
    invitation = (await db.execute(inv_stmt)).scalar_one_or_none()
    if not invitation:
        raise NotFoundError("Invalid token")

    ass_stmt = select(Assessment).where(Assessment.id == invitation.assessment_id)
    assessment = (await db.execute(ass_stmt)).scalar_one_or_none()

    att_stmt = select(AssessmentAttempt).where(AssessmentAttempt.invitation_id == invitation.id)
    attempt = (await db.execute(att_stmt)).scalar_one_or_none()
    if not attempt:
        raise NotFoundError("Exam attempt record not found")

    att_status = attempt.status.value if hasattr(attempt.status, "value") else str(attempt.status)
    if att_status in ["SUBMITTED", "EVALUATED"]:
        return ExamSubmissionResponse(
            attempt_id=attempt.id,
            status=att_status,
            total_score=attempt.total_score,
            max_score=attempt.max_score,
            percentage=attempt.percentage,
            passed=attempt.passed,
            submitted_at=attempt.submitted_at or attempt.updated_at,
            message="Assessment already graded and finalized",
        )

    # Fetch all questions and options for grading
    q_stmt = (
        select(AssessmentQuestion, Question)
        .join(Question, AssessmentQuestion.question_id == Question.id)
        .where(AssessmentQuestion.assessment_id == assessment.id)
    )
    q_rows = (await db.execute(q_stmt)).all()

    # Load all candidate answers
    ans_stmt = select(CandidateAnswer).where(CandidateAnswer.attempt_id == attempt.id)
    answers = (await db.execute(ans_stmt)).scalars().all()
    ans_map = {str(a.question_id): a for a in answers}

    total_score = 0.0
    max_score = 0.0

    # ── Auto-Grading Calculation ──────────────────────────────────────────────
    for link, q in q_rows:
        pts = link.points_override if link.points_override is not None else q.points
        max_score += pts

        # Fetch correct option IDs for this question
        opt_stmt = select(QuestionOption).where(QuestionOption.question_id == q.id)
        options = (await db.execute(opt_stmt)).scalars().all()
        correct_opt_ids = {str(o.id) for o in options if o.is_correct}

        ans_entry = ans_map.get(str(q.id))
        if ans_entry:
            candidate_selected_set = set(ans_entry.selected_option_ids)
            # Exact match check
            is_correct = (candidate_selected_set == correct_opt_ids)
            awarded = pts if is_correct else 0.0

            ans_entry.is_correct = is_correct
            ans_entry.score_awarded = awarded
            total_score += awarded
        else:
            # Candidate did not answer this question
            total_score += 0.0

    percentage = round((total_score / max_score * 100.0), 2) if max_score > 0 else 0.0
    passed = percentage >= assessment.passing_score_percentage
    now_utc = datetime.now(timezone.utc)

    # Phase 9: Generate plain-language AI ranking rationale
    from core.ai.copilot import generate_candidate_ranking_rationale
    ai_rationale = await generate_candidate_ranking_rationale(
        percentage=percentage,
        role_title=assessment.title,
    )

    attempt.status = AttemptStatus.EVALUATED
    attempt.submitted_at = now_utc
    attempt.total_score = total_score
    attempt.max_score = max_score
    attempt.percentage = percentage
    attempt.passed = passed
    attempt.ai_ranking_rationale = ai_rationale

    invitation.status = InvitationStatus.COMPLETED
    await db.flush()

    await write_audit_log(
        db,
        user_id=invitation.candidate_id,
        company_id=assessment.company_id,
        action="assessment.submitted",
        resource_type="attempt",
        resource_id=str(attempt.id),
        metadata={
            "candidate_email": invitation.candidate_email,
            "total_score": total_score,
            "max_score": max_score,
            "percentage": percentage,
            "passed": passed,
        },
    )

    return ExamSubmissionResponse(
        attempt_id=attempt.id,
        status="EVALUATED",
        total_score=total_score,
        max_score=max_score,
        percentage=percentage,
        passed=passed,
        submitted_at=now_utc,
        message="Assessment submitted and evaluated successfully!",
    )
