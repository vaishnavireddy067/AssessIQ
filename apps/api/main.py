"""
AssessIQ — FastAPI Application Entry Point
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse

from config import settings
from database import engine, Base
from core.exceptions import AssessIQException
from modules.auth.router import router as auth_router
from modules.companies.router import router as companies_router
from modules.users.router import router as users_router
from modules.candidates.router import router as candidates_router
from modules.audit.router import router as audit_router
from modules.admin.router import router as admin_router
from modules.questions.router import router as questions_router
from modules.assessments.router import router as assessments_router
from modules.invitations.router import router as invitations_router
from modules.test_taking.router import router as test_taking_router
from modules.results.router import router as results_router
from modules.coding.router import router as coding_router
from modules.sql.router import router as sql_router
from modules.ai.router import router as ai_router
from modules.ai.copilot_router import router as copilot_router
from modules.proctoring.router import router as proctoring_router
from modules.public_api.router import router as public_api_router
from modules.public_api.contact_router import router as contact_router
from modules.analytics.passport_router import router as passport_router
from modules.analytics.fairness_router import router as fairness_router
from modules.analytics.leak_radar_router import router as leak_radar_router
from modules.analytics.panel_review_router import router as panel_review_router
from modules.analytics.outcomes_router import router as outcomes_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup → yield → shutdown."""
    # Startup: ensure tables exist in DB
    from database import Base
    import modules.analytics.models
    import modules.audit.models
    import modules.roles.models
    import modules.companies.models
    import modules.companies.enterprise_models
    import modules.companies.subscription_models
    import modules.users.models
    import modules.candidates.models
    import modules.assessments.models
    import modules.coding.models
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Shutdown
    await engine.dispose()


app = FastAPI(
    title="AssessIQ API",
    description="AI-powered assessment and recruitment platform for B2B hiring.",
    version="0.3.0",
    docs_url="/docs" if settings.APP_ENV != "production" else None,
    redoc_url="/redoc" if settings.APP_ENV != "production" else None,
    openapi_url="/openapi.json" if settings.APP_ENV != "production" else None,
    lifespan=lifespan,
)

# ── Middleware ─────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.APP_ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Global exception handler ───────────────────────────────────────────────────
@app.exception_handler(AssessIQException)
async def assessiq_exception_handler(request, exc: AssessIQException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
            }
        },
    )


# ── Routes ─────────────────────────────────────────────────────────────────────
app.include_router(auth_router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(companies_router, prefix="/api/v1/companies", tags=["Companies"])
app.include_router(users_router, prefix="/api/v1/users", tags=["Users"])
app.include_router(candidates_router, prefix="/api/v1/candidates", tags=["Candidates"])
app.include_router(questions_router, prefix="/api/v1/questions", tags=["Questions & Banks"])
app.include_router(assessments_router, prefix="/api/v1/assessments", tags=["Assessments"])
app.include_router(coding_router, prefix="/api/v1/coding", tags=["Coding Sandbox"])
app.include_router(sql_router, prefix="/api/v1/sql", tags=["SQL Sandbox"])
app.include_router(invitations_router, prefix="/api/v1", tags=["Invitations"])
app.include_router(test_taking_router, prefix="/api/v1/exam", tags=["Exam Runner"])
app.include_router(results_router, prefix="/api/v1", tags=["Results & Scorecards"])
app.include_router(audit_router, prefix="/api/v1/audit", tags=["Audit"])
app.include_router(admin_router, prefix="/api/v1/admin", tags=["Admin"])
app.include_router(ai_router, prefix="/api/v1/ai", tags=["AI Question Generator"])
app.include_router(copilot_router, prefix="/api/v1/ai", tags=["AI Copilot & Resumes"])
app.include_router(proctoring_router, prefix="/api/v1", tags=["Proctoring & Anti-Cheat"])
app.include_router(public_api_router, prefix="/public/v1", tags=["Public API"])
app.include_router(contact_router, prefix="/api/v1/contact", tags=["Contact & Sales Inquiries"])
app.include_router(contact_router, prefix="/api/v1/public/contact", tags=["Contact & Sales Inquiries"])
# Phase 9: Advanced Analytics
app.include_router(passport_router, prefix="/api/v1", tags=["Skill Passport"])
app.include_router(fairness_router, prefix="/api/v1", tags=["Fairness Audit"])
app.include_router(leak_radar_router, prefix="/api/v1", tags=["Leak Radar"])
app.include_router(panel_review_router, prefix="/api/v1", tags=["Panel Review"])
app.include_router(outcomes_router, prefix="/api/v1", tags=["Post-Hire Outcomes"])


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "healthy", "version": "0.1.0"}

@app.get("/healthz", tags=["Health"])
async def liveness_check():
    """Liveness probe – always returns healthy if the process is running."""
    return {"status": "alive"}

@app.get("/readyz", tags=["Health"])
async def readiness_check():
    """Readiness probe – verifies DB connection before reporting ready."""
    try:
        from sqlalchemy import text
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception:
        return {"status": "unavailable"}
    return {"status": "ready"}
