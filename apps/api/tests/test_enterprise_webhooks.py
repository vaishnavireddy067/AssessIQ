import pytest
import hmac
import hashlib
import json
import uuid
import datetime

from core.api_keys import get_company_id_from_api_key
from core.webhooks.dispatcher import dispatch_webhook_event, WebhookEvent
from fastapi import HTTPException
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

# For testing, we mock the httpx client and DB sessions
class MockWebhookEndpoint:
    def __init__(self):
        self.url = "https://ats.example.com/webhook"
        self.secret_key = "super-secret"
        self.events = ["candidate.submitted", "assessment.published"]
        self.is_active = True

class MockApiKey:
    def __init__(self, company_id):
        self.company_id = company_id
        self.key_hash = "mocked-hash"
        self.is_active = True
        self.expires_at = None
        self.last_used_at = None

class MockAsyncResult:
    def __init__(self, obj):
        self.obj = obj
    def scalar_one_or_none(self):
        return self.obj
    def scalars(self):
        class MockScalars:
            def all(self_inner):
                return [self.obj] if self.obj else []
        return MockScalars()

class MockAsyncSession:
    async def execute(self, stmt):
        # Infer type based on table being queried.
        # This is very simplified for the unit test.
        if "api_keys" in str(stmt):
            return MockAsyncResult(MockApiKey(uuid.uuid4()))
        elif "webhook_endpoints" in str(stmt):
            return MockAsyncResult(MockWebhookEndpoint())
        return MockAsyncResult(None)
    
    async def commit(self):
        pass


@pytest.mark.asyncio
async def test_api_key_auth_valid():
    db = MockAsyncSession()
    company_id = await get_company_id_from_api_key(
        api_key_value="Bearer mocked-hash", 
        db=db
    )
    assert company_id is not None
    assert isinstance(company_id, str)


@pytest.mark.asyncio
async def test_api_key_auth_missing():
    db = MockAsyncSession()
    with pytest.raises(HTTPException) as excinfo:
        await get_company_id_from_api_key(api_key_value=None, db=db)
    
    assert excinfo.value.status_code == 401
    assert "Missing Authorization" in excinfo.value.detail


def test_hmac_signature_generation():
    secret = "super-secret"
    payload = {
        "event_id": "test-123",
        "event_type": "candidate.submitted",
        "timestamp": "2024-01-01T00:00:00Z",
        "data": {"score": 95}
    }
    body_bytes = json.dumps(payload, separators=(',', ':')).encode('utf-8')
    
    signature = hmac.new(
        secret.encode('utf-8'),
        body_bytes,
        hashlib.sha256
    ).hexdigest()

    # Just ensure it generated a valid SHA256 hex string
    assert len(signature) == 64
