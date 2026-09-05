import pytest
import asyncio
from core.ai.copilot import generate_copilot_proposal, CopilotAssessmentRequest, check_duplicate
from core.ai.resume_parser import parse_resume_text
from core.ai.skill_matrix import calculate_candidate_skill_matrix


@pytest.mark.asyncio
async def test_copilot_proposal_generation_gating():
    """Verify generated assessment proposals land strictly in IN_REVIEW state and are unapproved."""
    req = CopilotAssessmentRequest(
        role_title="Backend Cloud Engineer",
        seniority="SENIOR",
        target_skills=["Python", "Docker"],
        duration_minutes=45,
        include_coding=True,
        include_sql=True,
        mcq_count=2,
    )

    proposal = await generate_copilot_proposal(req)
    assert proposal["status"] == "IN_REVIEW"
    assert proposal["total_items"] >= 4  # 2 MCQs + 1 Coding + 1 SQL

    # Every item must have is_approved == False and status == IN_REVIEW
    for item in proposal["proposed_items"]:
        assert item["status"] == "IN_REVIEW"
        assert item["is_approved"] is False
        assert "title" in item
        assert item["type"] in ["MCQ", "CODING", "SQL"]


def test_duplicate_detection():
    """Verify duplicate detection flags similar question titles."""
    existing = [
        "Core Architectural Principles of Docker",
        "SQL Aggregation of Monthly Active Users",
    ]
    warning = check_duplicate("Core Architectural Principles of Docker", existing)
    assert warning is not None
    assert "Potential duplicate" in warning

    no_warning = check_duplicate("Completely Unique Quantum Computing Question", existing)
    assert no_warning is None


def test_resume_parser_advisory_guarantee():
    """Verify resume parser extracts skills and guarantees advisory-only status."""
    resume_text = """
    Jane Doe
    jane.doe@example.com
    5 years of experience in modern full-stack web development.
    Proficient in Python, FastAPI, React, PostgreSQL, Docker, and AWS.
    Built microservices architectures handling production traffic.
    Bachelor's Degree in Computer Science.
    """
    res = parse_resume_text(resume_text)
    assert res.candidate_email == "jane.doe@example.com"
    assert res.years_experience >= 4.0
    assert "Python" in res.extracted_skills
    assert "React" in res.extracted_skills
    assert "Docker" in res.extracted_skills
    assert res.is_advisory_only is True
    assert "Advisory" in res.advisory_summary
    assert len(res.recommended_assessments) >= 1


def test_candidate_skill_matrix_calculation():
    """Verify skill grouping and percentage accuracy."""
    questions = [
        {"tags": ["Python", "Algorithms"], "score_awarded": 3.0, "points": 3.0},
        {"tags": ["Python"], "score_awarded": 1.5, "points": 3.0},
        {"tags": ["SQL", "Databases"], "score_awarded": 5.0, "points": 5.0},
    ]

    matrix = calculate_candidate_skill_matrix("attempt-123", questions)
    assert matrix.attempt_id == "attempt-123"
    skill_map = {s.skill: s for s in matrix.skills}

    # Python: (3.0 + 1.5) / (3.0 + 3.0) = 4.5 / 6.0 = 75.0%
    assert skill_map["Python"].score_percentage == 75.0
    assert skill_map["Python"].proficiency_level == "ADVANCED"

    # SQL: 5.0 / 5.0 = 100.0%
    assert skill_map["Sql"].score_percentage == 100.0
    assert skill_map["Sql"].proficiency_level == "EXPERT"
