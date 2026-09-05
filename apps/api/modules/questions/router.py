"""
Questions router — CRUD for Question Banks, Questions, and Options.
"""
import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from database import get_db
from core.rbac import RoleName
from core.exceptions import NotFoundError, ForbiddenError, BadRequestError
from core.audit import write_audit_log
from dependencies import get_current_user, require_roles, CurrentUser
from modules.assessments.models import QuestionBank, Question, QuestionOption, QuestionType, DifficultyLevel

router = APIRouter()


# ── Schemas ───────────────────────────────────────────────────────────────────
class OptionCreate(BaseModel):
    option_text: str = Field(min_length=1)
    is_correct: bool = False
    order_index: int = 0


class OptionResponse(BaseModel):
    id: uuid.UUID
    option_text: str
    is_correct: bool
    order_index: int

    class Config:
        from_attributes = True


class QuestionCreate(BaseModel):
    title: str = Field(min_length=3, max_length=255)
    content_markdown: str = Field(min_length=5)
    question_type: QuestionType = QuestionType.MCQ_SINGLE
    difficulty: DifficultyLevel = DifficultyLevel.MEDIUM
    points: float = Field(default=1.0, ge=0.5)
    explanation: Optional[str] = None
    tags: Optional[List[str]] = []
    options: List[OptionCreate] = Field(min_length=2)


class QuestionResponse(BaseModel):
    id: uuid.UUID
    bank_id: uuid.UUID
    company_id: Optional[uuid.UUID] = None
    title: str
    content_markdown: str
    question_type: QuestionType
    difficulty: DifficultyLevel
    points: float
    explanation: Optional[str] = None
    tags: Optional[List[str]] = []
    options: List[OptionResponse] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class QuestionBankCreate(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    description: Optional[str] = None
    category: str = Field(default="General", max_length=100)


class QuestionBankResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: Optional[str] = None
    category: str
    company_id: Optional[uuid.UUID] = None
    is_active: bool
    questions_count: Optional[int] = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ── Question Bank Endpoints ───────────────────────────────────────────────────
@router.get("/banks", response_model=List[QuestionBankResponse])
async def list_question_banks(
    current_user: CurrentUser = Depends(
        require_roles(RoleName.SUPER_ADMIN, RoleName.COMPANY_ADMIN, RoleName.RECRUITER, RoleName.QUESTION_MANAGER)
    ),
    db: AsyncSession = Depends(get_db),
):
    """List question banks accessible to the tenant (plus system banks where company_id is NULL)."""
    stmt = select(QuestionBank).where(QuestionBank.deleted_at.is_(None))
    if not current_user.is_super_admin():
        stmt = stmt.where(
            (QuestionBank.company_id == current_user.company_id) | (QuestionBank.company_id.is_(None))
        )
    stmt = stmt.order_by(QuestionBank.created_at.desc())
    result = await db.execute(stmt)
    banks = result.scalars().all()

    response = []
    for b in banks:
        q_count_res = await db.execute(
            select(Question.id).where(Question.bank_id == b.id, Question.deleted_at.is_(None))
        )
        q_count = len(q_count_res.scalars().all())
        response.append(
            QuestionBankResponse(
                id=b.id,
                name=b.name,
                description=b.description,
                category=b.category,
                company_id=b.company_id,
                is_active=b.is_active,
                questions_count=q_count,
                created_at=b.created_at,
                updated_at=b.updated_at,
            )
        )
    return response


@router.post("/banks", response_model=QuestionBankResponse, status_code=status.HTTP_201_CREATED)
async def create_question_bank(
    payload: QuestionBankCreate,
    current_user: CurrentUser = Depends(
        require_roles(RoleName.SUPER_ADMIN, RoleName.COMPANY_ADMIN, RoleName.QUESTION_MANAGER)
    ),
    db: AsyncSession = Depends(get_db),
):
    """Create a new tenant question bank."""
    bank = QuestionBank(
        name=payload.name,
        description=payload.description,
        category=payload.category,
        company_id=current_user.company_id,
        is_active=True,
    )
    db.add(bank)
    await db.flush()

    await write_audit_log(
        db,
        user_id=current_user.id,
        company_id=current_user.company_id,
        action="question_bank.created",
        resource_type="question_bank",
        resource_id=str(bank.id),
        metadata={"name": bank.name},
    )

    return QuestionBankResponse(
        id=bank.id,
        name=bank.name,
        description=bank.description,
        category=bank.category,
        company_id=bank.company_id,
        is_active=bank.is_active,
        questions_count=0,
        created_at=bank.created_at,
        updated_at=bank.updated_at,
    )


@router.get("/banks/{bank_id}", response_model=QuestionBankResponse)
async def get_question_bank(
    bank_id: uuid.UUID,
    current_user: CurrentUser = Depends(
        require_roles(RoleName.SUPER_ADMIN, RoleName.COMPANY_ADMIN, RoleName.RECRUITER, RoleName.QUESTION_MANAGER)
    ),
    db: AsyncSession = Depends(get_db),
):
    """Get single question bank details."""
    stmt = select(QuestionBank).where(QuestionBank.id == bank_id, QuestionBank.deleted_at.is_(None))
    res = await db.execute(stmt)
    bank = res.scalar_one_or_none()
    if not bank:
        raise NotFoundError("QuestionBank")

    if not current_user.is_super_admin() and bank.company_id and bank.company_id != current_user.company_id:
        raise ForbiddenError("Access to this question bank is forbidden")

    q_count_res = await db.execute(
        select(Question.id).where(Question.bank_id == bank.id, Question.deleted_at.is_(None))
    )
    return QuestionBankResponse(
        id=bank.id,
        name=bank.name,
        description=bank.description,
        category=bank.category,
        company_id=bank.company_id,
        is_active=bank.is_active,
        questions_count=len(q_count_res.scalars().all()),
        created_at=bank.created_at,
        updated_at=bank.updated_at,
    )


# ── Question Endpoints ────────────────────────────────────────────────────────
@router.get("/banks/{bank_id}/questions", response_model=List[QuestionResponse])
async def list_questions_in_bank(
    bank_id: uuid.UUID,
    current_user: CurrentUser = Depends(
        require_roles(RoleName.SUPER_ADMIN, RoleName.COMPANY_ADMIN, RoleName.RECRUITER, RoleName.QUESTION_MANAGER)
    ),
    db: AsyncSession = Depends(get_db),
):
    """List all questions with their options inside a question bank."""
    bank_stmt = select(QuestionBank).where(QuestionBank.id == bank_id, QuestionBank.deleted_at.is_(None))
    bank_res = await db.execute(bank_stmt)
    bank = bank_res.scalar_one_or_none()
    if not bank:
        raise NotFoundError("QuestionBank")

    if not current_user.is_super_admin() and bank.company_id and bank.company_id != current_user.company_id:
        raise ForbiddenError("Access to this question bank is forbidden")

    stmt = (
        select(Question)
        .where(Question.bank_id == bank_id, Question.deleted_at.is_(None))
        .order_by(Question.created_at.asc())
    )
    result = await db.execute(stmt)
    questions = result.scalars().all()

    responses = []
    for q in questions:
        opt_stmt = select(QuestionOption).where(QuestionOption.question_id == q.id).order_by(QuestionOption.order_index.asc())
        opts = (await db.execute(opt_stmt)).scalars().all()
        responses.append(
            QuestionResponse(
                id=q.id,
                bank_id=q.bank_id,
                company_id=q.company_id,
                title=q.title,
                content_markdown=q.content_markdown,
                question_type=q.question_type,
                difficulty=q.difficulty,
                points=q.points,
                explanation=q.explanation,
                tags=q.tags or [],
                options=[OptionResponse.from_orm(o) for o in opts],
                created_at=q.created_at,
                updated_at=q.updated_at,
            )
        )
    return responses


@router.post("/banks/{bank_id}/questions", response_model=QuestionResponse, status_code=status.HTTP_201_CREATED)
async def create_question(
    bank_id: uuid.UUID,
    payload: QuestionCreate,
    current_user: CurrentUser = Depends(
        require_roles(RoleName.SUPER_ADMIN, RoleName.COMPANY_ADMIN, RoleName.QUESTION_MANAGER)
    ),
    db: AsyncSession = Depends(get_db),
):
    """Create a new MCQ question and its choices inside a bank."""
    bank_stmt = select(QuestionBank).where(QuestionBank.id == bank_id, QuestionBank.deleted_at.is_(None))
    bank = (await db.execute(bank_stmt)).scalar_one_or_none()
    if not bank:
        raise NotFoundError("QuestionBank")

    # Validate that at least one option is marked correct
    has_correct = any(opt.is_correct for opt in payload.options)
    if not has_correct:
        raise BadRequestError("At least one option must be marked as correct (is_correct=true)")

    question = Question(
        bank_id=bank_id,
        company_id=current_user.company_id,
        title=payload.title,
        content_markdown=payload.content_markdown,
        question_type=payload.question_type,
        difficulty=payload.difficulty,
        points=payload.points,
        explanation=payload.explanation,
        tags=payload.tags or [],
    )
    db.add(question)
    await db.flush()

    for idx, opt in enumerate(payload.options):
        db.add(
            QuestionOption(
                question_id=question.id,
                option_text=opt.option_text,
                is_correct=opt.is_correct,
                order_index=opt.order_index or idx,
            )
        )
    await db.flush()

    await write_audit_log(
        db,
        user_id=current_user.id,
        company_id=current_user.company_id,
        action="question.created",
        resource_type="question",
        resource_id=str(question.id),
        metadata={"title": question.title, "bank_id": str(bank_id)},
    )

    opt_stmt = select(QuestionOption).where(QuestionOption.question_id == question.id).order_by(QuestionOption.order_index.asc())
    opts = (await db.execute(opt_stmt)).scalars().all()

    return QuestionResponse(
        id=question.id,
        bank_id=question.bank_id,
        company_id=question.company_id,
        title=question.title,
        content_markdown=question.content_markdown,
        question_type=question.question_type,
        difficulty=question.difficulty,
        points=question.points,
        explanation=question.explanation,
        tags=question.tags or [],
        options=[OptionResponse.from_orm(o) for o in opts],
        created_at=question.created_at,
        updated_at=question.updated_at,
    )
