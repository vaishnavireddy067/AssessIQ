# AssessIQ AI Architecture & Copilot Governance (Phase 5)

## 1. Overview
Phase 5 equips AssessIQ with an **Assessment Copilot**, an automated **Resume Intelligence Analyzer**, and a **Multi-Skill Competency Matrix** for deep candidate scoring.

---

## 2. Mandatory Human-in-the-Loop Review Gate

> [!IMPORTANT]
> **Zero Direct Publishing Rule**: AI models (LLMs/heuristics) are never permitted to publish content directly into active candidate-facing question banks.

The lifecycle of an AI-generated question is strictly enforced:
1. **Proposal Generation**: The recruiter inputs role parameters (`role_title`, `seniority`, `target_skills`, `duration`).
2. **Duplicate & Overlap Scanning**: The engine performs similarity calculations against existing company question banks to identify overlaps.
3. **Draft / In-Review Staging**: The proposal is stored in `copilot_proposals` table with status `IN_REVIEW`. All questions default to `is_approved = False`.
4. **Human Review & Approval**: A Question Manager or Company Admin reviews, edits, or discards individual questions, designates a destination Question Bank, and clicks **Approve & Publish**. Only then are real `Question` and `QuestionOption` entities created.

```
[ Recruiter Prompt ] ──> [ AI Copilot ] ──> [ Duplicate Check ]
                                                    │
                                                    ▼
                                           [ IN_REVIEW Draft ]
                                                    │
                                           [ Human Review Gate ]
                                         (Edit / Select / Approve)
                                                    │
                                                    ▼
                                          [ Question Bank ]
```

---

## 3. Resume Parsing & Advisory-Only Intelligence

The **Resume Intelligence Engine** (`core/ai/resume_parser.py`) parses unstructured resume text, extracting technical competencies, estimated years of experience, education levels, and domain tags.

### Advisory-Only Guarantee
- **No Automated Rejections**: The resume parser provides consultative match recommendations to recruiters. It is architecturally decoupled from candidate qualification determinations.
- **No Unsolicited Auto-Assignments**: Assessment invitations require deliberate recruiter verification and scheduling.

---

## 4. Candidate Multi-Skill Competency Matrix

Candidate exam answers are evaluated not only as a scalar score percentage, but across domain tags (e.g. `Python`, `SQL`, `Docker`, `Algorithms`).

The aggregation formula:
$$\text{Skill Score \%} = \frac{\sum \text{Points Earned for Tag}}{\sum \text{Points Possible for Tag}} \times 100$$

Categorized into:
- **EXPERT**: $\ge 85\%$
- **ADVANCED**: $70\% - 84\%$
- **INTERMEDIATE**: $50\% - 69\%$
- **NOVICE**: $< 50\%$
