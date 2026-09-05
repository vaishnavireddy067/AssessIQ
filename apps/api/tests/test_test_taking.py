"""
Candidate Test-Taking, Anti-Leak Sanitization & Auto-Grading Test Suite.
"""
import pytest
from httpx import AsyncClient
from tests.conftest import auth_headers


@pytest.mark.asyncio
async def test_full_exam_lifecycle_and_auto_grading(client: AsyncClient, seed_data):
    admin_a = seed_data["admin_a"]
    company_a = seed_data["company_a"]
    headers = auth_headers(admin_a, ["COMPANY_ADMIN"], company_a.id)

    # 1. Create Question Bank & 2 Questions
    bank_res = await client.post(
        "/api/v1/questions/banks",
        json={"name": "Core CS", "category": "CS"},
        headers=headers,
    )
    bank_id = bank_res.json()["id"]

    # Q1 (Worth 2.0 pts)
    q1_res = await client.post(
        f"/api/v1/questions/banks/{bank_id}/questions",
        json={
            "title": "Stack Principle",
            "content_markdown": "What data structure follows LIFO?",
            "points": 2.0,
            "options": [
                {"option_text": "Stack", "is_correct": True},
                {"option_text": "Queue", "is_correct": False},
            ],
        },
        headers=headers,
    )
    q1 = q1_res.json()
    q1_id = q1["id"]
    q1_correct_opt_id = [o["id"] for o in q1["options"] if o["is_correct"]][0]

    # Q2 (Worth 3.0 pts)
    q2_res = await client.post(
        f"/api/v1/questions/banks/{bank_id}/questions",
        json={
            "title": "Queue Principle",
            "content_markdown": "What data structure follows FIFO?",
            "points": 3.0,
            "options": [
                {"option_text": "Queue", "is_correct": True},
                {"option_text": "Stack", "is_correct": False},
            ],
        },
        headers=headers,
    )
    q2 = q2_res.json()
    q2_id = q2["id"]
    q2_wrong_opt_id = [o["id"] for o in q2["options"] if not o["is_correct"]][0]

    # 2. Create Assessment & Attach Questions
    ass_res = await client.post(
        "/api/v1/assessments",
        json={"title": "Data Structures Quick Exam", "slug": "ds-quick-exam", "duration_minutes": 15, "passing_score_percentage": 50.0},
        headers=headers,
    )
    assessment_id = ass_res.json()["id"]

    await client.post(
        f"/api/v1/assessments/{assessment_id}/questions",
        json={"question_ids": [q1_id, q2_id]},
        headers=headers,
    )
    await client.post(f"/api/v1/assessments/{assessment_id}/publish", headers=headers)

    # 3. Create Candidate Invitation
    invite_res = await client.post(
        f"/api/v1/assessments/{assessment_id}/invitations",
        json={"candidate_email": "candidate_test@example.com", "candidate_name": "Test Candidate"},
        headers=headers,
    )
    assert invite_res.status_code == 201
    invitation = invite_res.json()
    token = invitation["token"]

    # 4. Candidate loads exam metadata (Public / Token Endpoint)
    meta_res = await client.get(f"/api/v1/exam/{token}/meta")
    assert meta_res.status_code == 200
    meta = meta_res.json()
    assert meta["title"] == "Data Structures Quick Exam"
    assert meta["total_questions"] == 2
    assert meta["already_started"] is False

    # 5. Candidate Starts Exam
    start_res = await client.post(f"/api/v1/exam/{token}/start")
    assert start_res.status_code == 200
    session = start_res.json()
    questions = session["questions"]
    assert len(questions) == 2

    # ── CRITICAL SECURITY CHECK: Anti-Leak Verification ────────────────────────
    for q in questions:
        for opt in q["options"]:
            assert "is_correct" not in opt, "SECURITY BREACH: is_correct must NOT be exposed to candidate!"

    # 6. Candidate Answers Q1 correctly and Q2 incorrectly
    await client.post(
        f"/api/v1/exam/{token}/save-answer",
        json={"question_id": q1_id, "selected_option_ids": [q1_correct_opt_id]},
    )
    await client.post(
        f"/api/v1/exam/{token}/save-answer",
        json={"question_id": q2_id, "selected_option_ids": [q2_wrong_opt_id]},
    )

    # 7. Candidate Submits Exam
    submit_res = await client.post(f"/api/v1/exam/{token}/submit")
    assert submit_res.status_code == 200
    result = submit_res.json()
    assert result["status"] == "EVALUATED"
    # Q1 gave 2.0 pts, Q2 gave 0 pts => total = 2.0 / 5.0 (40.0%)
    assert result["total_score"] == 2.0
    assert result["max_score"] == 5.0
    assert result["percentage"] == 40.0
    assert result["passed"] is False  # 40% < 50% pass mark

    # 8. Recruiter Views Results Scorecard
    results_list_res = await client.get(f"/api/v1/assessments/{assessment_id}/results", headers=headers)
    assert results_list_res.status_code == 200
    attempts = results_list_res.json()
    assert len(attempts) == 1
    assert attempts[0]["total_score"] == 2.0

    # Recruiter views detailed scorecard
    attempt_id = attempts[0]["id"]
    scorecard_res = await client.get(f"/api/v1/results/{attempt_id}", headers=headers)
    assert scorecard_res.status_code == 200
    scorecard = scorecard_res.json()
    assert len(scorecard["questions"]) == 2
    q1_scorecard = [item for item in scorecard["questions"] if item["question_id"] == q1_id][0]
    assert q1_scorecard["is_correct"] is True
    assert q1_scorecard["score_awarded"] == 2.0
