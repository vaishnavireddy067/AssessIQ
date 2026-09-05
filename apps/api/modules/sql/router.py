"""
SQL Problems & Sandbox Query Execution router.
"""
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database import get_db
from core.rbac import RoleName
from core.exceptions import NotFoundError, ForbiddenError, BadRequestError
from core.audit import write_audit_log
from core.sandbox.sql_runner import (
    execute_sqlite_query, verify_sql_solution, SqlVerificationSummary
)
from dependencies import get_current_user, require_roles, CurrentUser
from modules.assessments.models import DifficultyLevel
from modules.coding.models import SqlProblem

router = APIRouter()


# ── Schemas ───────────────────────────────────────────────────────────────────
class SqlProblemCreate(BaseModel):
    title: str = Field(min_length=3, max_length=255)
    slug: str = Field(min_length=2, max_length=100)
    description_markdown: str = Field(min_length=10)
    difficulty: DifficultyLevel = DifficultyLevel.MEDIUM
    schema_sql: str = Field(min_length=10, description="DDL + INSERT statements to build sandbox tables")
    solution_sql: str = Field(min_length=5, description="Reference solution query")
    points: float = Field(default=10.0, ge=1.0)
    tags: Optional[List[str]] = []


class SqlProblemResponse(BaseModel):
    id: uuid.UUID
    company_id: Optional[uuid.UUID] = None
    title: str
    slug: str
    description_markdown: str
    difficulty: DifficultyLevel
    schema_sql: str
    points: float
    tags: Optional[List[str]] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RunSqlQueryRequest(BaseModel):
    problem_id: Optional[uuid.UUID] = None
    schema_sql: Optional[str] = None
    query: str


# ── Routes ────────────────────────────────────────────────────────────────────
@router.get("/problems", response_model=List[SqlProblemResponse])
async def list_sql_problems(
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all SQL challenges accessible in tenant."""
    stmt = select(SqlProblem).where(SqlProblem.deleted_at.is_(None))
    if not current_user.is_super_admin():
        stmt = stmt.where(
            (SqlProblem.company_id == current_user.company_id) | (SqlProblem.company_id.is_(None))
        )
    stmt = stmt.order_by(SqlProblem.created_at.desc())
    problems = (await db.execute(stmt)).scalars().all()
    return problems


@router.post("/problems", response_model=SqlProblemResponse, status_code=status.HTTP_201_CREATED)
async def create_sql_problem(
    payload: SqlProblemCreate,
    current_user: CurrentUser = Depends(
        require_roles(RoleName.SUPER_ADMIN, RoleName.COMPANY_ADMIN, RoleName.QUESTION_MANAGER)
    ),
    db: AsyncSession = Depends(get_db),
):
    """Create a new SQL database query challenge."""
    # Verify solution query runs cleanly on schema
    ok, res, err = execute_sqlite_query(payload.schema_sql, payload.solution_sql)
    if not ok:
        raise BadRequestError(f"Validation failed: Solution query failed against schema: {err}")

    problem = SqlProblem(
        company_id=current_user.company_id,
        title=payload.title,
        slug=payload.slug.lower().strip(),
        description_markdown=payload.description_markdown,
        difficulty=payload.difficulty,
        schema_sql=payload.schema_sql,
        solution_sql=payload.solution_sql,
        points=payload.points,
        tags=payload.tags or [],
    )
    db.add(problem)
    await db.flush()

    await write_audit_log(
        db,
        user_id=current_user.id,
        company_id=current_user.company_id,
        action="sql_problem.created",
        resource_type="sql_problem",
        resource_id=str(problem.id),
        metadata={"title": problem.title, "slug": problem.slug},
    )
    return problem


@router.post("/run")
async def run_sql_sandbox(
    payload: RunSqlQueryRequest,
    db: AsyncSession = Depends(get_db),
):
    """Execute candidate SQL query in sandbox and return tabular result grid."""
    schema = payload.schema_sql
    if not schema and payload.problem_id:
        stmt = select(SqlProblem).where(SqlProblem.id == payload.problem_id)
        problem = (await db.execute(stmt)).scalar_one_or_none()
        if not problem:
            raise NotFoundError("SqlProblem")
        schema = problem.schema_sql

    if not schema:
        raise BadRequestError("Schema SQL or valid problem_id is required")

    ok, result, err = execute_sqlite_query(schema, payload.query)
    return {
        "status": "SUCCESS" if ok else "ERROR",
        "columns": result.columns,
        "rows": result.rows,
        "row_count": result.row_count,
        "execution_time_ms": result.execution_time_ms,
        "error_message": err,
    }


@router.post("/problems/{problem_id}/submit")
async def submit_sql_problem(
    problem_id: uuid.UUID,
    payload: RunSqlQueryRequest,
    db: AsyncSession = Depends(get_db),
):
    """Verify and grade candidate query against reference dataset."""
    stmt = select(SqlProblem).where(SqlProblem.id == problem_id)
    problem = (await db.execute(stmt)).scalar_one_or_none()
    if not problem:
        raise NotFoundError("SqlProblem")

    summary: SqlVerificationSummary = verify_sql_solution(
        schema_sql=problem.schema_sql,
        candidate_query=payload.query,
        solution_query=problem.solution_sql,
    )

    score_awarded = problem.points if summary.passed else 0.0

    return {
        "status": summary.status.value,
        "passed": summary.passed,
        "execution_time_ms": summary.execution_time_ms,
        "score_awarded": score_awarded,
        "max_score": problem.points,
        "candidate_rows": summary.candidate_result.rows,
        "candidate_columns": summary.candidate_result.columns,
        "expected_columns": summary.expected_result.columns if summary.expected_result else [],
        "error_message": summary.error_message,
    }
