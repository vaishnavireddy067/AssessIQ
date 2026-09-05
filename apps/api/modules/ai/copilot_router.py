"""
AssessIQ AI Copilot, Proposal Management, and Resume Intelligence Router.
"""
import uuid
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database import get_db
from core.rbac import RoleName
from core.exceptions import NotFoundError, BadRequestError
from core.ai.copilot import generate_copilot_proposal, CopilotAssessmentRequest
from core.ai.resume_parser import parse_resume_text, ResumeParseResult
from core.ai.skill_matrix import calculate_candidate_skill_matrix, CandidateSkillMatrix
from dependencies import get_current_user, require_roles, CurrentUser
from modules.ai.copilot_models import CopilotProposal, ResumeAnalysis, ProposalStatus
from modules.assessments.models import QuestionBank, Question, QuestionOption, QuestionType, DifficultyLevel

router = APIRouter()


# ── Schemas ───────────────────────────────────────────────────────────────────

class ResumeAnalyzeRequest(BaseModel):
    candidate_name: str
    candidate_email: str
    resume_text: str = Field(min_length=10, description="Plain text or parsed resume content")


class ApproveItemRequest(BaseModel):
    item_id: str
    target_bank_id: uuid.UUID


class ApproveProposalRequest(BaseModel):
    target_bank_id: uuid.UUID
    approved_item_ids: List[str] = Field(min_items=1)
    notes: Optional[str] = None


# ── Copilot Routes ────────────────────────────────────────────────────────────

@router.post("/copilot/propose", status_code=status.HTTP_201_CREATED)
async def create_assessment_proposal(
    payload: CopilotAssessmentRequest,
    current_user: CurrentUser = Depends(
        require_roles(RoleName.SUPER_ADMIN, RoleName.COMPANY_ADMIN, RoleName.QUESTION_MANAGER, RoleName.RECRUITER)
    ),
    db: AsyncSession = Depends(get_db),
):
    """
    Generate an assessment proposal in IN_REVIEW state using Assessment Copilot.
    AI-generated content NEVER auto-publishes without human review and approval.
    """
    # Fetch existing question titles for duplicate detection
    stmt = select(Question.title).where(Question.company_id == current_user.company_id)
    existing_titles = [r[0] for r in (await db.execute(stmt)).fetchall()]

    proposal_data = await generate_copilot_proposal(payload, existing_question_titles=existing_titles)

    proposal = CopilotProposal(
        company_id=current_user.company_id,
        created_by_user_id=current_user.id,
        role_title=payload.role_title,
        seniority=payload.seniority,
        target_skills=payload.target_skills,
        duration_minutes=payload.duration_minutes,
        status=ProposalStatus.IN_REVIEW,
        proposed_items=proposal_data["proposed_items"],
    )
    db.add(proposal)
    await db.flush()

    return {
        "proposal_id": proposal.id,
        "role_title": proposal.role_title,
        "seniority": proposal.seniority,
        "target_skills": proposal.target_skills,
        "duration_minutes": proposal.duration_minutes,
        "status": proposal.status,
        "total_items": len(proposal.proposed_items),
        "proposed_items": proposal.proposed_items,
        "approval_gate": "Items remain in IN_REVIEW state until explicitly approved into a Question Bank.",
    }


@router.get("/copilot/proposals", response_model=List[Dict[str, Any]])
async def list_proposals(
    current_user: CurrentUser = Depends(
        require_roles(RoleName.SUPER_ADMIN, RoleName.COMPANY_ADMIN, RoleName.QUESTION_MANAGER, RoleName.RECRUITER)
    ),
    db: AsyncSession = Depends(get_db),
):
    """List all AI assessment proposals pending human review."""
    stmt = (
        select(CopilotProposal)
        .where(CopilotProposal.company_id == current_user.company_id)
        .order_by(CopilotProposal.created_at.desc())
    )
    proposals = (await db.execute(stmt)).scalars().all()
    return [
        {
            "id": p.id,
            "role_title": p.role_title,
            "seniority": p.seniority,
            "target_skills": p.target_skills,
            "status": p.status,
            "total_items": len(p.proposed_items),
            "created_at": p.created_at,
        }
        for p in proposals
    ]


@router.get("/copilot/proposals/{proposal_id}")
async def get_proposal_details(
    proposal_id: uuid.UUID,
    current_user: CurrentUser = Depends(
        require_roles(RoleName.SUPER_ADMIN, RoleName.COMPANY_ADMIN, RoleName.QUESTION_MANAGER, RoleName.RECRUITER)
    ),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve full proposal including editable question drafts."""
    stmt = select(CopilotProposal).where(
        CopilotProposal.id == proposal_id,
        CopilotProposal.company_id == current_user.company_id,
    )
    proposal = (await db.execute(stmt)).scalar_one_or_none()
    if not proposal:
        raise NotFoundError("CopilotProposal")

    return {
        "id": proposal.id,
        "role_title": proposal.role_title,
        "seniority": proposal.seniority,
        "duration_minutes": proposal.duration_minutes,
        "target_skills": proposal.target_skills,
        "status": proposal.status,
        "proposed_items": proposal.proposed_items,
        "review_notes": proposal.review_notes,
    }


@router.post("/copilot/proposals/{proposal_id}/approve", status_code=status.HTTP_200_OK)
async def approve_proposal_items(
    proposal_id: uuid.UUID,
    payload: ApproveProposalRequest,
    current_user: CurrentUser = Depends(
        require_roles(RoleName.SUPER_ADMIN, RoleName.COMPANY_ADMIN, RoleName.QUESTION_MANAGER)
    ),
    db: AsyncSession = Depends(get_db),
):
    """
    Human-in-the-Loop Review Gate:
    Approves vetted AI questions and converts them into published Question Bank questions.
    """
    # Verify proposal exists
    stmt = select(CopilotProposal).where(
        CopilotProposal.id == proposal_id,
        CopilotProposal.company_id == current_user.company_id,
    )
    proposal = (await db.execute(stmt)).scalar_one_or_none()
    if not proposal:
        raise NotFoundError("CopilotProposal")

    # Verify target question bank
    b_stmt = select(QuestionBank).where(
        QuestionBank.id == payload.target_bank_id,
        QuestionBank.company_id == current_user.company_id,
    )
    bank = (await db.execute(b_stmt)).scalar_one_or_none()
    if not bank:
        raise NotFoundError("QuestionBank")

    approved_count = 0
    approved_set = set(payload.approved_item_ids)

    for item in proposal.proposed_items:
        if item.get("item_id") in approved_set:
            item["is_approved"] = True
            item["status"] = "APPROVED"

            # Create real Question in the question bank
            q = Question(
                bank_id=bank.id,
                company_id=current_user.company_id,
                title=item["title"],
                content_markdown=item.get("content_markdown") or item.get("description_markdown", ""),
                question_type=QuestionType.MCQ_SINGLE,
                difficulty=DifficultyLevel.MEDIUM,
                points=float(item.get("points", 2.0)),
                explanation=item.get("explanation"),
                tags=item.get("tags", []),
            )
            db.add(q)
            await db.flush()

            # If it has options, add them
            if "options" in item and item["options"]:
                for idx, opt in enumerate(item["options"]):
                    o = QuestionOption(
                        question_id=q.id,
                        option_text=opt.get("option_text", ""),
                        is_correct=opt.get("is_correct", False),
                        order_index=idx,
                    )
                    db.add(o)

            approved_count += 1

    proposal.status = ProposalStatus.APPROVED
    proposal.review_notes = payload.notes or f"Human approved {approved_count} items."
    await db.flush()

    return {
        "status": "approved",
        "proposal_id": proposal.id,
        "items_approved": approved_count,
        "target_bank_name": bank.name,
    }


# ── Resume Intelligence Routes ────────────────────────────────────────────────

@router.post("/resume/analyze", response_model=ResumeParseResult)
async def analyze_candidate_resume(
    payload: ResumeAnalyzeRequest,
    current_user: CurrentUser = Depends(
        require_roles(RoleName.SUPER_ADMIN, RoleName.COMPANY_ADMIN, RoleName.RECRUITER)
    ),
    db: AsyncSession = Depends(get_db),
):
    """
    Parse a candidate resume, extract key skills, and generate assessment recommendations.
    Advisory Only: Never auto-rejects or auto-assigns candidates.
    """
    from modules.assessments.models import Assessment
    ass_stmt = select(Assessment).where(
        Assessment.company_id == current_user.company_id,
        Assessment.is_deleted == False,
    )
    assessments = (await db.execute(ass_stmt)).scalars().all()
    available_list = [{"id": str(a.id), "title": a.title} for a in assessments]

    # Parse resume text
    result = parse_resume_text(payload.resume_text, available_assessments=available_list)
    result.candidate_name = payload.candidate_name
    result.candidate_email = payload.candidate_email

    # Persist analysis
    analysis = ResumeAnalysis(
        company_id=current_user.company_id,
        candidate_name=payload.candidate_name,
        candidate_email=payload.candidate_email,
        raw_resume_text=payload.resume_text,
        extracted_skills=result.extracted_skills,
        years_experience=result.years_experience,
        education_level=result.education_level,
        domain_tags=result.domain_tags,
        recommended_assessments=result.recommended_assessments,
        advisory_summary=result.advisory_summary,
    )
    db.add(analysis)
    await db.flush()

    return result


# ── Skill Competency Matrix Route ─────────────────────────────────────────────

@router.get("/results/{attempt_id}/skill-matrix", response_model=CandidateSkillMatrix)
async def get_candidate_skill_matrix(
    attempt_id: uuid.UUID,
    current_user: CurrentUser = Depends(
        require_roles(RoleName.SUPER_ADMIN, RoleName.COMPANY_ADMIN, RoleName.RECRUITER)
    ),
    db: AsyncSession = Depends(get_db),
):
    """
    Aggregates evaluated exam questions by skills and computes granular competency metrics.
    """
    from modules.results.router import get_candidate_scorecard
    # Load scorecard data
    scorecard = await get_candidate_scorecard(attempt_id=attempt_id, current_user=current_user, db=db)
    
    evaluated_questions = [
        {
            "tags": q.tags or [q.difficulty],
            "score_awarded": q.score_awarded,
            "points": q.points,
        }
        for q in scorecard.questions
    ]

    return calculate_candidate_skill_matrix(str(attempt_id), evaluated_questions)


# ── Copilot Template Recommendation ──────────────────────────────────────────
class RecommendTemplateRequest(BaseModel):
    role_title: str
    seniority: Optional[str] = "MID"
    job_description: Optional[str] = None
    target_skills: Optional[List[str]] = []


@router.post("/copilot/recommend-template")
async def recommend_assessment_template(
    payload: RecommendTemplateRequest,
    current_user: CurrentUser = Depends(
        require_roles(RoleName.SUPER_ADMIN, RoleName.COMPANY_ADMIN, RoleName.QUESTION_MANAGER, RoleName.RECRUITER)
    ),
):
    """
    AI Copilot evaluates role requirements and suggests the optimal assessment pattern template
    (CODING_ONLY, TECHNICAL_MCQ, APTITUDE_REASONING, VERBAL_APTITUDE, FULL_CAMPUS).
    """
    role_lower = payload.role_title.lower()
    desc_lower = (payload.job_description or "").lower()
    skills_lower = [s.lower() for s in payload.target_skills or []]
    combined_text = f"{role_lower} {desc_lower} {' '.join(skills_lower)}"

    # Heuristic & contextual classifier
    if any(k in combined_text for k in ["campus", "fresher", "graduate", "batch", "university", "trainee engineer", "tcs", "infosys", "wipro"]):
        template_key = "FULL_CAMPUS"
        confidence = 0.95
        rationale = "Campus and fresher hiring drives require multi-section filtering across Numerical, Reasoning, Verbal, and Hands-on Coding to establish batch percentiles."
        suggested_duration = 90
    elif any(k in combined_text for k in ["sde", "software engineer", "backend", "frontend", "algorithm", "dsa", "leetcode", "python developer", "java developer", "full stack"]):
        template_key = "CODING_ONLY"
        confidence = 0.94
        rationale = "Software engineering and developer roles prioritize algorithmic efficiency, clean code implementation, and edge-case execution in live sandbox environments."
        suggested_duration = 60
    elif any(k in combined_text for k in ["analyst", "data analyst", "business analyst", "finance", "quantitative", "operations research"]):
        template_key = "APTITUDE_REASONING"
        confidence = 0.92
        rationale = "Analytical roles focus on numerical accuracy, mathematical modeling, and deductive reasoning without requiring programming sandboxes."
        suggested_duration = 50
    elif any(k in combined_text for k in ["consulting", "marketing", "sales", "support", "content", "communication", "hr", "recruiter", "verbal"]):
        template_key = "VERBAL_APTITUDE"
        confidence = 0.90
        rationale = "Client-facing and communication roles require strong language comprehension, verbal agility, and applied business reasoning."
        suggested_duration = 45
    elif any(k in combined_text for k in ["devops", "systems", "database", "sql", "architect", "network", "qa", "test engineer"]):
        template_key = "TECHNICAL_MCQ"
        confidence = 0.88
        rationale = "Infrastructure, QA, and systems engineering benefit from targeted domain knowledge MCQs covering OS, networking, SQL, and code comprehension."
        suggested_duration = 50
    else:
        template_key = "TECHNICAL_MCQ"
        confidence = 0.80
        rationale = "A blended technical fundamentals assessment provides well-rounded evaluation across computer science domains."
        suggested_duration = 50

    return {
        "recommended_template_key": template_key,
        "confidence": confidence,
        "suggested_duration_minutes": suggested_duration,
        "rationale": rationale,
        "role_title": payload.role_title,
        "seniority": payload.seniority,
    }
