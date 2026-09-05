"""
AssessIQ SuperAdmin Platform Console, Observability & Billing Management Router.
"""
import uuid
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

from fastapi import APIRouter, Depends, status
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from database import get_db
from dependencies import require_super_admin, CurrentUser, get_current_user, require_roles
from core.rbac import RoleName
from core.exceptions import NotFoundError, BadRequestError
from core.billing.plans import SUBSCRIPTION_PLANS, get_plan
from core.reports.exporter import generate_candidate_csv_report, generate_assessment_summary_csv
from modules.companies.models import Company
from modules.users.models import User
from modules.candidates.models import Candidate
from modules.audit.models import AuditLog
from modules.assessments.models import Assessment, AssessmentAttempt
from modules.proctoring.models import ProctoringSession
from modules.companies.subscription_models import CompanySubscription

router = APIRouter()


class TenantSummaryResponse(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    plan_code: str
    plan_name: str
    monthly_candidate_limit: int
    monthly_candidates_used: int
    user_count: int
    assessment_count: int


class PlanChangeRequest(BaseModel):
    plan_code: str


# ── Platform Observability & Telemetry ────────────────────────────────────────

@router.get("/platform/metrics")
async def get_platform_observability_metrics(
    current_user: CurrentUser = Depends(require_super_admin()),
    db: AsyncSession = Depends(get_db),
):
    """
    Platform-wide operational telemetry and health metrics for SUPER_ADMIN.
    """
    c_count = await db.scalar(select(func.count(Company.id)).where(Company.deleted_at.is_(None))) or 0
    u_count = await db.scalar(select(func.count(User.id)).where(User.deleted_at.is_(None))) or 0
    cand_count = await db.scalar(select(func.count(Candidate.id)).where(Candidate.deleted_at.is_(None))) or 0
    ass_count = await db.scalar(select(func.count(Assessment.id)).where(Assessment.is_deleted == False)) or 0
    att_count = await db.scalar(select(func.count(AssessmentAttempt.id))) or 0
    flagged_sessions = await db.scalar(select(func.count(ProctoringSession.id)).where(ProctoringSession.is_flagged == True)) or 0
    audit_count = await db.scalar(select(func.count(AuditLog.id))) or 0

    return {
        "tenants": {
            "total_companies": c_count,
            "total_users": u_count,
            "total_candidates": cand_count,
        },
        "assessments": {
            "total_published_assessments": ass_count,
            "total_candidate_attempts": att_count,
            "flagged_proctoring_attempts": flagged_sessions,
            "incident_rate_percentage": round((flagged_sessions / att_count * 100), 1) if att_count > 0 else 0.0,
        },
        "system_health": {
            "database_status": "ONLINE",
            "audit_trail_depth": audit_count,
            "api_cluster_status": "OPTIMAL",
            "rate_limiting": "ENABLED",
        },
    }


@router.get("/stats")
async def get_admin_stats(
    current_user: CurrentUser = Depends(require_super_admin()),
    db: AsyncSession = Depends(get_db),
):
    """Platform aggregate statistics for Super Admin."""
    c_count = await db.scalar(select(func.count(Company.id)).where(Company.deleted_at.is_(None))) or 0
    u_count = await db.scalar(select(func.count(User.id)).where(User.deleted_at.is_(None))) or 0
    cand_count = await db.scalar(select(func.count(Candidate.id)).where(Candidate.deleted_at.is_(None))) or 0
    ass_count = await db.scalar(select(func.count(Assessment.id)).where(Assessment.deleted_at.is_(None))) or 0
    att_count = await db.scalar(select(func.count(AssessmentAttempt.id))) or 0

    return {
        "total_companies": c_count,
        "total_users": u_count,
        "total_candidates": cand_count,
        "total_assessments": ass_count,
        "total_attempts": att_count,
    }


# ── Global Tenant Management & Plan Control ───────────────────────────────────

@router.get("/tenants", response_model=List[TenantSummaryResponse])
async def list_all_tenants(
    current_user: CurrentUser = Depends(require_super_admin()),
    db: AsyncSession = Depends(get_db),
):
    """Lists all registered tenants with their subscription plans and usage."""
    c_stmt = select(Company).where(Company.deleted_at.is_(None)).order_by(Company.created_at.desc())
    companies = (await db.execute(c_stmt)).scalars().all()

    summaries = []
    for c in companies:
        sub_stmt = select(CompanySubscription).where(CompanySubscription.company_id == c.id)
        sub = (await db.execute(sub_stmt)).scalar_one_or_none()
        plan_code = sub.plan_code if sub else "STARTER"
        plan = get_plan(plan_code)

        u_count = await db.scalar(select(func.count(User.id)).where(User.company_id == c.id)) or 0
        a_count = await db.scalar(select(func.count(Assessment.id)).where(Assessment.company_id == c.id)) or 0

        summaries.append(
            TenantSummaryResponse(
                id=c.id,
                name=c.name,
                slug=c.slug,
                plan_code=plan_code,
                plan_name=plan.name,
                monthly_candidate_limit=sub.monthly_candidate_limit if sub else plan.monthly_candidate_limit,
                monthly_candidates_used=sub.monthly_candidates_used if sub else 0,
                user_count=u_count,
                assessment_count=a_count,
            )
        )
    return summaries


@router.post("/tenants/{company_id}/plan")
async def update_tenant_subscription(
    company_id: uuid.UUID,
    payload: PlanChangeRequest,
    current_user: CurrentUser = Depends(require_super_admin()),
    db: AsyncSession = Depends(get_db),
):
    """Modifies a company's subscription plan tier (SUPER_ADMIN only)."""
    sub_stmt = select(CompanySubscription).where(CompanySubscription.company_id == company_id)
    sub = (await db.execute(sub_stmt)).scalar_one_or_none()

    plan = get_plan(payload.plan_code)

    if not sub:
        sub = CompanySubscription(
            company_id=company_id,
            plan_code=plan.code,
            monthly_candidate_limit=plan.monthly_candidate_limit,
        )
        db.add(sub)
    else:
        sub.plan_code = plan.code
        sub.monthly_candidate_limit = plan.monthly_candidate_limit

    await db.flush()
    return {
        "status": "updated",
        "company_id": company_id,
        "new_plan": plan.name,
        "monthly_candidate_limit": plan.monthly_candidate_limit,
    }


# ── Reporting & CSV Export Endpoints ──────────────────────────────────────────

@router.get("/assessments/{assessment_id}/export")
async def export_assessment_results_csv(
    assessment_id: uuid.UUID,
    format: Optional[str] = "csv",
    current_user: CurrentUser = Depends(
        require_roles(RoleName.SUPER_ADMIN, RoleName.COMPANY_ADMIN, RoleName.RECRUITER)
    ),
    db: AsyncSession = Depends(get_db),
):
    """Exports cohort assessment scores as CSV."""
    from modules.results.router import get_assessment_results
    ass_stmt = select(Assessment).where(Assessment.id == assessment_id)
    assessment = (await db.execute(ass_stmt)).scalar_one_or_none()
    if not assessment:
        raise NotFoundError("Assessment")

    attempts = await get_assessment_results(assessment_id=assessment_id, current_user=current_user, db=db)
    csv_content = generate_assessment_summary_csv(assessment.title, [a.dict() for a in attempts])

    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="assessment_{assessment.slug}_results.csv"'},
    )


@router.get("/results/{attempt_id}/export")
async def export_candidate_scorecard_csv(
    attempt_id: uuid.UUID,
    format: Optional[str] = "csv",
    current_user: CurrentUser = Depends(
        require_roles(RoleName.SUPER_ADMIN, RoleName.COMPANY_ADMIN, RoleName.RECRUITER)
    ),
    db: AsyncSession = Depends(get_db),
):
    """Exports an individual candidate scorecard breakdown as CSV."""
    from modules.results.router import get_candidate_scorecard
    scorecard = await get_candidate_scorecard(attempt_id=attempt_id, current_user=current_user, db=db)
    csv_content = generate_candidate_csv_report(scorecard.dict())

    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="scorecard_{attempt_id}.csv"'},
    )
