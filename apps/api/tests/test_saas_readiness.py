import pytest
from core.billing.plans import get_plan, PlanTier
from core.notifications.provider import notification_provider, ConsoleEmailProvider, dispatch_candidate_invitation_email
from core.reports.exporter import generate_candidate_csv_report, generate_assessment_summary_csv

@pytest.mark.asyncio
async def test_subscription_plans():
    # Test plan resolution
    starter = get_plan("STARTER")
    assert starter.name == "Starter Tier"
    assert starter.monthly_candidate_limit == 50
    assert not starter.allow_ai_copilot

    enterprise = get_plan(PlanTier.ENTERPRISE)
    assert enterprise.name == "Enterprise Cloud"
    assert enterprise.monthly_candidate_limit == 10000
    assert enterprise.allow_ai_copilot

    # Fallback default
    invalid = get_plan("NON_EXISTENT")
    assert invalid.name == "Starter Tier"


@pytest.mark.asyncio
async def test_console_notification_dispatch():
    # Clear previous mock emails
    if isinstance(notification_provider, ConsoleEmailProvider):
        notification_provider.sent_emails.clear()

    # Dispatch test invite
    success = await dispatch_candidate_invitation_email(
        candidate_email="test@example.com",
        candidate_name="Alice",
        assessment_title="Senior Python Backend",
        exam_link="http://localhost:5173/exam/123",
        duration_minutes=60,
    )
    assert success is True

    if isinstance(notification_provider, ConsoleEmailProvider):
        assert len(notification_provider.sent_emails) == 1
        email = notification_provider.sent_emails[0]
        assert email.recipient_email == "test@example.com"
        assert "Senior Python Backend" in email.subject
        assert email.template_name == "candidate_invitation"
        assert email.context["exam_link"] == "http://localhost:5173/exam/123"


def test_csv_report_generation():
    scorecard_data = {
        "candidate_email": "jane@example.com",
        "assessment_title": "React Engineer",
        "total_score": 85,
        "max_score": 100,
        "percentage": 85.0,
        "passed": True,
        "questions": [
            {
                "title": "What is JSX?",
                "score_awarded": 10,
                "points": 10,
                "is_correct": True,
                "selected_option_ids": ["uuid-1"],
            }
        ],
    }

    csv_content = generate_candidate_csv_report(scorecard_data)
    
    assert "jane@example.com" in csv_content
    assert "React Engineer" in csv_content
    assert "PASSED" in csv_content
    assert "What is JSX?" in csv_content

def test_assessment_cohort_csv_generation():
    attempts = [
        {"candidate_email": "bob@example.com", "total_score": 40, "max_score": 100, "percentage": 40, "passed": False, "submitted_at": "2024-01-01T12:00:00Z"},
        {"candidate_email": "alice@example.com", "total_score": 95, "max_score": 100, "percentage": 95, "passed": True, "submitted_at": "2024-01-01T12:30:00Z"}
    ]
    csv_content = generate_assessment_summary_csv("Backend Cohort", attempts)

    assert "Backend Cohort" in csv_content
    assert "bob@example.com" in csv_content
    assert "FAILED" in csv_content
    assert "alice@example.com" in csv_content
    assert "PASSED" in csv_content
