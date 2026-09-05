"""
Coding Problems & Sandboxed Execution router.
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
from core.sandbox.code_runner import (
    CodeLanguage, run_code_against_test_cases, execute_single_run, 
    CodeExecutionSummary, normalize_output
)
from dependencies import get_current_user, require_roles, CurrentUser
from modules.assessments.models import DifficultyLevel
from modules.coding.models import CodingProblem, CodingTestCase

router = APIRouter()


# ── Schemas ───────────────────────────────────────────────────────────────────
class TestCaseCreate(BaseModel):
    input_data: str
    expected_output: str
    is_hidden: bool = False
    order_index: int = 0
    explanation: Optional[str] = None


class TestCaseResponse(BaseModel):
    id: uuid.UUID
    input_data: str
    expected_output: str
    is_hidden: bool
    order_index: int
    explanation: Optional[str] = None

    class Config:
        from_attributes = True


class CodingProblemCreate(BaseModel):
    title: str = Field(min_length=3, max_length=255)
    slug: str = Field(min_length=2, max_length=100)
    description_markdown: str = Field(min_length=10)
    difficulty: DifficultyLevel = DifficultyLevel.MEDIUM
    time_limit_ms: int = Field(default=2000, ge=500, le=10000)
    memory_limit_mb: int = Field(default=256, ge=64, le=1024)
    starter_code: Dict[str, str] = Field(default_factory=lambda: {
        "python": "def solution():\n    # Write your solution here\n    pass\n",
        "javascript": "function solution() {\n    // Write your solution here\n}\n"
    })
    solution_code: Optional[Dict[str, str]] = None
    points: float = Field(default=10.0, ge=1.0)
    tags: Optional[List[str]] = []
    test_cases: List[TestCaseCreate] = []


class CodingProblemResponse(BaseModel):
    id: uuid.UUID
    company_id: Optional[uuid.UUID] = None
    title: str
    slug: str
    description_markdown: str
    difficulty: DifficultyLevel
    time_limit_ms: int
    memory_limit_mb: int
    starter_code: Dict[str, str]
    points: float
    tags: Optional[List[str]] = []
    test_cases: List[TestCaseResponse] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RunCodeRequest(BaseModel):
    language: CodeLanguage = CodeLanguage.PYTHON
    code: str
    custom_input: Optional[str] = None
    problem_id: Optional[uuid.UUID] = None


class RunCodeResponse(BaseModel):
    status: str
    stdout: str
    stderr: str
    execution_time_ms: float
    passed_all: Optional[bool] = None
    test_case_results: Optional[List[Dict[str, Any]]] = None


# ── Routes ────────────────────────────────────────────────────────────────────
@router.get("/problems", response_model=List[CodingProblemResponse])
async def list_coding_problems(
    current_user: CurrentUser = Depends(require_roles(RoleName.SUPER_ADMIN, RoleName.COMPANY_ADMIN, RoleName.QUESTION_MANAGER)),
    db: AsyncSession = Depends(get_db),
):
    """List all coding challenges accessible in the tenant."""
    stmt = select(CodingProblem).where(CodingProblem.deleted_at.is_(None))
    if not current_user.is_super_admin():
        stmt = stmt.where(
            (CodingProblem.company_id == current_user.company_id) | (CodingProblem.company_id.is_(None))
        )
    stmt = stmt.order_by(CodingProblem.created_at.desc())
    problems = (await db.execute(stmt)).scalars().all()

    response = []
    for p in problems:
        tc_stmt = select(CodingTestCase).where(CodingTestCase.problem_id == p.id).order_by(CodingTestCase.order_index.asc())
        tcs = (await db.execute(tc_stmt)).scalars().all()

        # If user is candidate, hide is_hidden test cases
        is_candidate = current_user.has_role(RoleName.CANDIDATE) and not current_user.has_role(RoleName.COMPANY_ADMIN, RoleName.RECRUITER)
        filtered_tcs = [tc for tc in tcs if not (is_candidate and tc.is_hidden)]

        response.append(
            CodingProblemResponse(
                id=p.id,
                company_id=p.company_id,
                title=p.title,
                slug=p.slug,
                description_markdown=p.description_markdown,
                difficulty=p.difficulty,
                time_limit_ms=p.time_limit_ms,
                memory_limit_mb=p.memory_limit_mb,
                starter_code=p.starter_code,
                points=p.points,
                tags=p.tags or [],
                test_cases=[TestCaseResponse.from_orm(tc) for tc in filtered_tcs],
                created_at=p.created_at,
                updated_at=p.updated_at,
            )
        )
    return response


@router.post("/problems", response_model=CodingProblemResponse, status_code=status.HTTP_201_CREATED)
async def create_coding_problem(
    payload: CodingProblemCreate,
    current_user: CurrentUser = Depends(
        require_roles(RoleName.SUPER_ADMIN, RoleName.COMPANY_ADMIN, RoleName.QUESTION_MANAGER)
    ),
    db: AsyncSession = Depends(get_db),
):
    """Author a new coding challenge with starter templates and test cases."""
    problem = CodingProblem(
        company_id=current_user.company_id,
        title=payload.title,
        slug=payload.slug.lower().strip(),
        description_markdown=payload.description_markdown,
        difficulty=payload.difficulty,
        time_limit_ms=payload.time_limit_ms,
        memory_limit_mb=payload.memory_limit_mb,
        starter_code=payload.starter_code,
        solution_code=payload.solution_code,
        points=payload.points,
        tags=payload.tags or [],
    )
    db.add(problem)
    await db.flush()

    for idx, tc in enumerate(payload.test_cases):
        db.add(
            CodingTestCase(
                problem_id=problem.id,
                input_data=tc.input_data,
                expected_output=tc.expected_output,
                is_hidden=tc.is_hidden,
                order_index=tc.order_index or idx,
                explanation=tc.explanation,
            )
        )
    await db.flush()

    await write_audit_log(
        db,
        user_id=current_user.id,
        company_id=current_user.company_id,
        action="coding_problem.created",
        resource_type="coding_problem",
        resource_id=str(problem.id),
        metadata={"title": problem.title, "slug": problem.slug},
    )

    tc_stmt = select(CodingTestCase).where(CodingTestCase.problem_id == problem.id).order_by(CodingTestCase.order_index.asc())
    tcs = (await db.execute(tc_stmt)).scalars().all()

    return CodingProblemResponse(
        id=problem.id,
        company_id=problem.company_id,
        title=problem.title,
        slug=problem.slug,
        description_markdown=problem.description_markdown,
        difficulty=problem.difficulty,
        time_limit_ms=problem.time_limit_ms,
        memory_limit_mb=problem.memory_limit_mb,
        starter_code=problem.starter_code,
        points=problem.points,
        tags=problem.tags or [],
        test_cases=[TestCaseResponse.from_orm(tc) for tc in tcs],
        created_at=problem.created_at,
        updated_at=problem.updated_at,
    )


@router.post("/run", response_model=RunCodeResponse)
async def run_code_sandbox(
    payload: RunCodeRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Execute code in sandbox:
    1. If custom_input is provided, runs a single execution with stdin.
    2. If problem_id is provided, runs against sample (non-hidden) test cases.
    """
    if payload.problem_id:
        stmt = select(CodingProblem).where(CodingProblem.id == payload.problem_id)
        problem = (await db.execute(stmt)).scalar_one_or_none()
        if not problem:
            raise NotFoundError("CodingProblem")

        # Load visible sample test cases only
        tc_stmt = select(CodingTestCase).where(
            CodingTestCase.problem_id == payload.problem_id,
            CodingTestCase.is_hidden.is_(False),
        ).order_by(CodingTestCase.order_index.asc())
        tcs = (await db.execute(tc_stmt)).scalars().all()

        tc_dicts = [
            {
                "id": str(tc.id),
                "input_data": tc.input_data,
                "expected_output": tc.expected_output,
                "is_hidden": False,
            }
            for tc in tcs
        ]

        summary: CodeExecutionSummary = await run_code_against_test_cases(
            language=payload.language,
            code=payload.code,
            test_cases=tc_dicts,
            time_limit_ms=problem.time_limit_ms,
        )

        return RunCodeResponse(
            status=summary.status.value,
            stdout="",
            stderr=summary.error_message or "",
            execution_time_ms=summary.execution_time_ms,
            passed_all=(summary.passed_test_cases == summary.total_test_cases),
            test_case_results=[r.dict() for r in summary.test_case_results],
        )

    # Single custom input run
    retcode, stdout, stderr, elapsed_ms = await execute_single_run(
        language=payload.language,
        code=payload.code,
        input_data=payload.custom_input or "",
        time_limit_ms=2000,
    )

    return RunCodeResponse(
        status="SUCCESS" if retcode == 0 else ("TIMED_OUT" if retcode == -1 else "ERROR"),
        stdout=stdout,
        stderr=stderr,
        execution_time_ms=elapsed_ms,
    )


@router.post("/problems/{problem_id}/submit")
async def submit_and_grade_problem(
    problem_id: uuid.UUID,
    payload: RunCodeRequest,
    db: AsyncSession = Depends(get_db),
):
    """Evaluate code solution against ALL test cases (including hidden benchmark test cases)."""
    stmt = select(CodingProblem).where(CodingProblem.id == problem_id)
    problem = (await db.execute(stmt)).scalar_one_or_none()
    if not problem:
        raise NotFoundError("CodingProblem")

    tc_stmt = select(CodingTestCase).where(CodingTestCase.problem_id == problem_id).order_by(CodingTestCase.order_index.asc())
    tcs = (await db.execute(tc_stmt)).scalars().all()

    tc_dicts = [
        {
            "id": str(tc.id),
            "input_data": tc.input_data,
            "expected_output": tc.expected_output,
            "is_hidden": tc.is_hidden,
        }
        for tc in tcs
    ]

    summary = await run_code_against_test_cases(
        language=payload.language,
        code=payload.code,
        test_cases=tc_dicts,
        time_limit_ms=problem.time_limit_ms,
    )

    score_awarded = (summary.passed_test_cases / summary.total_test_cases * problem.points) if summary.total_test_cases > 0 else 0.0

    return {
        "status": summary.status.value,
        "total_test_cases": summary.total_test_cases,
        "passed_test_cases": summary.passed_test_cases,
        "execution_time_ms": summary.execution_time_ms,
        "score_awarded": round(score_awarded, 2),
        "max_score": problem.points,
        "passed": summary.status.value == "ACCEPTED",
    }
