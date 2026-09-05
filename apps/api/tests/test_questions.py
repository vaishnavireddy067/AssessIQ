"""
Questions and Question Bank test suite.
"""
import pytest
from httpx import AsyncClient
from tests.conftest import auth_headers


@pytest.mark.asyncio
async def test_create_and_list_question_banks(client: AsyncClient, seed_data):
    admin_a = seed_data["admin_a"]
    company_a = seed_data["company_a"]
    headers = auth_headers(admin_a, ["COMPANY_ADMIN"], company_a.id)

    # 1. Create bank
    payload = {
        "name": "Cloud Infrastructure & DevOps",
        "description": "Kubernetes, Docker, CI/CD pipelines",
        "category": "DevOps",
    }
    res = await client.post("/api/v1/questions/banks", json=payload, headers=headers)
    assert res.status_code == 201
    bank_data = res.json()
    assert bank_data["name"] == "Cloud Infrastructure & DevOps"
    bank_id = bank_data["id"]

    # 2. List banks
    list_res = await client.get("/api/v1/questions/banks", headers=headers)
    assert list_res.status_code == 200
    banks = list_res.json()
    assert any(b["id"] == bank_id for b in banks)


@pytest.mark.asyncio
async def test_create_question_with_options(client: AsyncClient, seed_data):
    admin_a = seed_data["admin_a"]
    company_a = seed_data["company_a"]
    headers = auth_headers(admin_a, ["COMPANY_ADMIN"], company_a.id)

    # Create bank first
    bank_res = await client.post(
        "/api/v1/questions/banks",
        json={"name": "Algorithms & Data Structures", "category": "CS Fundamentals"},
        headers=headers,
    )
    bank_id = bank_res.json()["id"]

    # Create Question with valid options
    q_payload = {
        "title": "Binary Search Time Complexity",
        "content_markdown": "What is the worst-case time complexity of binary search on a sorted array of length n?",
        "question_type": "MCQ_SINGLE",
        "difficulty": "EASY",
        "points": 1.5,
        "explanation": "Binary search divides the search interval in half at each step, giving logarithmic O(log n) time.",
        "tags": ["algorithms", "searching"],
        "options": [
            {"option_text": "O(log n)", "is_correct": True, "order_index": 0},
            {"option_text": "O(n)", "is_correct": False, "order_index": 1},
            {"option_text": "O(n log n)", "is_correct": False, "order_index": 2},
            {"option_text": "O(1)", "is_correct": False, "order_index": 3},
        ],
    }
    q_res = await client.post(f"/api/v1/questions/banks/{bank_id}/questions", json=q_payload, headers=headers)
    assert q_res.status_code == 201
    q_data = q_res.json()
    assert q_data["title"] == "Binary Search Time Complexity"
    assert len(q_data["options"]) == 4


@pytest.mark.asyncio
async def test_create_question_fails_without_correct_option(client: AsyncClient, seed_data):
    admin_a = seed_data["admin_a"]
    company_a = seed_data["company_a"]
    headers = auth_headers(admin_a, ["COMPANY_ADMIN"], company_a.id)

    bank_res = await client.post(
        "/api/v1/questions/banks",
        json={"name": "Test Bank", "category": "Testing"},
        headers=headers,
    )
    bank_id = bank_res.json()["id"]

    invalid_q = {
        "title": "Invalid Question",
        "content_markdown": "No option is marked correct",
        "question_type": "MCQ_SINGLE",
        "difficulty": "EASY",
        "options": [
            {"option_text": "Choice A", "is_correct": False},
            {"option_text": "Choice B", "is_correct": False},
        ],
    }
    res = await client.post(f"/api/v1/questions/banks/{bank_id}/questions", json=invalid_q, headers=headers)
    assert res.status_code == 400
