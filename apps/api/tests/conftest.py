"""
Pytest configuration and shared test fixtures for AssessIQ API.
"""
import os
import sys
import uuid
import pytest
from typing import AsyncGenerator
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from database import Base, get_db
from main import app
from core.security import hash_password, create_access_token
from core.rbac import RoleName
from modules.users.models import User
from modules.companies.models import Company, CompanyPlan
from modules.roles.models import Role, UserRole
from modules.candidates.models import Candidate

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = async_sessionmaker(
    bind=test_engine, class_=AsyncSession, expire_on_commit=False
)


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide clean database session per test function."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestingSessionLocal() as session:
        # Seed standard roles
        for r_name in [RoleName.SUPER_ADMIN, RoleName.COMPANY_ADMIN, RoleName.RECRUITER, RoleName.QUESTION_MANAGER, RoleName.CANDIDATE]:
            session.add(Role(name=r_name.value))
        await session.commit()
        yield session

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Provide AsyncClient wired to FastAPI app with overridden DB dependency."""
    async def _get_test_db():
        yield db_session

    app.dependency_overrides[get_db] = _get_test_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def seed_data(db_session: AsyncSession):
    """Seed test fixtures: Super Admin, Company + Company Admin + Recruiter, and Candidate."""
    # 1. Super Admin
    superadmin = User(
        email="superadmin@test.com",
        hashed_password=hash_password("SuperSecret123!"),
        first_name="Super",
        last_name="Admin",
        company_id=None,
        is_active=True,
    )
    db_session.add(superadmin)
    await db_session.flush()

    super_role = (await db_session.execute(
        Role.__table__.select().where(Role.name == RoleName.SUPER_ADMIN.value)
    )).fetchone()
    db_session.add(UserRole(user_id=superadmin.id, role_id=super_role.id, company_id=None))

    # 2. Company A
    company_a = Company(
        name="Alpha Corp",
        slug="alpha-corp",
        plan=CompanyPlan.BUSINESS,
        is_active=True,
    )
    db_session.add(company_a)
    await db_session.flush()

    comp_role = (await db_session.execute(
        Role.__table__.select().where(Role.name == RoleName.COMPANY_ADMIN.value)
    )).fetchone()
    recruiter_role = (await db_session.execute(
        Role.__table__.select().where(Role.name == RoleName.RECRUITER.value)
    )).fetchone()
    candidate_role = (await db_session.execute(
        Role.__table__.select().where(Role.name == RoleName.CANDIDATE.value)
    )).fetchone()

    # Company A Admin
    admin_a = User(
        email="admin@alpha.com",
        hashed_password=hash_password("AlphaAdmin123!"),
        first_name="Alpha",
        last_name="Admin",
        company_id=company_a.id,
        is_active=True,
    )
    db_session.add(admin_a)
    await db_session.flush()
    db_session.add(UserRole(user_id=admin_a.id, role_id=comp_role.id, company_id=company_a.id))

    # Company A Recruiter
    recruiter_a = User(
        email="recruiter@alpha.com",
        hashed_password=hash_password("AlphaRecruiter123!"),
        first_name="Alpha",
        last_name="Recruiter",
        company_id=company_a.id,
        is_active=True,
    )
    db_session.add(recruiter_a)
    await db_session.flush()
    db_session.add(UserRole(user_id=recruiter_a.id, role_id=recruiter_role.id, company_id=company_a.id))

    # 3. Company B
    company_b = Company(
        name="Beta LLC",
        slug="beta-llc",
        plan=CompanyPlan.STARTER,
        is_active=True,
    )
    db_session.add(company_b)
    await db_session.flush()

    admin_b = User(
        email="admin@beta.com",
        hashed_password=hash_password("BetaAdmin123!"),
        first_name="Beta",
        last_name="Admin",
        company_id=company_b.id,
        is_active=True,
    )
    db_session.add(admin_b)
    await db_session.flush()
    db_session.add(UserRole(user_id=admin_b.id, role_id=comp_role.id, company_id=company_b.id))

    # 4. Global Candidate
    candidate = User(
        email="candidate@test.com",
        hashed_password=hash_password("Candidate123!"),
        first_name="Test",
        last_name="Candidate",
        company_id=None,
        is_active=True,
    )
    db_session.add(candidate)
    await db_session.flush()
    db_session.add(UserRole(user_id=candidate.id, role_id=candidate_role.id, company_id=None))
    db_session.add(Candidate(user_id=candidate.id, resume_url="https://example.com/resume.pdf"))

    await db_session.commit()

    return {
        "superadmin": superadmin,
        "company_a": company_a,
        "admin_a": admin_a,
        "recruiter_a": recruiter_a,
        "company_b": company_b,
        "admin_b": admin_b,
        "candidate": candidate,
    }


def auth_headers(user: User, roles: list[str], company_id: uuid.UUID = None) -> dict:
    payload = {"sub": str(user.id), "roles": roles}
    if company_id:
        payload["company_id"] = str(company_id)
    token = create_access_token(payload)
    return {"Authorization": f"Bearer {token}"}
