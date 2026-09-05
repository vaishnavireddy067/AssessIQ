"""
Users router — user profile management, user creation within company, and listing.
"""
import uuid
from datetime import datetime, timezone
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database import get_db
from core.security import hash_password, verify_password
from core.rbac import RoleName
from core.exceptions import NotFoundError, ConflictError, ForbiddenError, BadRequestError, UnauthorizedError
from core.audit import write_audit_log
from dependencies import get_current_user, require_roles, CurrentUser
from modules.users.models import User
from modules.roles.models import Role, UserRole
from modules.companies.models import Company

router = APIRouter()


# ── Schemas ───────────────────────────────────────────────────────────────────
class UserProfileResponse(BaseModel):
    id: uuid.UUID
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    full_name: Optional[str] = None
    phone: Optional[str] = None
    avatar_url: Optional[str] = None
    is_active: bool
    is_email_verified: bool
    company_id: Optional[uuid.UUID] = None
    roles: List[str] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserUpdateMeRequest(BaseModel):
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=30)
    avatar_url: Optional[str] = None


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8)


class CreateUserRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role_name: RoleName = RoleName.RECRUITER
    company_id: Optional[uuid.UUID] = None  # Super admin can specify, Company Admin uses their own


# ── Helper to resolve user response ───────────────────────────────────────────
async def build_user_profile(user: User, db: AsyncSession) -> UserProfileResponse:
    stmt = (
        select(Role.name)
        .join(UserRole, UserRole.role_id == Role.id)
        .where(UserRole.user_id == user.id)
    )
    result = await db.execute(stmt)
    role_names = [r for r in result.scalars().all()]

    return UserProfileResponse(
        id=user.id,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        full_name=user.full_name,
        phone=user.phone,
        avatar_url=user.avatar_url,
        is_active=user.is_active,
        is_email_verified=user.is_email_verified,
        company_id=user.company_id,
        roles=role_names,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


# ── Routes ────────────────────────────────────────────────────────────────────
@router.get("/me", response_model=UserProfileResponse)
async def get_my_profile(
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve profile and roles for the currently authenticated user."""
    return await build_user_profile(current_user.user, db)


@router.put("/me", response_model=UserProfileResponse)
async def update_my_profile(
    payload: UserUpdateMeRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update profile details of currently logged-in user."""
    user = current_user.user
    for field, val in payload.dict(exclude_unset=True).items():
        setattr(user, field, val)

    await db.flush()
    await write_audit_log(
        db,
        user_id=user.id,
        company_id=user.company_id,
        action="user.profile_updated",
        resource_type="user",
        resource_id=str(user.id),
    )
    return await build_user_profile(user, db)


@router.post("/change-password")
async def change_password(
    payload: ChangePasswordRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Change password for the logged-in user."""
    user = current_user.user
    if not verify_password(payload.current_password, user.hashed_password):
        raise UnauthorizedError("Incorrect current password")

    user.hashed_password = hash_password(payload.new_password)
    await db.flush()

    await write_audit_log(
        db,
        user_id=user.id,
        company_id=user.company_id,
        action="user.password_changed",
        resource_type="user",
        resource_id=str(user.id),
    )
    return {"status": "success", "message": "Password changed successfully"}


@router.get("", response_model=List[UserProfileResponse])
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: CurrentUser = Depends(require_roles(RoleName.SUPER_ADMIN, RoleName.COMPANY_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """List users within tenant scope (Company Admin sees company users; Super Admin sees all)."""
    stmt = select(User).where(User.deleted_at.is_(None))
    if not current_user.is_super_admin():
        stmt = stmt.where(User.company_id == current_user.company_id)

    stmt = stmt.offset(skip).limit(limit).order_by(User.created_at.desc())
    result = await db.execute(stmt)
    users = result.scalars().all()

    responses = []
    for u in users:
        responses.append(await build_user_profile(u, db))
    return responses


@router.post("", response_model=UserProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    payload: CreateUserRequest,
    current_user: CurrentUser = Depends(require_roles(RoleName.SUPER_ADMIN, RoleName.COMPANY_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Create a user within the company (COMPANY_ADMIN) or across companies (SUPER_ADMIN)."""
    existing = await db.execute(select(User).where(User.email == payload.email))
    if existing.scalar_one_or_none():
        raise ConflictError("User with this email already exists")

    # Determine target company
    if current_user.is_super_admin():
        target_company_id = payload.company_id
    else:
        target_company_id = current_user.company_id

    # If assigning a role, ensure Company Admin cannot grant SUPER_ADMIN
    if not current_user.is_super_admin() and payload.role_name == RoleName.SUPER_ADMIN:
        raise ForbiddenError("Cannot grant SUPER_ADMIN privileges")

    new_user = User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        first_name=payload.first_name,
        last_name=payload.last_name,
        company_id=target_company_id,
        is_active=True,
        is_email_verified=True,
    )
    db.add(new_user)
    await db.flush()

    # Assign requested role
    role_query = await db.execute(select(Role).where(Role.name == payload.role_name.value))
    role_obj = role_query.scalar_one_or_none()
    if not role_obj:
        role_obj = Role(name=payload.role_name.value)
        db.add(role_obj)
        await db.flush()

    user_role = UserRole(user_id=new_user.id, role_id=role_obj.id, company_id=target_company_id)
    db.add(user_role)
    await db.flush()

    await write_audit_log(
        db,
        user_id=current_user.id,
        company_id=target_company_id,
        action="user.created",
        resource_type="user",
        resource_id=str(new_user.id),
        metadata={"email": new_user.email, "role": payload.role_name.value},
    )

    return await build_user_profile(new_user, db)


@router.get("/{user_id}", response_model=UserProfileResponse)
async def get_user_by_id(
    user_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_roles(RoleName.SUPER_ADMIN, RoleName.COMPANY_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Get user details by ID within tenant boundary."""
    stmt = select(User).where(User.id == user_id, User.deleted_at.is_(None))
    if not current_user.is_super_admin():
        stmt = stmt.where(User.company_id == current_user.company_id)

    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if not user:
        raise NotFoundError("User")
    return await build_user_profile(user, db)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_roles(RoleName.SUPER_ADMIN, RoleName.COMPANY_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Soft delete / deactivate a user within tenant scope."""
    if user_id == current_user.id:
        raise BadRequestError("Cannot delete your own account")

    stmt = select(User).where(User.id == user_id, User.deleted_at.is_(None))
    if not current_user.is_super_admin():
        stmt = stmt.where(User.company_id == current_user.company_id)

    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if not user:
        raise NotFoundError("User")

    user.deleted_at = datetime.now(timezone.utc)
    user.is_active = False
    await db.flush()

    await write_audit_log(
        db,
        user_id=current_user.id,
        company_id=user.company_id,
        action="user.deleted",
        resource_type="user",
        resource_id=str(user.id),
    )
    return None
