import pytest
from core.ai.summarizer import evaluate_candidate_performance
from modules.proctoring.router import EVENT_SCORE_DEDUCTIONS, FLAG_THRESHOLD


def test_ai_candidate_evaluator_high_performer():
    """Verify high scores produce STRONG_HIRE recommendations with positive evaluation metrics."""
    result = evaluate_candidate_performance(
        score_percentage=92.5,
        total_questions=10,
        correct_count=9,
        proctoring_score=95.0,
        coding_results=[{"passed": True}, {"passed": True}],
    )
    assert result.recommendation == "STRONG_HIRE"
    assert result.technical_depth_rating == "SENIOR"
    assert len(result.strengths) >= 2
    assert "92.5" in result.executive_summary
    assert "high exam integrity" in result.integrity_assessment.lower()


def test_ai_candidate_evaluator_proctoring_flag():
    """Verify poor proctoring score marks session as flagged with low integrity."""
    result = evaluate_candidate_performance(
        score_percentage=85.0,
        total_questions=10,
        correct_count=8,
        proctoring_score=45.0,
    )
    # High score degraded due to low integrity
    assert result.recommendation == "BORDERLINE"
    assert "repeated tab switches" in str(result.weaknesses)


def test_ai_candidate_evaluator_reject():
    """Verify failing score produces REJECT recommendation."""
    result = evaluate_candidate_performance(
        score_percentage=35.0,
        total_questions=10,
        correct_count=3,
        proctoring_score=100.0,
    )
    assert result.recommendation == "REJECT"
    assert "below recommended passing threshold" in str(result.weaknesses)


def test_proctoring_event_deduction_math():
    """Verify deduction rules calculate correctly."""
    initial_score = 100.0
    tab_deduction = EVENT_SCORE_DEDUCTIONS.get("TAB_SWITCH", 10.0)
    fullscreen_deduction = EVENT_SCORE_DEDUCTIONS.get("FULLSCREEN_EXIT", 15.0)

    score_after = initial_score - (tab_deduction * 4) - fullscreen_deduction
    # 100 - 40 - 15 = 45.0
    assert score_after == 45.0
    assert score_after < FLAG_THRESHOLD
