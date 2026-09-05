"""
AssessIQ Pluggable Notification System.
Abstracts email and messaging providers to support SendGrid, SMTP, or Console dev logging.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, EmailStr


class EmailNotification(BaseModel):
    recipient_email: str
    subject: str
    template_name: str
    context: Dict[str, Any]


class EmailProvider(ABC):
    @abstractmethod
    async def send_email(self, notification: EmailNotification) -> bool:
        pass


class ConsoleEmailProvider(EmailProvider):
    """Local development and test email provider."""
    def __init__(self):
        self.sent_emails: List[EmailNotification] = []

    async def send_email(self, notification: EmailNotification) -> bool:
        self.sent_emails.append(notification)
        print(f"[EMAIL NOTIFICATION DISPATCHED]")
        print(f"To: {notification.recipient_email}")
        print(f"Subject: {notification.subject}")
        print(f"Template: {notification.template_name}")
        print(f"Context: {notification.context}")
        print("-" * 50)
        return True


# Global default notification instance
notification_provider: EmailProvider = ConsoleEmailProvider()


async def dispatch_candidate_invitation_email(
    candidate_email: str,
    candidate_name: str,
    assessment_title: str,
    exam_link: str,
    duration_minutes: int,
) -> bool:
    """Dispatches test invitation email with direct exam runner magic link."""
    return await notification_provider.send_email(
        EmailNotification(
            recipient_email=candidate_email,
            subject=f"Invitation: Technical Assessment for {assessment_title}",
            template_name="candidate_invitation",
            context={
                "candidate_name": candidate_name,
                "assessment_title": assessment_title,
                "exam_link": exam_link,
                "duration_minutes": duration_minutes,
            },
        )
    )


async def dispatch_submission_receipt_email(
    candidate_email: str,
    assessment_title: str,
    score_percentage: float,
) -> bool:
    """Dispatches confirmation receipt to candidate upon assessment submission."""
    return await notification_provider.send_email(
        EmailNotification(
            recipient_email=candidate_email,
            subject=f"Receipt: Your Assessment for {assessment_title} has been submitted",
            template_name="submission_receipt",
            context={
                "assessment_title": assessment_title,
                "score_percentage": score_percentage,
            },
        )
    )


async def dispatch_recruiter_high_risk_alert(
    recruiter_email: str,
    candidate_email: str,
    assessment_title: str,
    integrity_score: float,
    attempt_id: str,
) -> bool:
    """Alerts hiring managers when a candidate attempt is flagged as HIGH_RISK."""
    return await notification_provider.send_email(
        EmailNotification(
            recipient_email=recruiter_email,
            subject=f"⚠️ Security Alert: Assessment flagged for review ({candidate_email})",
            template_name="recruiter_risk_alert",
            context={
                "candidate_email": candidate_email,
                "assessment_title": assessment_title,
                "integrity_score": integrity_score,
                "scorecard_link": f"/assessments/results?attempt_id={attempt_id}",
            },
        )
    )
