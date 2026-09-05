import pytest
from httpx import AsyncClient
from tests.conftest import auth_headers

@pytest.mark.asyncio
async def test_company_portal_api_keys_webhooks_sso(client: AsyncClient, seed_data):
    admin_a = seed_data["admin_a"]
    company_a = seed_data["company_a"]
    headers = auth_headers(admin_a, ["COMPANY_ADMIN"], company_a.id)

    # 1. Test Company Stats
    stats_res = await client.get("/api/v1/companies/me/stats", headers=headers)
    assert stats_res.status_code == 200
    stats_data = stats_res.json()
    assert "total_assessments" in stats_data
    assert "total_candidates" in stats_data
    assert "team_members_count" in stats_data

    # 2. Test Plan Usage
    plan_res = await client.get("/api/v1/companies/me/plan-usage", headers=headers)
    assert plan_res.status_code == 200
    plan_data = plan_res.json()
    assert "monthly_candidate_limit" in plan_data
    assert "features" in plan_data
    assert len(plan_data["features"]) > 0

    # 3. Test Upgrade Request
    up_res = await client.post("/api/v1/companies/me/upgrade-request", headers=headers, json={
        "requested_plan": "ENTERPRISE",
        "notes": "Scaling for 500+ candidates"
    })
    assert up_res.status_code == 200
    assert up_res.json()["requested_plan"] == "ENTERPRISE"
    assert up_res.json()["status"] == "PENDING_REVIEW"

    # 4. Test API Key Generation
    key_res = await client.post("/api/v1/companies/me/api-keys", headers=headers, json={
        "name": "Greenhouse ATS Production Key",
        "expires_in_days": 90
    })
    assert key_res.status_code == 201
    key_data = key_res.json()
    assert key_data["name"] == "Greenhouse ATS Production Key"
    assert key_data["raw_key"].startswith("aiq_live_")
    key_id = key_data["id"]

    # 5. Test List API Keys
    list_keys_res = await client.get("/api/v1/companies/me/api-keys", headers=headers)
    assert list_keys_res.status_code == 200
    keys_list = list_keys_res.json()
    assert any(k["id"] == key_id for k in keys_list)

    # 6. Test Revoke API Key
    del_key_res = await client.delete(f"/api/v1/companies/me/api-keys/{key_id}", headers=headers)
    assert del_key_res.status_code == 204

    # 7. Test Webhook Registration
    wh_res = await client.post("/api/v1/companies/me/webhooks", headers=headers, json={
        "url": "https://api.acmecorp.com/webhooks/assessiq",
        "events": ["candidate.submitted", "proctoring.flagged"]
    })
    assert wh_res.status_code == 201
    wh_data = wh_res.json()
    assert wh_data["url"] == "https://api.acmecorp.com/webhooks/assessiq"
    assert "candidate.submitted" in wh_data["events"]
    wh_id = wh_data["id"]

    # 8. Test Webhook Ping
    ping_res = await client.post(f"/api/v1/companies/me/webhooks/{wh_id}/test", headers=headers)
    assert ping_res.status_code == 200
    assert ping_res.json()["status"] == "DISPATCHED_SUCCESSFULLY"

    # 9. Test Delete Webhook
    del_wh_res = await client.delete(f"/api/v1/companies/me/webhooks/{wh_id}", headers=headers)
    assert del_wh_res.status_code == 204

    # 10. Test SSO Configuration
    sso_res = await client.put("/api/v1/companies/me/sso", headers=headers, json={
        "provider_type": "SAML",
        "idp_entity_id": "https://sts.windows.net/acme-tenant/",
        "idp_sso_url": "https://login.microsoftonline.com/acme/saml2",
        "is_active": True
    })
    assert sso_res.status_code == 200
    assert sso_res.json()["provider_type"] == "SAML"
    assert sso_res.json()["is_active"] is True

    # 11. Test Get SSO
    get_sso_res = await client.get("/api/v1/companies/me/sso", headers=headers)
    assert get_sso_res.status_code == 200
    assert get_sso_res.json()["idp_entity_id"] == "https://sts.windows.net/acme-tenant/"

    # 12. Test Candidate Directory
    cand_res = await client.get("/api/v1/companies/me/candidates", headers=headers)
    assert cand_res.status_code == 200
    assert isinstance(cand_res.json(), list)
