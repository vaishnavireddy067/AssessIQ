import pytest
from core.ai.generator import (
    generate_mcqs,
    generate_coding_problem,
    generate_sql_problem,
    fallback_mcq_generator,
)


@pytest.mark.asyncio
async def test_fallback_mcq_generator_structure():
    """Verify fallback MCQ generator produces valid, structured multiple-choice questions."""
    questions = fallback_mcq_generator(topic="Docker", count=2, difficulty="MEDIUM")
    assert len(questions) == 2

    for q in questions:
        assert q.title
        assert "Docker" in q.title or "docker" in q.tags
        assert q.difficulty == "MEDIUM"
        assert len(q.options) >= 2
        # Exactly one correct option
        correct_opts = [opt for opt in q.options if opt.is_correct]
        assert len(correct_opts) == 1
        assert q.explanation


@pytest.mark.asyncio
async def test_generate_mcqs_service():
    """Verify generate_mcqs returns correctly structured questions."""
    questions = await generate_mcqs(topic="PostgreSQL", count=3, difficulty="HARD")
    assert len(questions) <= 3
    assert all(q.difficulty == "HARD" for q in questions)


@pytest.mark.asyncio
async def test_generate_coding_problem():
    """Verify coding challenge generation returns starter code and test cases."""
    problem = await generate_coding_problem(topic="Binary Search Trees", difficulty="HARD")
    assert "challenge" in problem.slug
    assert problem.difficulty == "HARD"
    assert "python" in problem.starter_code
    assert "javascript" in problem.starter_code
    assert len(problem.test_cases) >= 2
    assert any(tc.get("is_hidden") for tc in problem.test_cases)


@pytest.mark.asyncio
async def test_generate_sql_problem():
    """Verify SQL challenge generator includes valid DDL schema and reference solution."""
    sql_prob = await generate_sql_problem(topic="User Session Analytics", difficulty="MEDIUM")
    assert sql_prob.difficulty == "MEDIUM"
    assert "CREATE TABLE" in sql_prob.schema_sql
    assert "SELECT" in sql_prob.solution_sql
    assert "metrics" in sql_prob.schema_sql
