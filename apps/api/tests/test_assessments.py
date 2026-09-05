"""
Assessments builder and publishing test suite.
"""
import pytest
from httpx import AsyncClient
from tests.conftest import auth_headers


@pytest.mark.asyncio
async def test_create_assessment_and_attach_questions(client: AsyncClient, seed_data):
    admin_a = seed_data["admin_a"]
    company_a = seed_data["company_a"]
    headers = auth_headers(admin_a, ["COMPANY_ADMIN"], company_a.id)

    # 1. Create Question
    bank_res = await client.post(
        "/api/v1/questions/banks",
        json={"name": "Frontend Bank", "category": "Frontend"},
        headers=headers,
    )
    bank_id = bank_res.json()["id"]

    q_res = await client.post(
        f"/api/v1/questions/banks/{bank_id}/questions",
        json={
            "title": "React Reconciliation",
            "content_markdown": "What algorithm does React use for DOM diffing?",
            "question_type": "MCQ_SINGLE",
            "difficulty": "MEDIUM",
            "points": 2.0,
            "options": [
                {"option_text": "Heuristic O(n) Virtual DOM diffing", "is_correct": True},
                {"option_text": "Exhaustive tree comparison O(n^3)", "is_correct": False},
            ],
        },
        headers=headers,
    )
    question_id = q_res.json()["id"]

    # 2. Create Assessment Draft
    ass_payload = {
        "title": "React Senior Frontend Assessment",
        "slug": "react-senior-assessment",
        "description": "Evaluate React lifecycle, hooks, and virtual DOM concepts.",
        "duration_minutes": 25,
        "passing_score_percentage": 70.0,
    }
    ass_res = await client.post("/api/v1/assessments", json=ass_payload, headers=headers)
    assert ass_res.status_code == 201
    ass_data = ass_res.json()
    assert ass_data["status"] == "DRAFT"
    assessment_id = ass_data["id"]

    # 3. Attach question
    attach_res = await client.post(
        f"/api/v1/assessments/{assessment_id}/questions",
        json={"question_ids": [question_id]},
        headers=headers,
    )
    assert attach_res.status_code == 200
    updated_ass = attach_res.json()
    assert updated_ass["total_questions"] == 1
    assert updated_ass["total_points"] == 2.0

    # 4. Publish assessment
    pub_res = await client.post(f"/api/v1/assessments/{assessment_id}/publish", headers=headers)
    assert pub_res.status_code == 200
    assert pub_res.json()["status"] == "PUBLISHED"


@pytest.mark.asyncio
async def test_assessment_templates_lifecycle(client: AsyncClient, seed_data):
    admin_a = seed_data["admin_a"]
    company_a = seed_data["company_a"]
    headers = auth_headers(admin_a, ["COMPANY_ADMIN"], company_a.id)

    # 1. List default templates
    res = await client.get("/api/v1/assessments/templates", headers=headers)
    assert res.status_code == 200
    templates = res.json()
    assert len(templates) >= 6
    template_keys = [t["key"] for t in templates]
    assert "CODING_ONLY" in template_keys
    assert "FULL_CAMPUS" in template_keys
    assert "APTITUDE_REASONING" in template_keys

    # 2. Create assessment from template
    create_res = await client.post(
        "/api/v1/assessments/create-from-template",
        json={
            "template_key": "FULL_CAMPUS",
            "title": "TCS Campus Batch Drive 2026",
            "duration_minutes": 90,
        },
        headers=headers,
    )
    assert create_res.status_code == 201
    created_data = create_res.json()
    assert created_data["title"] == "TCS Campus Batch Drive 2026"
    assert created_data["id"] is not None
    assert len(created_data["sections_config"]["sections"]) == 4

    # 3. Save a custom template for company
    custom_res = await client.post(
        "/api/v1/assessments/templates",
        json={
            "key": "FINANCE_QUANT_TEST",
            "title": "Finance & Quant Specialist Round",
            "category": "Analyst & Quant",
            "description": "Probability, statistics, and financial modeling questions.",
            "icon": "📈",
            "color": "#10b981",
            "duration_minutes": 45,
            "passing_score_percentage": 75.0,
            "allow_section_switching": True,
            "sections": [
                {
                    "id": "sec_prob",
                    "name": "Probability & Statistics",
                    "type": "APTITUDE",
                    "duration_minutes": 25,
                    "question_count": 15,
                    "description": "Probability & Statistics",
                },
                {
                    "id": "sec_modeling",
                    "name": "Financial Modeling Logic",
                    "type": "REASONING",
                    "duration_minutes": 20,
                    "question_count": 10,
                    "description": "Financial Modeling",
                },
            ],
            "features": ["Financial formulas", "Timed sections"],
        },
        headers=headers,
    )
    assert custom_res.status_code == 201
    custom_template = custom_res.json()
    assert custom_template["key"].startswith("custom-")
    assert custom_template["sections_count"] == 2
    template_id = custom_template["id"]

    # 4. Verify custom template shows in templates list
    list_after = await client.get("/api/v1/assessments/templates", headers=headers)
    assert list_after.status_code == 200
    all_titles = [t["title"] for t in list_after.json()]
    assert "Finance & Quant Specialist Round" in all_titles

    # 5. Delete custom template
    del_res = await client.delete(f"/api/v1/assessments/templates/{template_id}", headers=headers)
    assert del_res.status_code == 200


@pytest.mark.asyncio
async def test_ai_copilot_recommend_template(client: AsyncClient, seed_data):
    admin_a = seed_data["admin_a"]
    company_a = seed_data["company_a"]
    headers = auth_headers(admin_a, ["COMPANY_ADMIN"], company_a.id)

    # Check SDE role recommendation -> CODING_ONLY
    sde_res = await client.post(
        "/api/v1/ai/copilot/recommend-template",
        json={"role_title": "Backend SDE II", "seniority": "MID", "target_skills": ["Python", "DSA"]},
        headers=headers,
    )
    assert sde_res.status_code == 200
    assert sde_res.json()["recommended_template_key"] == "CODING_ONLY"

    # Check Campus drive recommendation -> FULL_CAMPUS
    campus_res = await client.post(
        "/api/v1/ai/copilot/recommend-template",
        json={"role_title": "Trainee Engineer Campus Batch", "seniority": "JUNIOR"},
        headers=headers,
    )
    assert campus_res.status_code == 200
    assert campus_res.json()["recommended_template_key"] == "FULL_CAMPUS"

