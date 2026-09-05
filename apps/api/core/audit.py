"""
Audit logging — append-oriented security event recorder.
All sensitive actions are logged here.
Audit logs should not be modified by normal users.
"""
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import insert

from modules.audit.models import AuditLog


async def write_audit_log(
    db: AsyncSession,
    *,
    user_id: Optional[uuid.UUID],
    company_id: Optional[uuid.UUID],
    action: str,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    metadata: Optional[dict[str, Any]] = None,
) -> None:
    """
    Write a single audit log entry.
    This is fire-and-forget — errors are logged but do not abort the main operation.
    """
    try:
        log_entry = AuditLog(
            id=uuid.uuid4(),
            user_id=user_id,
            company_id=company_id,
            action=action,
            resource_type=resource_type,
            resource_id=str(resource_id) if resource_id else None,
            ip_address=ip_address,
            user_agent=user_agent,
            extra_metadata=metadata or {},
            created_at=datetime.now(timezone.utc),
        )
        db.add(log_entry)
        # Note: session commit handled by the request lifecycle
    except Exception as e:
        # Never let audit logging failures break the main request
        import logging
        logging.getLogger(__name__).error(f"Audit log write failed: {e}")
