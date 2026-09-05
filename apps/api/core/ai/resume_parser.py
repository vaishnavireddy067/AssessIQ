"""
AssessIQ Resume Intelligence Engine.
Extracts skills, experience, and recommends matching assessment paths.
Advisory Only: Never auto-rejects or auto-assigns candidates.
"""
import re
from typing import List, Dict, Any
from pydantic import BaseModel


KNOWN_TECH_SKILLS = [
    "python", "javascript", "typescript", "react", "node.js", "docker", "kubernetes",
    "postgresql", "mongodb", "redis", "fastapi", "django", "flask", "aws", "gcp",
    "azure", "sql", "git", "ci/cd", "rest api", "graphql", "microservices", "kafka",
    "c++", "java", "go", "rust", "linux", "html5", "css3", "tailwind", "next.js",
]


class ResumeParseResult(BaseModel):
    candidate_name: str
    candidate_email: str
    extracted_skills: List[str]
    years_experience: float
    education_level: str
    domain_tags: List[str]
    recommended_assessments: List[Dict[str, Any]]
    advisory_summary: str
    is_advisory_only: bool = True


def parse_resume_text(
    resume_text: str,
    available_assessments: List[Dict[str, Any]] = None,
) -> ResumeParseResult:
    """
    Parses unstructured resume text to extract skills and recommend test modules.
    Advisory only.
    """
    text_lower = resume_text.lower()

    # 1. Extract candidate email
    email_match = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", resume_text)
    candidate_email = email_match.group(0) if email_match else "candidate@example.com"

    # 2. Extract name
    lines = [l.strip() for l in resume_text.strip().split("\n") if l.strip()]
    candidate_name = lines[0] if lines else "Candidate"
    # Clean non-name characters if first line has email/phone
    if "@" in candidate_name or len(candidate_name) > 50:
        candidate_name = "Candidate"

    # 3. Extract technical skills
    extracted = []
    for skill in KNOWN_TECH_SKILLS:
        # Match whole word
        pattern = r"\b" + re.escape(skill) + r"\b"
        if re.search(pattern, text_lower):
            extracted.append(skill.title() if len(skill) > 3 else skill.upper())

    # 4. Extract experience estimation
    years = 2.0  # default baseline
    exp_matches = re.findall(r"(\d+)\+?\s*(?:years?|yrs?)(?:\s+of)?\s+(?:experience|exp)", text_lower)
    if exp_matches:
        try:
            years = float(exp_matches[0])
        except ValueError:
            pass

    # 5. Extract education
    education = "Bachelor's Degree"
    if "phd" in text_lower or "doctorate" in text_lower:
        education = "Ph.D."
    elif "master" in text_lower or "ms " in text_lower or "m.tech" in text_lower:
        education = "Master's Degree"
    elif "bachelor" in text_lower or "b.tech" in text_lower or "bs " in text_lower:
        education = "Bachelor's Degree"

    # 6. Determine domain tags
    domain_tags = []
    if any(s in text_lower for s in ["react", "vue", "frontend", "css", "html", "javascript"]):
        domain_tags.append("Frontend")
    if any(s in text_lower for s in ["python", "fastapi", "django", "node", "backend", "microservices"]):
        domain_tags.append("Backend")
    if any(s in text_lower for s in ["sql", "postgresql", "database", "redis"]):
        domain_tags.append("Databases")
    if any(s in text_lower for s in ["docker", "kubernetes", "aws", "devops", "ci/cd"]):
        domain_tags.append("Cloud & DevOps")

    # 7. Recommend matching assessments (from available list or generic presets)
    recommended = []
    if available_assessments:
        for ass in available_assessments:
            title = ass.get("title", "").lower()
            if any(skill.lower() in title for skill in extracted) or any(tag.lower() in title for tag in domain_tags):
                recommended.append({
                    "assessment_id": ass.get("id"),
                    "title": ass.get("title"),
                    "match_reason": f"Matches extracted competencies in {', '.join(extracted[:3])}",
                })

    if not recommended:
        # Fallback advisory recommendations
        if "Backend" in domain_tags:
            recommended.append({
                "assessment_id": None,
                "title": "Backend Engineering & API Mastery Assessment",
                "match_reason": "Recommended based on strong backend skill density (FastAPI/Python/Node).",
            })
        if "Cloud & DevOps" in domain_tags:
            recommended.append({
                "assessment_id": None,
                "title": "Docker, Kubernetes & Infrastructure Assessment",
                "match_reason": "Matches infrastructure and containerization experience.",
            })
        if not recommended:
            recommended.append({
                "assessment_id": None,
                "title": "Full-Stack Software Engineer Assessment",
                "match_reason": "Broad technical competencies detected across core web fundamentals.",
            })

    advisory_summary = (
        f"Candidate {candidate_name} exhibits approximately {years:.1f} years of experience with core proficiency "
        f"in {', '.join(extracted[:4]) if extracted else 'software engineering'}. "
        f"Advisory Recommendation: Assign recommended assessment modules for structured verification. "
        f"(Note: This AI analysis is purely consultative and does not make automated employment decisions.)"
    )

    return ResumeParseResult(
        candidate_name=candidate_name,
        candidate_email=candidate_email,
        extracted_skills=extracted,
        years_experience=years,
        education_level=education,
        domain_tags=domain_tags,
        recommended_assessments=recommended,
        advisory_summary=advisory_summary,
        is_advisory_only=True,
    )
