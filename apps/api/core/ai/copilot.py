"""
AssessIQ Assessment Copilot Core Engine.
Handles natural-language assessment proposal generation, duplicate checking,
and human-in-the-loop review enforcement.
"""
import uuid
import re
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from core.ai.generator import (
    fallback_mcq_generator,
    generate_coding_problem,
    generate_sql_problem,
    GeneratedMCQ,
    GeneratedCodingProblem,
    GeneratedSqlProblem,
)


class CopilotAssessmentRequest(BaseModel):
    role_title: str = Field(min_length=2, max_length=255, description="Target job title (e.g. Senior Backend Engineer)")
    seniority: str = Field(default="MID", description="JUNIOR, MID, SENIOR, LEAD")
    target_skills: List[str] = Field(min_items=1, description="Key skills: Python, PostgreSQL, Docker, AWS")
    duration_minutes: int = Field(default=60, ge=15, le=180)
    include_coding: bool = Field(default=True)
    include_sql: bool = Field(default=True)
    mcq_count: int = Field(default=5, ge=1, le=15)


def check_duplicate(item_title: str, existing_titles: List[str], threshold: float = 0.8) -> Optional[str]:
    """
    Checks if a generated question title closely duplicates an existing question.
    Uses token-overlap similarity.
    """
    clean_target = set(re.findall(r"\w+", item_title.lower()))
    if not clean_target:
        return None

    for existing in existing_titles:
        clean_exist = set(re.findall(r"\w+", existing.lower()))
        if not clean_exist:
            continue
        intersection = clean_target.intersection(clean_exist)
        similarity = len(intersection) / max(len(clean_target), len(clean_exist))
        if similarity >= threshold:
            return f"Potential duplicate of existing question: '{existing}' (similarity: {similarity:.0%})"

    return None


async def generate_copilot_proposal(
    request: CopilotAssessmentRequest,
    existing_question_titles: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Synthesizes an assessment proposal with a balanced question mix.
    Crucially, ALL generated items land in 'IN_REVIEW' state with human approval gates.
    """
    existing_titles = existing_question_titles or []
    proposed_items: List[Dict[str, Any]] = []

    # 1. Generate MCQs across target skills
    skills = request.target_skills or ["General Engineering"]
    questions_per_skill = max(1, request.mcq_count // len(skills))
    
    diff_mapping = {
        "JUNIOR": "EASY",
        "MID": "MEDIUM",
        "SENIOR": "HARD",
        "LEAD": "HARD",
    }
    difficulty = diff_mapping.get(request.seniority.upper(), "MEDIUM")

    for skill in skills:
        mcqs = fallback_mcq_generator(topic=skill, count=questions_per_skill, difficulty=difficulty)
        for m in mcqs:
            dup_warning = check_duplicate(m.title, existing_titles)
            proposed_items.append({
                "item_id": str(uuid.uuid4()),
                "type": "MCQ",
                "title": m.title,
                "content_markdown": m.content_markdown,
                "difficulty": m.difficulty,
                "points": m.points,
                "explanation": m.explanation,
                "options": [opt.dict() for opt in m.options],
                "tags": m.tags,
                "status": "IN_REVIEW",  # Mandatory review state
                "duplicate_warning": dup_warning,
                "is_approved": False,
            })
            existing_titles.append(m.title)

    # 2. Add Algorithmic Coding Problem if requested
    if request.include_coding:
        primary_skill = skills[0]
        coding_prob = await generate_coding_problem(topic=f"{primary_skill} Algorithms", difficulty=difficulty)
        dup_warning = check_duplicate(coding_prob.title, existing_titles)
        proposed_items.append({
            "item_id": str(uuid.uuid4()),
            "type": "CODING",
            "title": coding_prob.title,
            "slug": coding_prob.slug,
            "description_markdown": coding_prob.description_markdown,
            "difficulty": coding_prob.difficulty,
            "time_limit_ms": coding_prob.time_limit_ms,
            "starter_code": coding_prob.starter_code,
            "test_cases": coding_prob.test_cases,
            "points": coding_prob.points,
            "tags": coding_prob.tags,
            "status": "IN_REVIEW",
            "duplicate_warning": dup_warning,
            "is_approved": False,
        })
        existing_titles.append(coding_prob.title)

    # 3. Add SQL Challenge if requested
    if request.include_sql:
        sql_prob = await generate_sql_problem(topic=f"{request.role_title} Analytics", difficulty=difficulty)
        dup_warning = check_duplicate(sql_prob.title, existing_titles)
        proposed_items.append({
            "item_id": str(uuid.uuid4()),
            "type": "SQL",
            "title": sql_prob.title,
            "slug": sql_prob.slug,
            "description_markdown": sql_prob.description_markdown,
            "difficulty": sql_prob.difficulty,
            "schema_sql": sql_prob.schema_sql,
            "solution_sql": sql_prob.solution_sql,
            "points": sql_prob.points,
            "tags": sql_prob.tags,
            "status": "IN_REVIEW",
            "duplicate_warning": dup_warning,
            "is_approved": False,
        })
        existing_titles.append(sql_prob.title)

    return {
        "role_title": request.role_title,
        "seniority": request.seniority,
        "duration_minutes": request.duration_minutes,
        "target_skills": request.target_skills,
        "total_items": len(proposed_items),
        "status": "IN_REVIEW",
        "proposed_items": proposed_items,
    }


async def generate_candidate_ranking_rationale(
    percentage: float, 
    role_title: str, 
    integrity_score: float = 100.0,
    skill_breakdown: Optional[Dict[str, float]] = None
) -> str:
    """
    Phase 9: Generates a plain-language rationale explaining a candidate's score context.
    (Mocked for local development without actual LLM calls).
    """
    skills_text = ""
    if skill_breakdown:
        # Sort skills by score
        sorted_skills = sorted(skill_breakdown.items(), key=lambda x: x[1], reverse=True)
        top_skills = ", ".join([f"{k} ({v}%)" for k, v in sorted_skills[:2]])
        weak_skills = ", ".join([f"{k} ({v}%)" for k, v in sorted_skills[-2:]])
        if top_skills:
            skills_text = f"demonstrating strong proficiency in {top_skills}"
            if weak_skills and weak_skills != top_skills:
                skills_text += f", with opportunities for improvement in {weak_skills}"
    
    if percentage >= 85:
        tier = "Exceptional"
    elif percentage >= 70:
        tier = "Strong"
    elif percentage >= 50:
        tier = "Borderline"
    else:
        tier = "Below Target"

    rationale = f"{tier} candidate for {role_title} ({percentage}% score) {skills_text}."
    
    if integrity_score < 75.0:
        rationale += f" Note: AI Proctoring flagged session anomalies (Trust Score: {integrity_score}%). Human review strongly recommended."

    return rationale
