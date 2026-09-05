"""
Authentication routes — login, logout, token refresh, candidate registration, self-serve company registration.
"""
from datetime import datetime, timedelta, timezone
import uuid
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field, field_validator

from fastapi import APIRouter, Depends, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token_value,
    hash_token,
)
from core.exceptions import BadRequestError, UnauthorizedError, ConflictError
from core.audit import write_audit_log
from database import get_db
from modules.users.models import User, RefreshToken
from modules.companies.models import Company
from modules.roles.models import Role, UserRole
from modules.candidates.models import Candidate
from dependencies import get_current_user, CurrentUser
from config import settings

router = APIRouter()


# ── Pydantic Schemas ──────────────────────────────────────────────────────────
class RegisterCandidateRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class RegisterCompanyRequest(BaseModel):
    company_name: str = Field(min_length=2, max_length=255)
    company_slug: str = Field(min_length=2, max_length=100)
    admin_email: EmailStr
    admin_password: str = Field(min_length=8)
    admin_first_name: Optional[str] = None
    admin_last_name: Optional[str] = None

    @field_validator("company_slug")
    def slug_must_be_alphanumeric(cls, v: str) -> str:
        if not v.replace("-", "").isalnum():
            raise ValueError("company_slug must be alphanumeric or hyphens only")
        return v.lower().strip()


class LoginRequest(BaseModel):
    email: Optional[str] = None
    username: Optional[str] = None
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    refresh_token: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str


# ── Routes ────────────────────────────────────────────────────────────────────
@router.post("/login", response_model=TokenResponse)
async def login(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Authenticate user with email/username and password via JSON or URL-encoded form data."""
    login_user = ""
    login_pass = ""

    content_type = request.headers.get("content-type", "").lower()
    if "application/json" in content_type:
        try:
            body = await request.json()
            login_user = str(body.get("email") or body.get("username") or "").strip().lower()
            login_pass = str(body.get("password") or "")
        except Exception:
            raise BadRequestError("Malformed JSON login body")
    else:
        # Form data fallback
        try:
            form = await request.form()
            login_user = str(form.get("username") or form.get("email") or "").strip().lower()
            login_pass = str(form.get("password") or "")
        except Exception:
            raise BadRequestError("Invalid form data submission")

    if not login_user or not login_pass:
        raise UnauthorizedError("Email and password are required")

    stmt = (
        select(User)
        .where(User.email == login_user, User.deleted_at.is_(None))
        .limit(1)
    )
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if not user or not verify_password(login_pass, user.hashed_password):
        raise UnauthorizedError("Invalid email or password")
    if not user.is_active:
        raise UnauthorizedError("Account has been disabled")

    # Resolve roles for the JWT payload
    stmt = (
        select(Role.name)
        .join(UserRole, UserRole.role_id == Role.id)
        .where(UserRole.user_id == user.id)
    )
    role_result = await db.execute(stmt)
    role_names = [r for r in role_result.scalars().all()]

    payload = {
        "sub": str(user.id),
        "roles": role_names,
    }
    if user.company_id:
        payload["company_id"] = str(user.company_id)

    access_token = create_access_token(payload)
    refresh_raw = create_refresh_token_value()
    refresh_hashed = hash_token(refresh_raw)
    refresh_entry = RefreshToken(
        user_id=user.id,
        token_hash=refresh_hashed,
        expires_at=(datetime.now(timezone.utc) + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)).isoformat(),
        revoked=False,
    )
    db.add(refresh_entry)
    await db.flush()

    await write_audit_log(
        db,
        user_id=user.id,
        company_id=user.company_id,
        action="auth.login",
        resource_type="user",
        resource_id=str(user.id),
    )

    return TokenResponse(access_token=access_token, refresh_token=refresh_raw)


@router.post("/register-company", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register_company(
    payload: RegisterCompanyRequest,
    db: AsyncSession = Depends(get_db),
):
    """Self-serve company onboarding: creates company, admin user, and COMPANY_ADMIN role in one transaction."""
    # Check slug uniqueness
    existing_comp = await db.execute(select(Company).where(Company.slug == payload.company_slug))
    if existing_comp.scalar_one_or_none():
        raise ConflictError("Company slug already in use")

    # Check admin email uniqueness globally
    user_check = await db.execute(select(User).where(User.email == payload.admin_email.strip().lower()))
    if user_check.scalar_one_or_none():
        raise ConflictError("Admin email already registered")

    new_company = Company(
        name=payload.company_name,
        slug=payload.company_slug,
        is_active=True,
    )
    db.add(new_company)
    await db.flush()

    admin_user = User(
        email=payload.admin_email.strip().lower(),
        hashed_password=hash_password(payload.admin_password),
        first_name=payload.admin_first_name,
        last_name=payload.admin_last_name,
        company_id=new_company.id,
        is_active=True,
        is_email_verified=False,
    )
    db.add(admin_user)
    await db.flush()

    # Assign COMPANY_ADMIN role
    admin_role = await db.execute(select(Role).where(Role.name == "COMPANY_ADMIN"))
    role_obj = admin_role.scalar_one_or_none()
    if not role_obj:
        role_obj = Role(name="COMPANY_ADMIN", description="Administrator for an organization")
        db.add(role_obj)
        await db.flush()

    user_role = UserRole(user_id=admin_user.id, role_id=role_obj.id, company_id=new_company.id)
    db.add(user_role)
    await db.flush()

    # Issue tokens
    token_payload = {
        "sub": str(admin_user.id),
        "roles": ["COMPANY_ADMIN"],
        "company_id": str(new_company.id),
    }
    access_token = create_access_token(token_payload)
    refresh_raw = create_refresh_token_value()
    refresh_hashed = hash_token(refresh_raw)
    refresh_entry = RefreshToken(
        user_id=admin_user.id,
        token_hash=refresh_hashed,
        expires_at=(datetime.now(timezone.utc) + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)).isoformat(),
        revoked=False,
    )
    db.add(refresh_entry)
    await db.flush()

    await write_audit_log(
        db,
        user_id=admin_user.id,
        company_id=new_company.id,
        action="company.self_registered",
        resource_type="company",
        resource_id=str(new_company.id),
    )

    return TokenResponse(access_token=access_token, refresh_token=refresh_raw)


@router.post("/register-candidate", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register_candidate(
    payload: RegisterCandidateRequest,
    db: AsyncSession = Depends(get_db),
):
    """Register a global candidate account."""
    user_check = await db.execute(select(User).where(User.email == payload.email.strip().lower()))
    if user_check.scalar_one_or_none():
        raise ConflictError("An account with this email already exists")

    candidate_user = User(
        email=payload.email.strip().lower(),
        hashed_password=hash_password(payload.password),
        first_name=payload.first_name,
        last_name=payload.last_name,
        company_id=None,  # Candidate is global
        is_active=True,
        is_email_verified=False,
    )
    db.add(candidate_user)
    await db.flush()

    # Assign CANDIDATE role
    cand_role = await db.execute(select(Role).where(Role.name == "CANDIDATE"))
    role_obj = cand_role.scalar_one_or_none()
    if not role_obj:
        role_obj = Role(name="CANDIDATE", description="Assessment test-taker")
        db.add(role_obj)
        await db.flush()

    user_role = UserRole(user_id=candidate_user.id, role_id=role_obj.id, company_id=None)
    db.add(user_role)

    # Create candidate profile
    cand_profile = Candidate(user_id=candidate_user.id)
    db.add(cand_profile)
    await db.flush()

    token_payload = {
        "sub": str(candidate_user.id),
        "roles": ["CANDIDATE"],
    }
    access_token = create_access_token(token_payload)
    refresh_raw = create_refresh_token_value()
    refresh_hashed = hash_token(refresh_raw)
    refresh_entry = RefreshToken(
        user_id=candidate_user.id,
        token_hash=refresh_hashed,
        expires_at=(datetime.now(timezone.utc) + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)).isoformat(),
        revoked=False,
    )
    db.add(refresh_entry)
    await db.flush()

    await write_audit_log(
        db,
        user_id=candidate_user.id,
        company_id=None,
        action="candidate.registered",
        resource_type="candidate",
        resource_id=str(candidate_user.id),
    )

    return TokenResponse(access_token=access_token, refresh_token=refresh_raw)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    payload: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
):
    """Rotate refresh token and issue a fresh access token."""
    raw_token = payload.refresh_token
    hashed_val = hash_token(raw_token)

    stmt = select(RefreshToken).where(
        RefreshToken.token_hash == hashed_val,
        RefreshToken.revoked.is_(False),
    )
    result = await db.execute(stmt)
    token_record = result.scalar_one_or_none()

    if not token_record:
        raise UnauthorizedError("Invalid or revoked refresh token")

    # Load user
    user_stmt = select(User).where(User.id == token_record.user_id, User.deleted_at.is_(None))
    user_res = await db.execute(user_stmt)
    user = user_res.scalar_one_or_none()
    if not user or not user.is_active:
        raise UnauthorizedError("User is inactive or deleted")

    # Revoke old refresh token (secure rotation)
    token_record.revoked = True

    # Issue new tokens
    stmt = (
        select(Role.name)
        .join(UserRole, UserRole.role_id == Role.id)
        .where(UserRole.user_id == user.id)
    )
    role_result = await db.execute(stmt)
    role_names = [r for r in role_result.scalars().all()]

    jwt_payload = {"sub": str(user.id), "roles": role_names}
    if user.company_id:
        jwt_payload["company_id"] = str(user.company_id)

    new_access_token = create_access_token(jwt_payload)
    new_refresh_raw = create_refresh_token_value()
    new_refresh_hashed = hash_token(new_refresh_raw)

    new_refresh_entry = RefreshToken(
        user_id=user.id,
        token_hash=new_refresh_hashed,
        expires_at=(datetime.now(timezone.utc) + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)).isoformat(),
        revoked=False,
    )
    db.add(new_refresh_entry)
    await db.flush()

    return TokenResponse(access_token=new_access_token, refresh_token=new_refresh_raw)


@router.post("/logout")
async def logout(
    payload: Optional[RefreshTokenRequest] = None,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Revoke user refresh token on logout."""
    if payload and payload.refresh_token:
        hashed_val = hash_token(payload.refresh_token)
        await db.execute(
            update(RefreshToken)
            .where(RefreshToken.token_hash == hashed_val)
            .values(revoked=True)
        )
    else:
        # Revoke all active refresh tokens for this user
        await db.execute(
            update(RefreshToken)
            .where(RefreshToken.user_id == current_user.id)
            .values(revoked=True)
        )
    await db.flush()

    await write_audit_log(
        db,
        user_id=current_user.id,
        company_id=current_user.company_id,
        action="auth.logout",
        resource_type="user",
        resource_id=str(current_user.id),
    )
    return {"status": "success", "message": "Successfully logged out"}
