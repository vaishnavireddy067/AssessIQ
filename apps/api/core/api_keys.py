"""
AssessIQ API Key Authentication Dependency (Phase 8).
Validates programmatic API tokens against the database for ATS integration endpoints.
"""
from fastapi import Security, HTTPException, status, Depends
from fastapi.security import APIKeyHeader
from sqlalchemy.ext.asyncio import AsyncSession
import sqlalchemy as sa
import datetime
from typing import Optional

from database import get_db
from modules.companies.enterprise_models import ApiKey

api_key_header = APIKeyHeader(name="Authorization", auto_error=False)


async def get_company_id_from_api_key(
    api_key_value: str = Security(api_key_header),
    db: AsyncSession = Depends(get_db)
) -> Optional[str]:
    """
    Validates a Bearer token or direct API Key provided in the Authorization header.
    Returns the associated company_id string.
    """
    if not api_key_value:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization API Key header"
        )
    
    # Strip Bearer prefix if provided
    token = api_key_value.replace("Bearer ", "").strip()
    
    # In a real system, you would hash the incoming token and compare it.
    # For this Phase 8 simulation, we simply look up the token hash directly.
    # (Assuming the client provides the raw token, which we hash and query).
    
    # Simulate a naive lookup (in prod, use secure compare)
    stmt = sa.select(ApiKey).where(
        ApiKey.key_hash == token,
        ApiKey.is_active == True
    )
    db_api_key = (await db.execute(stmt)).scalar_one_or_none()

    if not db_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or revoked API Key"
        )

    if db_api_key.expires_at and db_api_key.expires_at < datetime.datetime.now(datetime.timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API Key has expired"
        )

    # Update last_used_at
    db_api_key.last_used_at = datetime.datetime.now(datetime.timezone.utc)
    await db.commit()

    return str(db_api_key.company_id)
