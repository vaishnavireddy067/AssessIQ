"""
Authentication and onboarding tests.
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, seed_data):
    response = await client.post(
        "/api/v1/auth/login",
        data={"username": "superadmin@test.com", "password": "SuperSecret123!"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_failure_wrong_password(client: AsyncClient, seed_data):
    response = await client.post(
        "/api/v1/auth/login",
        data={"username": "superadmin@test.com", "password": "WrongPassword!"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_nonexistent_user(client: AsyncClient, seed_data):
    response = await client.post(
        "/api/v1/auth/login",
        data={"username": "nobody@test.com", "password": "SomePassword123!"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_register_company_success(client: AsyncClient, db_session):
    payload = {
        "company_name": "New Venture Inc",
        "company_slug": "new-venture",
        "admin_email": "founder@newventure.com",
        "admin_password": "SecurePassword123!",
        "admin_first_name": "John",
        "admin_last_name": "Doe",
    }
    response = await client.post("/api/v1/auth/register-company", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data


@pytest.mark.asyncio
async def test_register_company_duplicate_slug(client: AsyncClient, seed_data):
    payload = {
        "company_name": "Alpha Duplicate",
        "company_slug": "alpha-corp",  # Already exists in seed_data
        "admin_email": "otheradmin@alpha.com",
        "admin_password": "SecurePassword123!",
    }
    response = await client.post("/api/v1/auth/register-company", json=payload)
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_register_company_duplicate_email(client: AsyncClient, seed_data):
    payload = {
        "company_name": "Brand New Co",
        "company_slug": "brand-new-co",
        "admin_email": "admin@alpha.com",  # Already exists in seed_data
        "admin_password": "SecurePassword123!",
    }
    response = await client.post("/api/v1/auth/register-company", json=payload)
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_register_candidate_success(client: AsyncClient, db_session):
    payload = {
        "email": "newbie_candidate@test.com",
        "password": "Password123!",
        "first_name": "Sam",
        "last_name": "Coder",
    }
    response = await client.post("/api/v1/auth/register-candidate", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data


@pytest.mark.asyncio
async def test_token_refresh_and_rotation(client: AsyncClient, seed_data):
    # 1. Login
    login_res = await client.post(
        "/api/v1/auth/login",
        data={"username": "admin@alpha.com", "password": "AlphaAdmin123!"},
    )
    tokens = login_res.json()
    refresh_token = tokens["refresh_token"]

    # 2. Refresh
    refresh_res = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert refresh_res.status_code == 200
    new_tokens = refresh_res.json()
    assert "access_token" in new_tokens
    assert "refresh_token" in new_tokens
    assert new_tokens["refresh_token"] != refresh_token

    # 3. Re-using the old refresh token must now fail (rotation security)
    retry_old = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert retry_old.status_code == 401
