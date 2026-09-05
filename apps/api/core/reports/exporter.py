"""
AssessIQ Multi-Format Reporting & Export Engine.
Generates CSV and JSON scorecard reports for candidate evaluation archives.
"""
import csv
import io
import json
from typing import List, Dict, Any


def generate_candidate_csv_report(scorecard_data: Dict[str, Any]) -> str:
    """
    Generates a structured CSV report from a candidate scorecard.
    Includes overall outcome, points earned, proctoring score, and question breakdown.
    """
    output = io.StringIO()
    writer = csv.writer(output)

    # 1. Header Metadata
    writer.writerow(["AssessIQ Candidate Evaluation Report"])
    writer.writerow(["Candidate Email", scorecard_data.get("candidate_email", "")])
    writer.writerow(["Assessment Title", scorecard_data.get("assessment_title", "")])
    writer.writerow(["Score", f"{scorecard_data.get('total_score', 0)} / {scorecard_data.get('max_score', 0)} ({scorecard_data.get('percentage', 0)}%)"])
    writer.writerow(["Outcome", "PASSED" if scorecard_data.get("passed") else "FAILED"])
    writer.writerow([])

    # 2. Detailed Questions Table
    writer.writerow(["Question #", "Title", "Points Earned", "Max Points", "Status", "Candidate Pick"])
    for idx, q in enumerate(scorecard_data.get("questions", []), 1):
        writer.writerow([
            idx,
            q.get("title", ""),
            q.get("score_awarded", 0),
            q.get("points", 0),
            "CORRECT" if q.get("is_correct") else "INCORRECT",
            "; ".join([str(opt) for opt in q.get("selected_option_ids", [])]),
        ])

    return output.getvalue()


def generate_assessment_summary_csv(assessment_title: str, attempts: List[Dict[str, Any]]) -> str:
    """
    Generates an assessment-wide batch results CSV export.
    """
    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow(["Assessment Cohort Results", assessment_title])
    writer.writerow(["Candidate Email", "Score", "Max Points", "Percentage", "Outcome", "Submitted At"])

    for att in attempts:
        writer.writerow([
            att.get("candidate_email", ""),
            att.get("total_score", 0),
            att.get("max_score", 0),
            f"{att.get('percentage', 0)}%",
            "PASSED" if att.get("passed") else "FAILED",
            att.get("submitted_at", "In Progress"),
        ])

    return output.getvalue()
