"""
AssessIQ Subscription Plans & Pricing Configurations.
Modeled as declarative config rather than scattered hard-coded checks.
"""
from enum import Enum
from typing import Dict, Any, List
from pydantic import BaseModel


class PlanTier(str, Enum):
    STARTER = "STARTER"
    BUSINESS = "BUSINESS"
    ENTERPRISE = "ENTERPRISE"


class SubscriptionPlan(BaseModel):
    code: str
    name: str
    price_monthly_usd: int
    monthly_candidate_limit: int
    active_assessment_limit: int
    allow_coding_sandbox: bool
    allow_sql_sandbox: bool
    allow_ai_copilot: bool
    allow_advanced_proctoring: bool
    data_retention_days: int
    features: List[str]


# Platform subscription plan catalog
SUBSCRIPTION_PLANS: Dict[str, SubscriptionPlan] = {
    PlanTier.STARTER: SubscriptionPlan(
        code="STARTER",
        name="Starter Tier",
        price_monthly_usd=49,
        monthly_candidate_limit=50,
        active_assessment_limit=5,
        allow_coding_sandbox=True,
        allow_sql_sandbox=True,
        allow_ai_copilot=False,
        allow_advanced_proctoring=False,
        data_retention_days=30,
        features=[
            "Up to 50 candidate tests/month",
            "5 active technical assessments",
            "Standard MCQ, Coding & SQL sandboxes",
            "Browser-level anti-cheat tracking",
            "30-day telemetry retention",
            "Standard email support",
        ],
    ),
    PlanTier.BUSINESS: SubscriptionPlan(
        code="BUSINESS",
        name="Business Scale",
        price_monthly_usd=199,
        monthly_candidate_limit=500,
        active_assessment_limit=50,
        allow_coding_sandbox=True,
        allow_sql_sandbox=True,
        allow_ai_copilot=True,
        allow_advanced_proctoring=True,
        data_retention_days=90,
        features=[
            "Up to 500 candidate tests/month",
            "50 active assessments",
            "AI Assessment Copilot (Question generation)",
            "Resume parsing & skill recommendations",
            "Webcam & sensory AI proctoring",
            "Candidate Skill Competency Matrix",
            "90-day telemetry retention",
            "Priority support",
        ],
    ),
    PlanTier.ENTERPRISE: SubscriptionPlan(
        code="ENTERPRISE",
        name="Enterprise Cloud",
        price_monthly_usd=799,
        monthly_candidate_limit=10000,
        active_assessment_limit=1000,
        allow_coding_sandbox=True,
        allow_sql_sandbox=True,
        allow_ai_copilot=True,
        allow_advanced_proctoring=True,
        data_retention_days=365,
        features=[
            "Unlimited candidate tests & assessments",
            "Dedicated execution sandbox compute",
            "Custom sensory proctoring rules & SLAs",
            "Custom data retention policies (up to 365 days)",
            "Single Sign-On (SSO) & SAML ready",
            "24/7 dedicated enterprise support",
        ],
    ),
}


def get_plan(plan_code: str) -> SubscriptionPlan:
    """Retrieve plan config, defaulting to STARTER."""
    return SUBSCRIPTION_PLANS.get(plan_code.upper(), SUBSCRIPTION_PLANS[PlanTier.STARTER])
