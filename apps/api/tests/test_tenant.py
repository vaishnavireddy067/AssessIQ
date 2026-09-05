"""
Multi-tenant isolation and RBAC authorization tests.
"""
import pytest
from httpx import AsyncClient
from tests.conftest import auth_headers


@pytest.mark.asyncio
async def test_candidate_profile_access_global(client: AsyncClient, seed_data):
    candidate = seed_data["candidate"]
    headers = auth_headers(candidate, ["CANDIDATE"])

    # Candidate can read their own profile without any company context
    response = await client.get("/api/v1/candidates/me", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "candidate@test.com"
    assert data["resume_url"] == "https://example.com/resume.pdf"


@pytest.mark.asyncio
async def test_candidate_cannot_access_company_endpoints(client: AsyncClient, seed_data):
    candidate = seed_data["candidate"]
    company_a = seed_data["company_a"]
    headers = auth_headers(candidate, ["CANDIDATE"])

    # Candidate should get 403 Forbidden trying to access companies list or create users
    res_comp = await client.get("/api/v1/companies", headers=headers)
    assert res_comp.status_code == 403

    res_users = await client.get("/api/v1/users", headers=headers)
    assert res_users.status_code == 403


@pytest.mark.asyncio
async def test_company_admin_tenant_isolation(client: AsyncClient, seed_data):
    admin_a = seed_data["admin_a"]
    company_a = seed_data["company_a"]
    company_b = seed_data["company_b"]
    headers_a = auth_headers(admin_a, ["COMPANY_ADMIN"], company_a.id)

    # Admin A can view their own company
    res_my_company = await client.get("/api/v1/companies/me", headers=headers_a)
    assert res_my_company.status_code == 200
    assert res_my_company.json()["slug"] == "alpha-corp"

    # Admin A cannot access company B's direct details
    res_other_company = await client.get(f"/api/v1/companies/{company_b.id}", headers=headers_a)
    assert res_other_company.status_code == 403

    # Admin A listing users only sees company A's users
    res_users = await client.get("/api/v1/users", headers=headers_a)
    assert res_users.status_code == 200
    user_emails = [u["email"] for u in res_users.json()]
    assert "admin@alpha.com" in user_emails
    assert "recruiter@alpha.com" in user_emails
    assert "admin@beta.com" not in user_emails  # Isolated!


@pytest.mark.asyncio
async def test_super_admin_cross_tenant_access(client: AsyncClient, seed_data):
    superadmin = seed_data["superadmin"]
    headers = auth_headers(superadmin, ["SUPER_ADMIN"])

    # Super Admin can list all companies
    res_companies = await client.get("/api/v1/companies", headers=headers)
    assert res_companies.status_code == 200
    slugs = [c["slug"] for c in res_companies.json()]
    assert "alpha-corp" in slugs
    assert "beta-llc" in slugs

    # Super Admin can view system stats
    res_stats = await client.get("/api/v1/admin/stats", headers=headers)
    assert res_stats.status_code == 200
    stats = res_stats.json()
    assert stats["total_companies"] >= 2
    assert stats["total_users"] >= 4
