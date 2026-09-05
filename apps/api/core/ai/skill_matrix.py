"""
AssessIQ Candidate Multi-Skill Competency Matrix.
Computes domain breakdown percentages (e.g. Python 91%, SQL 88%, DSA 76%)
from actual candidate assessment answers and question tags.
"""
from typing import List, Dict, Any
from pydantic import BaseModel


class SkillCompetency(BaseModel):
    skill: str
    score_percentage: float
    questions_attempted: int
    points_earned: float
    total_points_possible: float
    proficiency_level: str  # NOVICE, INTERMEDIATE, ADVANCED, EXPERT


class CandidateSkillMatrix(BaseModel):
    attempt_id: str
    overall_proficiency: str
    skills: List[SkillCompetency]


def calculate_candidate_skill_matrix(
    attempt_id: str,
    evaluated_questions: List[Dict[str, Any]],
) -> CandidateSkillMatrix:
    """
    Groups questions by tags/skills and computes earned vs possible points.
    """
    skill_buckets: Dict[str, Dict[str, float]] = {}

    for q in evaluated_questions:
        tags = q.get("tags") or ["General Knowledge"]
        earned = float(q.get("score_awarded", 0.0))
        possible = max(1.0, float(q.get("points", 1.0)))

        for tag in tags:
            clean_tag = tag.strip().title()
            if clean_tag not in skill_buckets:
                skill_buckets[clean_tag] = {"earned": 0.0, "possible": 0.0, "count": 0}
            skill_buckets[clean_tag]["earned"] += earned
            skill_buckets[clean_tag]["possible"] += possible
            skill_buckets[clean_tag]["count"] += 1

    competencies: List[SkillCompetency] = []
    total_pct_sum = 0.0

    for skill, data in skill_buckets.items():
        pct = round((data["earned"] / data["possible"]) * 100, 1) if data["possible"] > 0 else 0.0
        total_pct_sum += pct

        if pct >= 85.0:
            level = "EXPERT"
        elif pct >= 70.0:
            level = "ADVANCED"
        elif pct >= 50.0:
            level = "INTERMEDIATE"
        else:
            level = "NOVICE"

        competencies.append(
            SkillCompetency(
                skill=skill,
                score_percentage=pct,
                questions_attempted=int(data["count"]),
                points_earned=round(data["earned"], 1),
                total_points_possible=round(data["possible"], 1),
                proficiency_level=level,
            )
        )

    # Sort descending by score
    competencies.sort(key=lambda c: c.score_percentage, reverse=True)

    avg_score = total_pct_sum / len(competencies) if competencies else 0.0
    if avg_score >= 85.0:
        overall = "EXPERT"
    elif avg_score >= 70.0:
        overall = "ADVANCED"
    elif avg_score >= 50.0:
        overall = "INTERMEDIATE"
    else:
        overall = "DEVELOPING"

    return CandidateSkillMatrix(
        attempt_id=attempt_id,
        overall_proficiency=overall,
        skills=competencies,
    )
