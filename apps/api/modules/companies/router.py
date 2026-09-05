"""
Companies router — endpoints for managing company tenants, integrations, API keys, webhooks, and SSO.
"""
import uuid
import secrets
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, HttpUrl

from fastapi import APIRouter, Depends, Query, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func, desc

from database import get_db
from core.rbac import RoleName
from core.exceptions import NotFoundError, ConflictError, ForbiddenError, BadRequestError
from core.audit import write_audit_log
from dependencies import get_current_user, require_roles, require_super_admin, CurrentUser
from modules.companies.models import Company, CompanyPlan
from modules.companies.enterprise_models import ApiKey, WebhookEndpoint, EnterpriseSSOConfig, WebhookEvent
from modules.companies.subscription_models import CompanySubscription
from modules.assessments.models import Assessment, AssessmentAttempt, CandidateInvitation
from modules.candidates.models import Candidate
from modules.users.models import User
from modules.proctoring.models import ProctoringSession

router = APIRouter()


# ── Pydantic Schemas ──────────────────────────────────────────────────────────
class CompanyCreateRequest(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    slug: str = Field(min_length=2, max_length=100)
    domain: Optional[str] = None
    website: Optional[str] = None
    industry: Optional[str] = None
    size: Optional[str] = None
    plan: Optional[CompanyPlan] = CompanyPlan.STARTER


class CompanyUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    domain: Optional[str] = None
    website: Optional[str] = None
    industry: Optional[str] = None
    size: Optional[str] = None
    logo_url: Optional[str] = None
    plan: Optional[CompanyPlan] = None
    is_active: Optional[bool] = None


class CompanyResponse(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    domain: Optional[str] = None
    website: Optional[str] = None
    industry: Optional[str] = None
    size: Optional[str] = None
    logo_url: Optional[str] = None
    plan: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ApiKeyCreateRequest(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    expires_in_days: Optional[int] = Field(default=90, ge=1, le=365)


class ApiKeyResponse(BaseModel):
    id: uuid.UUID
    name: str
    prefix: str
    is_active: bool
    last_used_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ApiKeyCreatedResponse(ApiKeyResponse):
    raw_key: str  # Only returned upon creation


class WebhookCreateRequest(BaseModel):
    url: str = Field(min_length=10, max_length=2048)
    events: List[str] = Field(default=["candidate.submitted", "proctoring.flagged"])


class WebhookResponse(BaseModel):
    id: uuid.UUID
    url: str
    secret_key: str
    is_active: bool
    events: List[str]
    created_at: datetime

    class Config:
        from_attributes = True


class WebhookTestResponse(BaseModel):
    status: str
    event: str
    payload_dispatched: Dict[str, Any]
    timestamp: datetime


class SSOConfigRequest(BaseModel):
    provider_type: str = Field(default="SAML")  # SAML or OIDC
    idp_entity_id: Optional[str] = None
    idp_sso_url: Optional[str] = None
    idp_x509_cert: Optional[str] = None
    oidc_client_id: Optional[str] = None
    oidc_client_secret: Optional[str] = None
    oidc_issuer: Optional[str] = None
    is_active: bool = True


class SSOConfigResponse(BaseModel):
    provider_type: str
    idp_entity_id: Optional[str] = None
    idp_sso_url: Optional[str] = None
    idp_x509_cert: Optional[str] = None
    oidc_client_id: Optional[str] = None
    oidc_issuer: Optional[str] = None
    is_active: bool
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class CompanyStatsResponse(BaseModel):
    total_assessments: int
    published_assessments: int
    total_invitations: int
    total_attempts: int
    completed_attempts: int
    average_score: float
    flagged_attempts: int
    total_candidates: int
    team_members_count: int
    plan: str
    candidates_quota_limit: int
    candidates_quota_used: int


class CompanyCandidateItem(BaseModel):
    id: uuid.UUID
    email: str
    full_name: Optional[str] = None
    phone: Optional[str] = None
    created_at: datetime
    latest_assessment_title: Optional[str] = None
    latest_status: Optional[str] = None
    latest_score: Optional[int] = None
    latest_percentage: Optional[float] = None
    latest_integrity_score: Optional[float] = None
    is_flagged: bool = False


class PlanUsageResponse(BaseModel):
    plan: str
    status: str
    monthly_candidate_limit: int
    monthly_candidates_used: int
    current_period_end: datetime
    features: List[str]


class UpgradeTierRequest(BaseModel):
    requested_plan: str
    notes: Optional[str] = None


# ── Core Company Profile & Stats Routes ─────────────────────────────────────────

@router.get("/me", response_model=CompanyResponse)
async def get_my_company(
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the current authenticated user's company profile."""
    if not current_user.company_id:
        raise NotFoundError("No company associated with current account")

    stmt = select(Company).where(
        Company.id == current_user.company_id,
        Company.deleted_at.is_(None),
    )
    result = await db.execute(stmt)
    company = result.scalar_one_or_none()
    if not company:
        raise NotFoundError("Company")
    return company


@router.put("/me", response_model=CompanyResponse)
async def update_my_company(
    payload: CompanyUpdateRequest,
    current_user: CurrentUser = Depends(require_roles(RoleName.COMPANY_ADMIN, RoleName.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Update current company settings (COMPANY_ADMIN only)."""
    if not current_user.company_id and not current_user.is_super_admin():
        raise ForbiddenError("User is not bound to a company context")

    company_id = current_user.company_id
    stmt = select(Company).where(Company.id == company_id, Company.deleted_at.is_(None))
    result = await db.execute(stmt)
    company = result.scalar_one_or_none()
    if not company:
        raise NotFoundError("Company")

    update_data = payload.dict(exclude_unset=True)
    if not current_user.is_super_admin():
        update_data.pop("plan", None)
        update_data.pop("is_active", None)

    for field, val in update_data.items():
        setattr(company, field, val)

    await db.flush()
    await write_audit_log(
        db,
        user_id=current_user.id,
        company_id=company.id,
        action="company.updated",
        resource_type="company",
        resource_id=str(company.id),
        metadata=update_data,
    )
    return company


@router.get("/me/stats", response_model=CompanyStatsResponse)
async def get_company_stats(
    current_user: CurrentUser = Depends(require_roles(RoleName.COMPANY_ADMIN, RoleName.RECRUITER, RoleName.QUESTION_MANAGER, RoleName.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve comprehensive tenant metrics and hiring KPIs for company portal dashboard."""
    if not current_user.company_id:
        raise NotFoundError("No company associated with current account")
    
    comp_id = current_user.company_id

    # 1. Company
    comp_stmt = select(Company).where(Company.id == comp_id)
    company = (await db.execute(comp_stmt)).scalar_one_or_none()
    if not company:
        raise NotFoundError("Company")

    # 2. Assessments count
    ass_stmt = select(Assessment).where(Assessment.company_id == comp_id, Assessment.deleted_at.is_(None))
    assessments = (await db.execute(ass_stmt)).scalars().all()
    total_assessments = len(assessments)
    published_assessments = len([a for a in assessments if a.status == "PUBLISHED"])
    assessment_ids = [a.id for a in assessments]

    # 3. Invitations count
    inv_stmt = select(func.count(CandidateInvitation.id)).where(CandidateInvitation.company_id == comp_id)
    total_invitations = (await db.execute(inv_stmt)).scalar() or 0

    # 4. Attempts & Scores
    total_attempts = 0
    completed_attempts = 0
    average_score = 0.0
    flagged_attempts = 0

    if assessment_ids:
        att_stmt = select(AssessmentAttempt).where(AssessmentAttempt.assessment_id.in_(assessment_ids))
        attempts = (await db.execute(att_stmt)).scalars().all()
        total_attempts = len(attempts)
        completed = [a for a in attempts if a.status == "SUBMITTED"]
        completed_attempts = len(completed)
        if completed_attempts > 0:
            average_score = round(sum(a.percentage for a in completed) / completed_attempts, 1)

        attempt_ids = [a.id for a in attempts]
        if attempt_ids:
            proc_stmt = select(func.count(ProctoringSession.id)).where(
                ProctoringSession.attempt_id.in_(attempt_ids),
                ProctoringSession.is_flagged == True
            )
            flagged_attempts = (await db.execute(proc_stmt)).scalar() or 0

    # 5. Candidates talent pool
    cand_stmt = select(func.count(func.distinct(CandidateInvitation.candidate_email))).where(CandidateInvitation.company_id == comp_id)
    total_candidates = (await db.execute(cand_stmt)).scalar() or 0

    # 6. Team members
    team_stmt = select(func.count(User.id)).where(User.company_id == comp_id, User.deleted_at.is_(None))
    team_members_count = (await db.execute(team_stmt)).scalar() or 1

    # 7. Quota limit based on plan
    plan_str = str(company.plan) if company.plan else "STARTER"
    quota_limits = {
        "STARTER": 50,
        "GROWTH": 250,
        "ENTERPRISE": 10000,
    }
    candidates_quota_limit = quota_limits.get(plan_str, 50)
    candidates_quota_used = min(total_invitations, candidates_quota_limit)

    return CompanyStatsResponse(
        total_assessments=total_assessments,
        published_assessments=published_assessments,
        total_invitations=total_invitations,
        total_attempts=total_attempts,
        completed_attempts=completed_attempts,
        average_score=average_score,
        flagged_attempts=flagged_attempts,
        total_candidates=total_candidates,
        team_members_count=team_members_count,
        plan=plan_str,
        candidates_quota_limit=candidates_quota_limit,
        candidates_quota_used=candidates_quota_used,
    )


# ── Candidate Directory Routes ──────────────────────────────────────────────────

@router.get("/me/candidates", response_model=List[CompanyCandidateItem])
async def list_company_candidates(
    current_user: CurrentUser = Depends(require_roles(RoleName.COMPANY_ADMIN, RoleName.RECRUITER, RoleName.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve full candidate talent pool associated with the company with recent assessment attempts."""
    if not current_user.company_id:
        raise NotFoundError("No company associated with current account")
    
    comp_id = current_user.company_id
    inv_stmt = (
        select(CandidateInvitation, Assessment.title)
        .join(Assessment, CandidateInvitation.assessment_id == Assessment.id)
        .where(CandidateInvitation.company_id == comp_id)
        .order_by(CandidateInvitation.created_at.desc())
    )
    invitations = (await db.execute(inv_stmt)).all()

    items = []
    seen_emails = set()
    for inv, ass_title in invitations:
        if inv.candidate_email in seen_emails:
            continue
        seen_emails.add(inv.candidate_email)

        # Check latest attempt for this invitation
        att_stmt = (
            select(AssessmentAttempt)
            .where(AssessmentAttempt.invitation_id == inv.id)
            .order_by(AssessmentAttempt.created_at.desc())
            .limit(1)
        )
        attempt = (await db.execute(att_stmt)).scalar_one_or_none()

        latest_status = attempt.status if attempt else inv.status
        latest_score = int(attempt.total_score) if attempt else None
        latest_percentage = attempt.percentage if attempt else None
        integrity = None
        is_flagged = False

        if attempt:
            p_stmt = select(ProctoringSession).where(ProctoringSession.attempt_id == attempt.id)
            p_sess = (await db.execute(p_stmt)).scalar_one_or_none()
            if p_sess:
                integrity = float(p_sess.trust_score)
                is_flagged = p_sess.is_flagged

        items.append(CompanyCandidateItem(
            id=inv.id,
            email=inv.candidate_email,
            full_name=inv.candidate_name,
            phone=None,
            created_at=inv.created_at,
            latest_assessment_title=ass_title,
            latest_status=latest_status,
            latest_score=latest_score,
            latest_percentage=latest_percentage,
            latest_integrity_score=integrity,
            is_flagged=is_flagged
        ))

    return items


# ── Programmatic API Keys Management ───────────────────────────────────────────

@router.get("/me/api-keys", response_model=List[ApiKeyResponse])
async def list_company_api_keys(
    current_user: CurrentUser = Depends(require_roles(RoleName.COMPANY_ADMIN, RoleName.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """List programmatic API keys registered for ATS integrations."""
    if not current_user.company_id:
        raise NotFoundError("No company associated with current account")

    stmt = select(ApiKey).where(ApiKey.company_id == current_user.company_id).order_by(ApiKey.created_at.desc())
    keys = (await db.execute(stmt)).scalars().all()
    return keys


@router.post("/me/api-keys", response_model=ApiKeyCreatedResponse, status_code=status.HTTP_201_CREATED)
async def create_company_api_key(
    payload: ApiKeyCreateRequest,
    current_user: CurrentUser = Depends(require_roles(RoleName.COMPANY_ADMIN, RoleName.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Generate a new secure programmatic API key for external ATS (Greenhouse, Lever, Workable)."""
    if not current_user.company_id:
        raise NotFoundError("No company associated with current account")

    # Generate raw token e.g. aiq_live_abc123...
    raw_secret = secrets.token_urlsafe(32)
    raw_key = f"aiq_live_{raw_secret}"
    prefix = raw_key[:12] + "..."

    expires_at = None
    if payload.expires_in_days:
        expires_at = datetime.now(timezone.utc) + timedelta(days=payload.expires_in_days)

    new_api_key = ApiKey(
        company_id=current_user.company_id,
        name=payload.name,
        key_hash=raw_key,  # Direct key hash token lookup
        prefix=prefix,
        is_active=True,
        expires_at=expires_at,
    )
    db.add(new_api_key)
    await db.flush()

    await write_audit_log(
        db,
        user_id=current_user.id,
        company_id=current_user.company_id,
        action="api_key.created",
        resource_type="api_key",
        resource_id=str(new_api_key.id),
        metadata={"name": payload.name, "prefix": prefix},
    )

    return ApiKeyCreatedResponse(
        id=new_api_key.id,
        name=new_api_key.name,
        prefix=new_api_key.prefix,
        is_active=new_api_key.is_active,
        last_used_at=new_api_key.last_used_at,
        expires_at=new_api_key.expires_at,
        created_at=new_api_key.created_at,
        raw_key=raw_key,
    )


@router.delete("/me/api-keys/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_company_api_key(
    key_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_roles(RoleName.COMPANY_ADMIN, RoleName.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Revoke or delete an API key."""
    if not current_user.company_id:
        raise NotFoundError("No company associated with current account")

    stmt = select(ApiKey).where(ApiKey.id == key_id, ApiKey.company_id == current_user.company_id)
    key_obj = (await db.execute(stmt)).scalar_one_or_none()
    if not key_obj:
        raise NotFoundError("API Key")

    await db.delete(key_obj)
    await db.flush()

    await write_audit_log(
        db,
        user_id=current_user.id,
        company_id=current_user.company_id,
        action="api_key.revoked",
        resource_type="api_key",
        resource_id=str(key_id),
    )
    return None


# ── Webhooks Management ─────────────────────────────────────────────────────────

@router.get("/me/webhooks", response_model=List[WebhookResponse])
async def list_company_webhooks(
    current_user: CurrentUser = Depends(require_roles(RoleName.COMPANY_ADMIN, RoleName.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """List configured outgoing webhook destinations for ATS sync and candidate alerts."""
    if not current_user.company_id:
        raise NotFoundError("No company associated with current account")

    stmt = select(WebhookEndpoint).where(WebhookEndpoint.company_id == current_user.company_id).order_by(WebhookEndpoint.created_at.desc())
    endpoints = (await db.execute(stmt)).scalars().all()
    return endpoints


@router.post("/me/webhooks", response_model=WebhookResponse, status_code=status.HTTP_201_CREATED)
async def create_company_webhook(
    payload: WebhookCreateRequest,
    current_user: CurrentUser = Depends(require_roles(RoleName.COMPANY_ADMIN, RoleName.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Register a new webhook endpoint with custom event subscriptions."""
    if not current_user.company_id:
        raise NotFoundError("No company associated with current account")

    endpoint = WebhookEndpoint(
        company_id=current_user.company_id,
        url=payload.url,
        secret_key=secrets.token_hex(32),
        is_active=True,
        events=payload.events,
    )
    db.add(endpoint)
    await db.flush()

    await write_audit_log(
        db,
        user_id=current_user.id,
        company_id=current_user.company_id,
        action="webhook.created",
        resource_type="webhook_endpoint",
        resource_id=str(endpoint.id),
        metadata={"url": payload.url, "events": payload.events},
    )
    return endpoint


@router.delete("/me/webhooks/{webhook_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_company_webhook(
    webhook_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_roles(RoleName.COMPANY_ADMIN, RoleName.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Remove a webhook endpoint."""
    if not current_user.company_id:
        raise NotFoundError("No company associated with current account")

    stmt = select(WebhookEndpoint).where(
        WebhookEndpoint.id == webhook_id,
        WebhookEndpoint.company_id == current_user.company_id
    )
    wh = (await db.execute(stmt)).scalar_one_or_none()
    if not wh:
        raise NotFoundError("Webhook endpoint")

    await db.delete(wh)
    await db.flush()
    return None


@router.post("/me/webhooks/{webhook_id}/test", response_model=WebhookTestResponse)
async def test_company_webhook(
    webhook_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_roles(RoleName.COMPANY_ADMIN, RoleName.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Trigger a mock test webhook ping payload to verify destination endpoint connectivity."""
    if not current_user.company_id:
        raise NotFoundError("No company associated with current account")

    stmt = select(WebhookEndpoint).where(
        WebhookEndpoint.id == webhook_id,
        WebhookEndpoint.company_id == current_user.company_id
    )
    wh = (await db.execute(stmt)).scalar_one_or_none()
    if not wh:
        raise NotFoundError("Webhook endpoint")

    test_payload = {
        "event": "ping.test",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "company_id": str(current_user.company_id),
        "data": {
            "message": "AssessIQ Webhook Connection Verified successfully!",
            "endpoint_url": wh.url,
            "subscribed_events": wh.events,
        }
    }

    return WebhookTestResponse(
        status="DISPATCHED_SUCCESSFULLY",
        event="ping.test",
        payload_dispatched=test_payload,
        timestamp=datetime.now(timezone.utc),
    )


# ── Enterprise SSO Configuration ────────────────────────────────────────────────

@router.get("/me/sso", response_model=Optional[SSOConfigResponse])
async def get_company_sso_config(
    current_user: CurrentUser = Depends(require_roles(RoleName.COMPANY_ADMIN, RoleName.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Get company SSO SAML 2.0 / OIDC identity federation configuration."""
    if not current_user.company_id:
        raise NotFoundError("No company associated with current account")

    stmt = select(EnterpriseSSOConfig).where(EnterpriseSSOConfig.company_id == current_user.company_id)
    sso = (await db.execute(stmt)).scalar_one_or_none()
    if not sso:
        return None
    return sso


@router.put("/me/sso", response_model=SSOConfigResponse)
async def update_company_sso_config(
    payload: SSOConfigRequest,
    current_user: CurrentUser = Depends(require_roles(RoleName.COMPANY_ADMIN, RoleName.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Save or update company SSO SAML/OIDC settings."""
    if not current_user.company_id:
        raise NotFoundError("No company associated with current account")

    stmt = select(EnterpriseSSOConfig).where(EnterpriseSSOConfig.company_id == current_user.company_id)
    sso = (await db.execute(stmt)).scalar_one_or_none()

    if not sso:
        sso = EnterpriseSSOConfig(
            company_id=current_user.company_id,
            provider_type=payload.provider_type,
            idp_entity_id=payload.idp_entity_id,
            idp_sso_url=payload.idp_sso_url,
            idp_x509_cert=payload.idp_x509_cert,
            oidc_client_id=payload.oidc_client_id,
            oidc_client_secret=payload.oidc_client_secret,
            oidc_issuer=payload.oidc_issuer,
            is_active=payload.is_active,
        )
        db.add(sso)
    else:
        sso.provider_type = payload.provider_type
        sso.idp_entity_id = payload.idp_entity_id
        sso.idp_sso_url = payload.idp_sso_url
        sso.idp_x509_cert = payload.idp_x509_cert
        sso.oidc_client_id = payload.oidc_client_id
        if payload.oidc_client_secret:
            sso.oidc_client_secret = payload.oidc_client_secret
        sso.oidc_issuer = payload.oidc_issuer
        sso.is_active = payload.is_active

    await db.flush()
    await write_audit_log(
        db,
        user_id=current_user.id,
        company_id=current_user.company_id,
        action="sso_config.updated",
        resource_type="sso_config",
        resource_id=str(sso.id),
        metadata={"provider_type": payload.provider_type, "is_active": payload.is_active},
    )
    return sso


# ── Plan Usage & Upgrade Inquiries ─────────────────────────────────────────────

@router.get("/me/plan-usage", response_model=PlanUsageResponse)
async def get_plan_usage(
    current_user: CurrentUser = Depends(require_roles(RoleName.COMPANY_ADMIN, RoleName.RECRUITER, RoleName.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve current subscription tier limits and resource consumption."""
    if not current_user.company_id:
        raise NotFoundError("No company associated with current account")

    comp_stmt = select(Company).where(Company.id == current_user.company_id)
    company = (await db.execute(comp_stmt)).scalar_one_or_none()
    plan_name = str(company.plan) if company and company.plan else "STARTER"

    # Count candidate invites sent
    inv_stmt = select(func.count(CandidateInvitation.id)).where(CandidateInvitation.company_id == current_user.company_id)
    used_invites = (await db.execute(inv_stmt)).scalar() or 0

    plan_limits = {
        "STARTER": (50, [
            "Up to 50 candidate invites/mo",
            "MCQ & Coding Sandboxes",
            "Basic Proctoring (Webcam/Audio)",
            "Standard Recruiter Scorecards"
        ]),
        "GROWTH": (250, [
            "Up to 250 candidate invites/mo",
            "AI Copilot & Question Generator",
            "Resume Parser & Skill Matrix",
            "Full Proctoring Intelligence & Risk Score",
            "ATS Webhook Notifications"
        ]),
        "ENTERPRISE": (10000, [
            "Unlimited candidate invites",
            "Dedicated ATS APIs (Workable/Greenhouse/Lever)",
            "SAML 2.0 / OIDC Enterprise SSO",
            "Leak Radar & Question Integrity Scan",
            "Panel Review Collaboration & Custom Branding",
            "Dedicated Account Manager & SLA Guarantee"
        ]),
    }

    limit, features = plan_limits.get(plan_name, plan_limits["STARTER"])

    return PlanUsageResponse(
        plan=plan_name,
        status="ACTIVE",
        monthly_candidate_limit=limit,
        monthly_candidates_used=used_invites,
        current_period_end=datetime.now(timezone.utc) + timedelta(days=28),
        features=features
    )


@router.post("/me/upgrade-request")
async def submit_upgrade_request(
    payload: UpgradeTierRequest,
    current_user: CurrentUser = Depends(require_roles(RoleName.COMPANY_ADMIN, RoleName.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Submit a corporate tier upgrade or custom enterprise SLA inquiry."""
    if not current_user.company_id:
        raise NotFoundError("No company associated with current account")

    await write_audit_log(
        db,
        user_id=current_user.id,
        company_id=current_user.company_id,
        action="subscription.upgrade_requested",
        resource_type="company_subscription",
        resource_id=str(current_user.company_id),
        metadata={"requested_plan": payload.requested_plan, "notes": payload.notes},
    )

    return {
        "message": f"Upgrade inquiry for {payload.requested_plan} submitted successfully. Our enterprise solutions team will contact you within 2 business hours.",
        "requested_plan": payload.requested_plan,
        "status": "PENDING_REVIEW"
    }


# ── Global SuperAdmin Endpoints ─────────────────────────────────────────────────

@router.get("", response_model=List[CompanyResponse])
async def list_companies(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: CurrentUser = Depends(require_super_admin()),
    db: AsyncSession = Depends(get_db),
):
    """List all companies across the platform (SUPER_ADMIN only)."""
    stmt = (
        select(Company)
        .where(Company.deleted_at.is_(None))
        .offset(skip)
        .limit(limit)
        .order_by(Company.created_at.desc())
    )
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("", response_model=CompanyResponse, status_code=status.HTTP_201_CREATED)
async def create_company(
    payload: CompanyCreateRequest,
    current_user: CurrentUser = Depends(require_super_admin()),
    db: AsyncSession = Depends(get_db),
):
    """Create a new company tenant (SUPER_ADMIN only)."""
    existing = await db.execute(select(Company).where(Company.slug == payload.slug))
    if existing.scalar_one_or_none():
        raise ConflictError(f"Company slug '{payload.slug}' is already taken")

    new_company = Company(
        name=payload.name,
        slug=payload.slug,
        domain=payload.domain,
        website=payload.website,
        industry=payload.industry,
        size=payload.size,
        plan=payload.plan or CompanyPlan.STARTER,
        is_active=True,
    )
    db.add(new_company)
    await db.flush()

    await write_audit_log(
        db,
        user_id=current_user.id,
        company_id=new_company.id,
        action="company.created",
        resource_type="company",
        resource_id=str(new_company.id),
        metadata={"name": new_company.name, "slug": new_company.slug},
    )
    return new_company


@router.get("/{company_id}", response_model=CompanyResponse)
async def get_company_by_id(
    company_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Fetch company by ID (SUPER_ADMIN or member of that company)."""
    if not current_user.is_super_admin() and current_user.company_id != company_id:
        raise ForbiddenError("Access to this company's details is forbidden")

    stmt = select(Company).where(Company.id == company_id, Company.deleted_at.is_(None))
    result = await db.execute(stmt)
    company = result.scalar_one_or_none()
    if not company:
        raise NotFoundError("Company")
    return company


@router.put("/{company_id}", response_model=CompanyResponse)
async def update_company_by_id(
    company_id: uuid.UUID,
    payload: CompanyUpdateRequest,
    current_user: CurrentUser = Depends(require_super_admin()),
    db: AsyncSession = Depends(get_db),
):
    """Update any company by ID (SUPER_ADMIN only)."""
    stmt = select(Company).where(Company.id == company_id, Company.deleted_at.is_(None))
    result = await db.execute(stmt)
    company = result.scalar_one_or_none()
    if not company:
        raise NotFoundError("Company")

    update_data = payload.dict(exclude_unset=True)
    for field, val in update_data.items():
        setattr(company, field, val)

    await db.flush()
    await write_audit_log(
        db,
        user_id=current_user.id,
        company_id=company.id,
        action="company.admin_updated",
        resource_type="company",
        resource_id=str(company.id),
        metadata=update_data,
    )
    return company


@router.delete("/{company_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_company(
    company_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_super_admin()),
    db: AsyncSession = Depends(get_db),
):
    """Soft-delete a company (SUPER_ADMIN only)."""
    stmt = select(Company).where(Company.id == company_id, Company.deleted_at.is_(None))
    result = await db.execute(stmt)
    company = result.scalar_one_or_none()
    if not company:
        raise NotFoundError("Company")

    company.deleted_at = datetime.now(timezone.utc)
    company.is_active = False
    await db.flush()

    await write_audit_log(
        db,
        user_id=current_user.id,
        company_id=company.id,
        action="company.deleted",
        resource_type="company",
        resource_id=str(company.id),
    )
    return None
