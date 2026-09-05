"""
AssessIQ Transparent Risk & Integrity Scoring Model.
Calculates explainable score deductions and risk classifications.
Mandate: AI flags and classifies; a human recruiter retains final hiring decision.
"""
from typing import List, Dict, Any, Tuple
from pydantic import BaseModel


# Transparent deduction rules & severity definitions
SIGNAL_RULES: Dict[str, Dict[str, Any]] = {
    "MULTIPLE_FACES": {
        "deduction": 25.0,
        "severity": "CRITICAL",
        "description": "Additional person(s) detected in candidate camera frame.",
    },
    "FACE_ABSENT": {
        "deduction": 15.0,
        "severity": "HIGH",
        "description": "Candidate departed camera frame or face was obscured for >10s.",
    },
    "FULLSCREEN_EXIT": {
        "deduction": 15.0,
        "severity": "MEDIUM",
        "description": "Fullscreen examination mode exited.",
    },
    "TAB_SWITCH": {
        "deduction": 10.0,
        "severity": "MEDIUM",
        "description": "Browser tab switched or window focus departed.",
    },
    "CAMERA_DISCONNECTED": {
        "deduction": 10.0,
        "severity": "HIGH",
        "description": "Webcam video feed was severed or disabled.",
    },
    "AUDIO_SPIKE": {
        "deduction": 5.0,
        "severity": "LOW",
        "description": "Background speech or acoustic amplitude anomaly detected.",
    },
    "PASTE_DETECTED": {
        "deduction": 5.0,
        "severity": "LOW",
        "description": "Unauthorized clipboard paste content inserted.",
    },
    "WINDOW_BLUR": {
        "deduction": 3.0,
        "severity": "LOW",
        "description": "Exam browser window lost foreground focus.",
    },
}


class DeductionDetail(BaseModel):
    event_type: str
    occurrences: int
    points_deducted: float
    severity: str
    description: str


class IntegrityScoreExplanation(BaseModel):
    final_score: float
    risk_level: str  # NORMAL, LOW_RISK, REVIEW_REQUIRED, HIGH_RISK
    total_deductions: float
    deductions_breakdown: List[DeductionDetail]
    is_flagged: bool
    requires_human_review: bool
    summary: str


def compute_explainable_integrity_score(event_counts: Dict[str, int], proctoring_mode: str = "STANDARD") -> IntegrityScoreExplanation:
    """
    Computes a transparent integrity score (0-100) based on accumulated anomaly events.
    Applies different rules if LOW_FRICTION mode is enabled.
    """
    initial_score = 100.0
    total_deductions = 0.0
    breakdown: List[DeductionDetail] = []

    # Events ignored in LOW_FRICTION mode
    ignored_in_low_friction = {"MULTIPLE_FACES", "FACE_ABSENT", "CAMERA_DISCONNECTED", "AUDIO_SPIKE"}

    for event_type, count in event_counts.items():
        if count <= 0:
            continue
            
        if proctoring_mode == "LOW_FRICTION" and event_type.upper() in ignored_in_low_friction:
            continue

        rule = SIGNAL_RULES.get(
            event_type.upper(),
            {"deduction": 2.0, "severity": "LOW", "description": "Unclassified security anomaly."}
        )
        deduction = rule["deduction"] * count
        total_deductions += deduction

        breakdown.append(
            DeductionDetail(
                event_type=event_type.upper(),
                occurrences=count,
                points_deducted=deduction,
                severity=rule["severity"],
                description=rule["description"],
            )
        )

    final_score = max(0.0, initial_score - total_deductions)

    # Classify Risk Level
    if final_score >= 90.0:
        risk_level = "NORMAL"
        is_flagged = False
        requires_review = False
    elif final_score >= 75.0:
        risk_level = "LOW_RISK"
        is_flagged = False
        requires_review = False
    elif final_score >= 55.0:
        risk_level = "REVIEW_REQUIRED"
        is_flagged = True
        requires_review = True
    else:
        risk_level = "HIGH_RISK"
        is_flagged = True
        requires_review = True

    # Critical override: Any MULTIPLE_FACES or >2 FACE_ABSENT events trigger review required
    if proctoring_mode != "LOW_FRICTION":
        if event_counts.get("MULTIPLE_FACES", 0) > 0 or event_counts.get("FACE_ABSENT", 0) >= 2:
            if risk_level in ["NORMAL", "LOW_RISK"]:
                risk_level = "REVIEW_REQUIRED"
                is_flagged = True
                requires_review = True

    summary = (
        f"Integrity Score: {final_score:.1f}/100 ({risk_level.replace('_', ' ')}). "
        f"{len(breakdown)} anomaly categories detected resulting in -{total_deductions:.1f} point deductions. "
        f"{'Human review recommended before shortlisting.' if requires_review else 'Session verified clean with minimal irregularities.'}"
    )

    return IntegrityScoreExplanation(
        final_score=round(final_score, 1),
        risk_level=risk_level,
        total_deductions=round(total_deductions, 1),
        deductions_breakdown=breakdown,
        is_flagged=is_flagged,
        requires_human_review=requires_review,
        summary=summary,
    )
