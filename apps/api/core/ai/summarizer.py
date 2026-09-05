"""
AssessIQ AI Candidate Performance Evaluator & Summarizer.
Analyzes test results, runtimes, error patterns, and produces recruiter hiring recommendations.
"""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel


class AiCandidateEvaluation(BaseModel):
    recommendation: str  # STRONG_HIRE, HIRE, BORDERLINE, REJECT
    overall_score_percentage: float
    executive_summary: str
    strengths: List[str]
    weaknesses: List[str]
    technical_depth_rating: str  # JUNIOR, MID_LEVEL, SENIOR, PRINCIPAL
    integrity_assessment: str


def evaluate_candidate_performance(
    score_percentage: float,
    total_questions: int,
    correct_count: int,
    proctoring_score: float,
    coding_results: Optional[List[Dict[str, Any]]] = None,
) -> AiCandidateEvaluation:
    """
    Synthesizes candidate test execution data into an executive summary.
    """
    # 1. Determine Recommendation
    if score_percentage >= 85.0 and proctoring_score >= 80.0:
        recommendation = "STRONG_HIRE"
        depth = "SENIOR"
    elif score_percentage >= 70.0 and proctoring_score >= 70.0:
        recommendation = "HIRE"
        depth = "MID_LEVEL"
    elif score_percentage >= 50.0:
        recommendation = "BORDERLINE"
        depth = "JUNIOR"
    else:
        recommendation = "REJECT"
        depth = "JUNIOR"

    # 2. Extract Strengths & Weaknesses
    strengths = []
    weaknesses = []

    if score_percentage >= 70.0:
        strengths.append(f"Strong grasp of core technical principles, scoring {score_percentage}%.")
        strengths.append(f"Successfully answered {correct_count} of {total_questions} questions.")
    else:
        weaknesses.append(f"Scored {score_percentage}%, below recommended passing threshold.")

    if coding_results:
        all_passed = all(c.get("passed", False) for c in coding_results)
        if all_passed:
            strengths.append("High code quality: Passed 100% of algorithmic test cases within memory and time constraints.")
        else:
            weaknesses.append("Encountered edge-case failures or timeouts on algorithmic challenges.")

    if proctoring_score >= 90.0:
        integrity = "Verified high exam integrity with negligible suspicious events."
    elif proctoring_score >= 70.0:
        integrity = "Moderate exam integrity; minor window or tab switches detected."
    else:
        integrity = "Flagged: Multiple tab switches or focus departures detected during exam session."
        weaknesses.append(f"Low integrity trust score ({proctoring_score}/100) due to repeated tab switches.")

    summary = (
        f"Candidate achieved an overall score of {score_percentage}% across {total_questions} evaluation modules. "
        f"Demonstrated {depth.lower().replace('_', ' ')} competency. {integrity}"
    )

    return AiCandidateEvaluation(
        recommendation=recommendation,
        overall_score_percentage=score_percentage,
        executive_summary=summary,
        strengths=strengths or ["Demonstrated basic problem engagement."],
        weaknesses=weaknesses or ["No major conceptual weaknesses identified."],
        technical_depth_rating=depth,
        integrity_assessment=integrity,
    )
