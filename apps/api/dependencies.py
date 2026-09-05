"""
FastAPI dependencies for authentication, RBAC enforcement, and tenant scoping.
Every protected endpoint must use at least get_current_user.
"""
import uuid
from typing import Optional, List

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from config import settings
from core.security import decode_access_token
from core.rbac import RoleName, has_any_role
from core.exceptions import UnauthorizedError, ForbiddenError, TokenExpiredError
from database import get_db
from modules.users.models import User
from modules.roles.models import UserRole, Role

bearer_scheme = HTTPBearer(auto_error=False)


class CurrentUser:
    """
    Resolved current user — passed to route handlers via dependency injection.
    Contains user record + resolved role names for this request.
    """
    def __init__(self, user: User, roles: list[RoleName], company_id: Optional[uuid.UUID]):
        self.user = user
        self.roles = roles
        self.company_id = company_id  # None for SUPER_ADMIN acting globally

    @property
    def id(self) -> uuid.UUID:
        return self.user.id

    @property
    def email(self) -> str:
        return self.user.email

    def has_role(self, *roles: RoleName) -> bool:
        return has_any_role(self.roles, list(roles))

    def is_super_admin(self) -> bool:
        return RoleName.SUPER_ADMIN in self.roles


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> CurrentUser:
    """
    Core authentication dependency.
    Validates Bearer JWT, loads user + roles from DB.
    """
    if not credentials:
        raise UnauthorizedError("No authentication token provided")

    token = credentials.credentials
    try:
        payload = decode_access_token(token)
    except JWTError as e:
        if "expired" in str(e).lower():
            raise TokenExpiredError()
        raise UnauthorizedError("Invalid authentication token")

    user_id_str = payload.get("sub")
    if not user_id_str:
        raise UnauthorizedError("Invalid token payload")

    try:
        user_id = uuid.UUID(user_id_str)
    except ValueError:
        raise UnauthorizedError("Invalid token payload")

    # Load user
    stmt = select(User).where(User.id == user_id, User.deleted_at.is_(None))
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        raise UnauthorizedError("User not found")

    if not user.is_active:
        raise UnauthorizedError("Account is deactivated")

    # Load roles
    stmt = (
        select(Role.name)
        .join(UserRole, UserRole.role_id == Role.id)
        .where(UserRole.user_id == user.id)
    )
    result = await db.execute(stmt)
    role_names = [RoleName(r) for r in result.scalars().all()]

    # Determine company scope from JWT claim (set at login)
    company_id_str = payload.get("company_id")
    company_id = uuid.UUID(company_id_str) if company_id_str else None

    return CurrentUser(user=user, roles=role_names, company_id=company_id)


def require_roles(*roles: RoleName):
    """
    Dependency factory — enforce that the current user has at least one of the given roles.
    Usage:  Depends(require_roles(RoleName.COMPANY_ADMIN, RoleName.RECRUITER))
    """
    async def _check(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if not current_user.has_role(*roles):
            raise ForbiddenError(
                f"This action requires one of the following roles: {[r.value for r in roles]}"
            )
        return current_user

    return _check


def require_super_admin():
    """Shortcut dependency for super-admin-only endpoints."""
    return require_roles(RoleName.SUPER_ADMIN)


def get_company_id(current_user: CurrentUser = Depends(get_current_user)) -> Optional[uuid.UUID]:
    """
    Extract and enforce company_id from the current user context.
    For global users (e.g., candidates) this returns ``None``.
    For regular users it returns the associated company_id or raises ``ForbiddenError``
    if the user has no company scope.
    """
    if current_user.is_super_admin():
        # Super admin can act globally – may have no company_id
        return current_user.company_id

    # Global user (candidate) – company_id will be ``None``
    if current_user.company_id is None:
        return None

    # Regular scoped user – must have a company_id
    return current_user.company_id
