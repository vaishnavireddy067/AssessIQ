"""
AssessIQ Proctoring Data Retention and Purge Policy Service.
Automates removal of sensory signals and proctoring telemetry after retention periods.
"""
import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete, select, update

from modules.proctoring.models import ProctoringSession, ProctoringEvent, CandidateConsentRecord


DEFAULT_RETENTION_DAYS = 90


async def purge_expired_proctoring_telemetry(
    db: AsyncSession,
    company_id: uuid.UUID = None,
    older_than_days: int = DEFAULT_RETENTION_DAYS,
) -> Dict[str, Any]:
    """
    Purges proctoring events and sensory metadata older than the retention threshold.
    Preserves top-level session scores and recruiter audit notes for compliance.
    """
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=older_than_days)

    # Find expired sessions
    query = select(ProctoringSession.id).where(
        (ProctoringSession.created_at < cutoff_date) |
        (ProctoringSession.retention_expires_at != None, ProctoringSession.retention_expires_at < datetime.now(timezone.utc))
    )
    session_ids = (await db.execute(query)).scalars().all()

    if not session_ids:
        return {
            "status": "success",
            "purged_sessions_count": 0,
            "purged_events_count": 0,
            "retention_cutoff": cutoff_date.isoformat(),
        }

    # Delete associated detailed event payloads
    del_stmt = delete(ProctoringEvent).where(ProctoringEvent.session_id.in_(session_ids))
    evt_result = await db.execute(del_stmt)

    # Clear heavy raw JSON from sessions while keeping summary for candidate record
    clean_stmt = (
        update(ProctoringSession)
        .where(ProctoringSession.id.in_(session_ids))
        .values(
            weighted_deductions_json=[],
            summary_notes="Proctoring telemetry and sensory events purged in accordance with data retention policy.",
        )
    )
    await db.execute(clean_stmt)
    await db.flush()

    return {
        "status": "success",
        "purged_sessions_count": len(session_ids),
        "purged_events_count": evt_result.rowcount if hasattr(evt_result, "rowcount") else len(session_ids),
        "retention_cutoff": cutoff_date.isoformat(),
    }
