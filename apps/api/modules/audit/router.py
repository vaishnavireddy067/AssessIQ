"""
Audit router — security event log queries.
"""
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database import get_db
from core.rbac import RoleName
from core.exceptions import NotFoundError, ForbiddenError
from dependencies import require_roles, CurrentUser
from modules.audit.models import AuditLog

router = APIRouter()


# ── Schemas ───────────────────────────────────────────────────────────────────
class AuditLogResponse(BaseModel):
    id: uuid.UUID
    user_id: Optional[uuid.UUID] = None
    company_id: Optional[uuid.UUID] = None
    action: str
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    extra_metadata: Optional[Dict[str, Any]] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ── Routes ────────────────────────────────────────────────────────────────────
@router.get("", response_model=List[AuditLogResponse])
async def list_audit_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    action: Optional[str] = Query(None),
    resource_type: Optional[str] = Query(None),
    current_user: CurrentUser = Depends(require_roles(RoleName.SUPER_ADMIN, RoleName.COMPANY_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """List audit logs within tenant authorization boundary."""
    stmt = select(AuditLog)
    if not current_user.is_super_admin():
        stmt = stmt.where(AuditLog.company_id == current_user.company_id)

    if action:
        stmt = stmt.where(AuditLog.action == action)
    if resource_type:
        stmt = stmt.where(AuditLog.resource_type == resource_type)

    stmt = stmt.offset(skip).limit(limit).order_by(AuditLog.created_at.desc())
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/{log_id}", response_model=AuditLogResponse)
async def get_audit_log(
    log_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_roles(RoleName.SUPER_ADMIN, RoleName.COMPANY_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve details for a single audit log entry."""
    stmt = select(AuditLog).where(AuditLog.id == log_id)
    if not current_user.is_super_admin():
        stmt = stmt.where(AuditLog.company_id == current_user.company_id)

    result = await db.execute(stmt)
    log = result.scalar_one_or_none()
    if not log:
        raise NotFoundError("AuditLog")
    return log
