import pytest
from core.proctoring.scoring import compute_explainable_integrity_score, SIGNAL_RULES


def test_explainable_score_clean_session():
    """Verify that a candidate with zero events receives 100% score and NORMAL risk tier."""
    counts = {}
    exp = compute_explainable_integrity_score(counts)
    assert exp.final_score == 100.0
    assert exp.risk_level == "NORMAL"
    assert exp.total_deductions == 0.0
    assert exp.is_flagged is False
    assert exp.requires_human_review is False
    assert len(exp.deductions_breakdown) == 0


def test_explainable_score_sensory_events_deduction():
    """Verify that sensory camera and audio events compute transparent point deductions."""
    counts = {
        "MULTIPLE_FACES": 1,  # -25 pts
        "FACE_ABSENT": 1,     # -15 pts
        "AUDIO_SPIKE": 2,     # -10 pts
    }
    exp = compute_explainable_integrity_score(counts)
    
    # 100 - (25 + 15 + 10) = 50.0
    assert exp.final_score == 50.0
    assert exp.total_deductions == 50.0
    assert exp.risk_level in ["REVIEW_REQUIRED", "HIGH_RISK"]
    assert exp.is_flagged is True
    assert exp.requires_human_review is True

    # Check breakdown explainability
    breakdown_map = {d.event_type: d for d in exp.deductions_breakdown}
    assert breakdown_map["MULTIPLE_FACES"].points_deducted == 25.0
    assert breakdown_map["MULTIPLE_FACES"].severity == "CRITICAL"
    assert breakdown_map["FACE_ABSENT"].points_deducted == 15.0
    assert breakdown_map["AUDIO_SPIKE"].points_deducted == 10.0


def test_critical_override_forces_human_review():
    """Verify that critical signals force human review even if total score remains relatively high."""
    counts = {
        "MULTIPLE_FACES": 1,  # -25 pts -> score 75
    }
    exp = compute_explainable_integrity_score(counts)
    assert exp.final_score == 75.0
    # Overridden to REVIEW_REQUIRED due to multiple faces
    assert exp.risk_level == "REVIEW_REQUIRED"
    assert exp.requires_human_review is True


def test_no_code_path_auto_rejects_candidate():
    """Verify that even a HIGH_RISK score produces a review request rather than an automatic rejection."""
    counts = {
        "MULTIPLE_FACES": 2,  # -50
        "TAB_SWITCH": 5,      # -50
    }
    exp = compute_explainable_integrity_score(counts)
    assert exp.final_score == 0.0
    assert exp.risk_level == "HIGH_RISK"
    assert exp.requires_human_review is True
    # The summary directs human review rather than executing auto-rejection
    assert "Human review" in exp.summary
