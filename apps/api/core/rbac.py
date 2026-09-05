"""
Role-Based Access Control (RBAC) permission matrix.

Roles (in ascending privilege order):
  CANDIDATE < QUESTION_MANAGER < RECRUITER < COMPANY_ADMIN < SUPER_ADMIN

Every role check is enforced server-side via FastAPI dependencies.
Never rely on frontend-only role gating.
"""
from enum import Enum
from typing import Set


class RoleName(str, Enum):
    SUPER_ADMIN = "SUPER_ADMIN"
    COMPANY_ADMIN = "COMPANY_ADMIN"
    RECRUITER = "RECRUITER"
    QUESTION_MANAGER = "QUESTION_MANAGER"
    CANDIDATE = "CANDIDATE"


# Roles ordered from highest to lowest privilege
ROLE_HIERARCHY: list[RoleName] = [
    RoleName.SUPER_ADMIN,
    RoleName.COMPANY_ADMIN,
    RoleName.RECRUITER,
    RoleName.QUESTION_MANAGER,
    RoleName.CANDIDATE,
]


# Permissions each role has (additive model)
ROLE_PERMISSIONS: dict[RoleName, Set[str]] = {
    RoleName.SUPER_ADMIN: {
        "companies:read",
        "companies:write",
        "companies:delete",
        "users:read",
        "users:write",
        "users:delete",
        "subscriptions:read",
        "subscriptions:write",
        "audit_logs:read",
        "platform:admin",
    },
    RoleName.COMPANY_ADMIN: {
        "company:read",
        "company:write",
        "users:read",
        "users:write",
        "users:invite",
        "jobs:read",
        "jobs:write",
        "campaigns:read",
        "campaigns:write",
        "assessments:read",
        "assessments:write",
        "assessments:publish",
        "candidates:read",
        "candidates:invite",
        "results:read",
        "shortlist:write",
        "reports:read",
    },
    RoleName.RECRUITER: {
        "jobs:read",
        "jobs:write",
        "campaigns:read",
        "campaigns:write",
        "assessments:read",
        "assessments:write",
        "candidates:read",
        "candidates:invite",
        "results:read",
        "integrity:read",
        "integrity:review",
        "shortlist:write",
        "reports:read",
    },
    RoleName.QUESTION_MANAGER: {
        "questions:read",
        "questions:write",
        "questions:review",
        "questions:approve",
    },
    RoleName.CANDIDATE: {
        "profile:read",
        "profile:write",
        "assessments:take",
        "results:read_own",
    },
}


def get_user_permissions(roles: list[RoleName]) -> Set[str]:
    """Return the union of all permissions for the given roles."""
    permissions: Set[str] = set()
    for role in roles:
        permissions |= ROLE_PERMISSIONS.get(role, set())
    return permissions


def has_permission(user_roles: list[RoleName], permission: str) -> bool:
    return permission in get_user_permissions(user_roles)


def has_any_role(user_roles: list[RoleName], required: list[RoleName]) -> bool:
    return bool(set(user_roles) & set(required))
