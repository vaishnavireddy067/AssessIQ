"""
AI Question Generation & Challenge synthesis router.
"""
import uuid
from typing import List, Optional
from pydantic import BaseModel, Field

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from core.rbac import RoleName
from core.exceptions import BadRequestError
from core.ai.generator import (
    generate_mcqs, generate_coding_problem, generate_sql_problem,
    GeneratedMCQ, GeneratedCodingProblem, GeneratedSqlProblem
)
from dependencies import get_current_user, require_roles, CurrentUser

router = APIRouter()


class GenerateQuestionsRequest(BaseModel):
    topic: str = Field(min_length=2, max_length=255, description="Skill or topic (e.g. Docker, Python, Kubernetes)")
    count: int = Field(default=3, ge=1, le=10)
    difficulty: str = Field(default="MEDIUM", description="EASY, MEDIUM, HARD")


class GenerateCodingRequest(BaseModel):
    topic: str = Field(min_length=2, max_length=255)
    difficulty: str = Field(default="MEDIUM")


class GenerateSqlRequest(BaseModel):
    topic: str = Field(min_length=2, max_length=255)
    difficulty: str = Field(default="MEDIUM")


@router.post("/generate-questions", response_model=List[GeneratedMCQ])
async def generate_ai_mcqs(
    payload: GenerateQuestionsRequest,
    current_user: CurrentUser = Depends(
        require_roles(RoleName.SUPER_ADMIN, RoleName.COMPANY_ADMIN, RoleName.QUESTION_MANAGER, RoleName.RECRUITER)
    ),
):
    """Generate multiple-choice questions from a topic using AI."""
    questions = await generate_mcqs(
        topic=payload.topic,
        count=payload.count,
        difficulty=payload.difficulty,
    )
    return questions


@router.post("/generate-coding-problem", response_model=GeneratedCodingProblem)
async def generate_ai_coding(
    payload: GenerateCodingRequest,
    current_user: CurrentUser = Depends(
        require_roles(RoleName.SUPER_ADMIN, RoleName.COMPANY_ADMIN, RoleName.QUESTION_MANAGER, RoleName.RECRUITER)
    ),
):
    """Generate an algorithmic coding challenge with starter code and test cases."""
    return await generate_coding_problem(topic=payload.topic, difficulty=payload.difficulty)


@router.post("/generate-sql-problem", response_model=GeneratedSqlProblem)
async def generate_ai_sql(
    payload: GenerateSqlRequest,
    current_user: CurrentUser = Depends(
        require_roles(RoleName.SUPER_ADMIN, RoleName.COMPANY_ADMIN, RoleName.QUESTION_MANAGER, RoleName.RECRUITER)
    ),
):
    """Generate an SQL query problem with schema DDL and reference solution."""
    return await generate_sql_problem(topic=payload.topic, difficulty=payload.difficulty)
