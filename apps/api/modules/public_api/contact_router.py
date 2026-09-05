"""
Enterprise Contact & Demo Requests Router.
Allows prospective enterprise companies, recruiters, and candidates to submit inquiries,
schedule product walkthroughs, and request custom volume pricing.
"""
from datetime import datetime, timezone
import uuid
from typing import Optional
from pydantic import BaseModel, EmailStr, Field

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from core.audit import write_audit_log

router = APIRouter()


class ContactInquiryRequest(BaseModel):
    name: str = Field(min_length=2, max_length=150)
    work_email: EmailStr
    company_name: str = Field(min_length=2, max_length=255)
    company_size: Optional[str] = Field("10-50", max_length=50)
    inquiry_type: str = Field("enterprise_demo", description="enterprise_demo | sales_pricing | ats_integration | custom_bank | support")
    message: str = Field(min_length=5, max_length=2000)
    phone: Optional[str] = Field(None, max_length=30)


class ContactInquiryResponse(BaseModel):
    ticket_id: str
    status: str
    message: str
    received_at: str


@router.post("", response_model=ContactInquiryResponse, status_code=status.HTTP_201_CREATED)
async def submit_contact_inquiry(
    payload: ContactInquiryRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Public endpoint for enterprise companies to request demos, contact sales,
    or reach customer support.
    """
    ticket_id = f"INQ-{uuid.uuid4().hex[:8].upper()}"
    now_iso = datetime.now(timezone.utc).isoformat()

    # Log to security & system audit log
    await write_audit_log(
        db,
        user_id=None,
        company_id=None,
        action="inquiry.submitted",
        resource_type="contact_inquiry",
        resource_id=ticket_id,
        metadata={
            "ticket_id": ticket_id,
            "name": payload.name,
            "work_email": payload.work_email,
            "company_name": payload.company_name,
            "company_size": payload.company_size,
            "inquiry_type": payload.inquiry_type,
            "message_preview": payload.message[:100],
        },
    )

    return ContactInquiryResponse(
        ticket_id=ticket_id,
        status="received",
        message="Thank you! An AssessIQ enterprise solutions specialist will reach out within 2 business hours.",
        received_at=now_iso,
    )
