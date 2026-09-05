# apps/api/schemas.py
"""Pydantic schema definitions for AssessIQ Phase 1.
These models are used for request validation and response serialization.
All schemas are ORM‑compatible (Config.orm_mode = True) so they can be returned directly from SQLAlchemy model instances.
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field, validator

# ---------------------------------------------------------------------------
# Base class
# ---------------------------------------------------------------------------
class ORMBase(BaseModel):
    """Base class that enables ORM mode for all derived schemas."""

    class Config:
        orm_mode = True

# ---------------------------------------------------------------------------
# Company
# ---------------------------------------------------------------------------
class CompanyBase(ORMBase):
    name: str = Field(..., min_length=1, max_length=200)
    domain: Optional[str] = Field(None, max_length=200, description="Optional company email domain for auto‑invite.")

class CompanyCreate(CompanyBase):
    pass

class CompanyRead(CompanyBase):
    id: str  # UUID string
    created_at: datetime
    updated_at: datetime
    is_active: bool = True

# ---------------------------------------------------------------------------
# Role
# ---------------------------------------------------------------------------
class RoleBase(ORMBase):
    name: str = Field(..., description="One of SUPER_ADMIN, COMPANY_ADMIN, RECRUITER, QUESTION_MANAGER, CANDIDATE")

class RoleRead(RoleBase):
    id: str
    description: Optional[str] = None

# ---------------------------------------------------------------------------
# User / UserRole
# ---------------------------------------------------------------------------
class UserBase(ORMBase):
    email: EmailStr
    full_name: Optional[str] = None

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)
    company_id: Optional[str] = None  # Null for SUPER_ADMIN

class UserRead(UserBase):
    id: str
    is_active: bool = True
    created_at: datetime
    updated_at: datetime
    company_id: Optional[str] = None
    roles: List[RoleRead] = []

# ---------------------------------------------------------------------------
# Candidate & Profile
# ---------------------------------------------------------------------------
class CandidateProfileBase(ORMBase):
    resume_url: Optional[str] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None

class CandidateProfileRead(CandidateProfileBase):
    id: str
    candidate_id: str
    created_at: datetime
    updated_at: datetime

class CandidateBase(ORMBase):
    email: EmailStr
    full_name: Optional[str] = None

class CandidateCreate(CandidateBase):
    company_id: Optional[str] = None  # candidates can be invited across companies
    profile: Optional[CandidateProfileBase] = None

class CandidateRead(CandidateBase):
    id: str
    created_at: datetime
    updated_at: datetime
    company_id: Optional[str] = None
    profile: Optional[CandidateProfileRead] = None

# ---------------------------------------------------------------------------
# Audit Log
# ---------------------------------------------------------------------------
class AuditLogBase(ORMBase):
    action: str = Field(..., max_length=100)
    performed_by: str = Field(..., description="User UUID that performed the action")
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    details: Optional[dict] = Field(default_factory=dict)

class AuditLogRead(AuditLogBase):
    id: str
    timestamp: datetime

# ---------------------------------------------------------------------------
# Helper validators (example)
# ---------------------------------------------------------------------------
@validator("resume_url", "linkedin_url", "github_url", pre=True, always=True)
def empty_str_to_none(cls, v: Optional[str]):
    return v or None
