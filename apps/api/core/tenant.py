"""
Multi-tenant enforcement utilities.
Every database query for company-scoped data MUST go through these helpers.
"""
import uuid
from typing import TypeVar, Type

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.exceptions import ForbiddenError, NotFoundError

T = TypeVar("T")


def apply_company_filter(query, model, company_id: uuid.UUID):
    """
    Apply a company_id WHERE clause to any SQLAlchemy query.
    Use this for every query on company-scoped models.
    """
    return query.where(model.company_id == company_id)


async def get_company_resource_or_404(
    db: AsyncSession,
    model: Type[T],
    resource_id: uuid.UUID,
    company_id: uuid.UUID,
) -> T:
    """
    Fetch a resource by ID, enforcing company ownership.
    Returns 404 (not 403) to avoid revealing existence of cross-company resources.
    """
    stmt = select(model).where(
        model.id == resource_id,
        model.company_id == company_id,
        model.deleted_at.is_(None),
    )
    result = await db.execute(stmt)
    obj = result.scalar_one_or_none()
    if obj is None:
        raise NotFoundError(model.__name__)
    return obj
