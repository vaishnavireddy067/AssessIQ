"""
AssessIQ Webhook Dispatcher Engine (Phase 8).
Sends HMAC-signed JSON payloads to tenant webhook endpoints for ATS integrations.
"""
import json
import hmac
import hashlib
import httpx
import uuid
import datetime
import asyncio
from typing import Dict, Any, List

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from modules.companies.enterprise_models import WebhookEndpoint, WebhookEvent


async def dispatch_webhook_event(
    db: AsyncSession,
    company_id: uuid.UUID,
    event_type: WebhookEvent,
    payload: Dict[str, Any]
) -> None:
    """
    Looks up active webhook endpoints for a company that subscribe to `event_type`,
    generates an HMAC-SHA256 signature, and asynchronously fires HTTP POST requests.
    """
    stmt = sa.select(WebhookEndpoint).where(
        WebhookEndpoint.company_id == company_id,
        WebhookEndpoint.is_active == True
    )
    endpoints: List[WebhookEndpoint] = (await db.execute(stmt)).scalars().all()

    # Filter endpoints subscribed to this specific event
    subscribed_endpoints = [
        ep for ep in endpoints if event_type.value in ep.events or "*" in ep.events
    ]

    if not subscribed_endpoints:
        return

    # Standardize the webhook payload structure
    webhook_payload = {
        "event_id": str(uuid.uuid4()),
        "event_type": event_type.value,
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "data": payload
    }
    
    body_bytes = json.dumps(webhook_payload, separators=(',', ':')).encode('utf-8')

    # Fire and forget (in a real production system, this should use Celery/Redis for retries)
    asyncio.create_task(_send_webhooks_concurrently(subscribed_endpoints, body_bytes))


async def _send_webhooks_concurrently(endpoints: List[WebhookEndpoint], body_bytes: bytes):
    async with httpx.AsyncClient(timeout=10.0) as client:
        tasks = []
        for ep in endpoints:
            signature = hmac.new(
                ep.secret_key.encode('utf-8'),
                body_bytes,
                hashlib.sha256
            ).hexdigest()

            headers = {
                "Content-Type": "application/json",
                "AssessIQ-Signature": f"sha256={signature}",
                "User-Agent": "AssessIQ-Webhook-Dispatcher/1.0"
            }

            tasks.append(client.post(ep.url, content=body_bytes, headers=headers))
        
        # Fire all requests concurrently, ignoring failures in this simplified implementation
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for idx, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"[WEBHOOK ERROR] Failed to send webhook to {endpoints[idx].url}: {result}")
            else:
                print(f"[WEBHOOK SUCCESS] Sent to {endpoints[idx].url} (Status: {result.status_code})")
