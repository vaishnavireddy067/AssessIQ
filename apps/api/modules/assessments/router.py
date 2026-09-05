"""
Assessments router — test builder, question linking, and publishing workflow.
"""
import uuid
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, inspect

from database import get_db
from core.rbac import RoleName
from core.exceptions import NotFoundError, ForbiddenError, BadRequestError
from core.audit import write_audit_log
from dependencies import get_current_user, require_roles, CurrentUser
from modules.assessments.models import (
    Assessment, AssessmentQuestion, Question, QuestionOption, 
    AssessmentStatus, QuestionType, DifficultyLevel, AssessmentTemplate
)

router = APIRouter()


# ── Schemas ───────────────────────────────────────────────────────────────────
class AssessmentCreate(BaseModel):
    title: str = Field(min_length=3, max_length=255)
    slug: str = Field(min_length=2, max_length=100)
    description: Optional[str] = None
    instructions: Optional[str] = None
    duration_minutes: int = Field(default=30, ge=5, le=300)
    passing_score_percentage: float = Field(default=60.0, ge=0.0, le=100.0)
    shuffle_questions: bool = False
    shuffle_options: bool = False
    company_pattern: str = "CUSTOM"
    drive_start_time: Optional[datetime] = None
    drive_end_time: Optional[datetime] = None
    sections_config: Optional[Dict[str, Any]] = None
    allow_section_switching: bool = True


class AssessmentUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=3, max_length=255)
    description: Optional[str] = None
    instructions: Optional[str] = None
    duration_minutes: Optional[int] = Field(None, ge=5, le=300)
    passing_score_percentage: Optional[float] = Field(None, ge=0.0, le=100.0)
    shuffle_questions: Optional[bool] = None
    shuffle_options: Optional[bool] = None
    company_pattern: Optional[str] = None
    drive_start_time: Optional[datetime] = None
    drive_end_time: Optional[datetime] = None
    sections_config: Optional[Dict[str, Any]] = None
    allow_section_switching: Optional[bool] = None


class ScheduleDriveRequest(BaseModel):
    drive_start_time: Optional[datetime] = None
    drive_end_time: Optional[datetime] = None
    validity_hours: Optional[int] = 48  # Quick preset e.g. 24, 48, 72 hours


class CreateFromBlueprintRequest(BaseModel):
    blueprint_key: str  # e.g. "TCS_ION", "INFOSYS_INFYTQ", "WIPRO_AMCAT", "ACCENTURE_COGNITIVE"
    title: Optional[str] = None
    slug: Optional[str] = None
    drive_start_time: Optional[datetime] = None
    drive_end_time: Optional[datetime] = None
    validity_hours: Optional[int] = 72


class TemplateSectionItem(BaseModel):
    id: str
    name: str
    type: str
    duration_minutes: int
    question_count: int
    description: Optional[str] = None
    difficulty_mix: Optional[Dict[str, int]] = None


class SaveTemplateRequest(BaseModel):
    title: str = Field(min_length=3, max_length=255)
    category: str = Field(default="CUSTOM")  # CODING_ONLY, TECHNICAL_MCQ, APTITUDE_REASONING, VERBAL_APTITUDE, FULL_CAMPUS, CUSTOM
    description: Optional[str] = None
    icon: Optional[str] = "Layers"
    color: Optional[str] = "#6366F1"
    duration_minutes: int = Field(default=60, ge=5, le=300)
    passing_score_percentage: float = Field(default=60.0, ge=0.0, le=100.0)
    allow_section_switching: bool = True
    sections: List[TemplateSectionItem] = []
    features: Optional[List[str]] = []


class CreateFromTemplateRequest(BaseModel):
    template_key: Optional[str] = None
    template_id: Optional[uuid.UUID] = None
    title: Optional[str] = None
    slug: Optional[str] = None
    duration_minutes: Optional[int] = None
    passing_score_percentage: Optional[float] = None
    allow_section_switching: Optional[bool] = None
    validity_hours: Optional[int] = 72


class AttachQuestionRequest(BaseModel):
    question_ids: List[uuid.UUID]
    section_name: Optional[str] = "General"


class AssessmentQuestionResponse(BaseModel):
    id: uuid.UUID
    question_id: uuid.UUID
    title: str
    content_markdown: str
    question_type: QuestionType
    difficulty: DifficultyLevel
    points: float
    section_name: Optional[str] = "General"
    order_index: int


class AssessmentResponse(BaseModel):
    id: uuid.UUID
    company_id: uuid.UUID
    title: str
    slug: str
    description: Optional[str] = None
    instructions: Optional[str] = None
    duration_minutes: int
    passing_score_percentage: float
    shuffle_questions: bool
    shuffle_options: bool
    company_pattern: str = "CUSTOM"
    drive_start_time: Optional[datetime] = None
    drive_end_time: Optional[datetime] = None
    sections_config: Optional[Dict[str, Any]] = None
    allow_section_switching: bool = True
    is_drive_active: bool = True
    status: AssessmentStatus
    total_questions: int = 0
    total_points: float = 0.0
    questions: List[AssessmentQuestionResponse] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ── Standard Company Test Pattern Blueprints ──────────────────────────────────
COMPANY_BLUEPRINTS = [
    {
        "key": "TCS_ION",
        "company_name": "TCS (Tata Consultancy Services)",
        "platform_name": "TCS iON NQT Engine",
        "title": "TCS NQT / Digital & Ninja Comprehensive Assessment",
        "description": "Standard multi-stage assessment pattern with Foundation & Advanced stages, strict sectional timers, and hands-on coding.",
        "duration_minutes": 100,
        "passing_score_percentage": 65.0,
        "allow_section_switching": False,  # TCS iON locks sections sequentially
        "sections": [
            {
                "id": "tcs_foundation_num",
                "name": "Part A: Numerical Ability (Foundation)",
                "type": "APTITUDE",
                "duration_minutes": 25,
                "question_count": 20,
                "description": "Number systems, percentages, profit & loss, algebra, arithmetic reasoning."
            },
            {
                "id": "tcs_foundation_verbal",
                "name": "Part A: Verbal Ability (Foundation)",
                "type": "VERBAL",
                "duration_minutes": 25,
                "question_count": 20,
                "description": "Sentence completion, reading comprehension, grammar correction, para-jumbles."
            },
            {
                "id": "tcs_foundation_reasoning",
                "name": "Part A: Reasoning Ability (Foundation)",
                "type": "REASONING",
                "duration_minutes": 25,
                "question_count": 20,
                "description": "Data sufficiency, syllogisms, blood relations, seating arrangement, coding-decoding."
            },
            {
                "id": "tcs_adv_coding",
                "name": "Part B: Advanced Hands-On Coding",
                "type": "CODING",
                "duration_minutes": 45,
                "question_count": 2,
                "description": "2 Algorithmic coding problems executed against hidden test cases (Python, Java, C++, C)."
            },
        ],
        "features": [
            "Sequential Section Locking (Part A -> Part B)",
            "Automated Test Case Runner with Time/Memory limits",
            "Continuous Webcam Proctoring & Audio Telemetry",
            "Cutoff classification: TCS Ninja (60%+) vs TCS Digital (80%+)"
        ]
    },
    {
        "key": "INFOSYS_INFYTQ",
        "company_name": "Infosys",
        "platform_name": "Infosys Springboard / InfyTQ Portal",
        "title": "Infosys Specialist Programmer & SE Assessment Pattern",
        "description": "Focuses on reasoning, pseudocode prediction, and live programming with negative marking dynamics.",
        "duration_minutes": 100,
        "passing_score_percentage": 65.0,
        "allow_section_switching": True,
        "sections": [
            {
                "id": "infy_reasoning",
                "name": "Section 1: Reasoning & Analytical Ability",
                "type": "REASONING",
                "duration_minutes": 25,
                "question_count": 15,
                "description": "Analytical problem solving, spatial reasoning, data interpretation."
            },
            {
                "id": "infy_tech_pseudo",
                "name": "Section 2: Technical Ability & Pseudocode",
                "type": "TECHNICAL_MCQ",
                "duration_minutes": 35,
                "question_count": 20,
                "description": "Code output prediction, algorithmic time complexity, data structures & OOP."
            },
            {
                "id": "infy_hands_on",
                "name": "Section 3: Hands-On Coding & SQL Sandbox",
                "type": "CODING_AND_SQL",
                "duration_minutes": 40,
                "question_count": 2,
                "description": "1 Algorithmic problem + 1 Relational SQL query scenario."
            },
        ],
        "features": [
            "Modular section navigation",
            "Specialist Programmer (DSE/SP) vs System Engineer benchmark",
            "Full code compiler sandbox + database evaluator"
        ]
    },
    {
        "key": "WIPRO_AMCAT",
        "company_name": "Wipro",
        "platform_name": "Wipro TalentNext / AMCAT / Superset",
        "title": "Wipro Elite National Talent Hunt (NTH) Pattern",
        "description": "Standard AMCAT-style adaptive multi-domain evaluation covering Quants, Logical, English, and Automata Coding.",
        "duration_minutes": 100,
        "passing_score_percentage": 60.0,
        "allow_section_switching": False,
        "sections": [
            {
                "id": "wipro_quants",
                "name": "Section 1: Quantitative Aptitude",
                "type": "APTITUDE",
                "duration_minutes": 20,
                "question_count": 16,
                "description": "Applied mathematics, probability, permutations, speed-distance-time."
            },
            {
                "id": "wipro_logical",
                "name": "Section 2: Logical Reasoning",
                "type": "REASONING",
                "duration_minutes": 20,
                "question_count": 14,
                "description": "Inductive reasoning, pattern detection, logical flowcharts."
            },
            {
                "id": "wipro_verbal",
                "name": "Section 3: English Verbal Ability",
                "type": "VERBAL",
                "duration_minutes": 20,
                "question_count": 18,
                "description": "Grammar, contextual vocabulary, reading comprehension."
            },
            {
                "id": "wipro_automata",
                "name": "Section 4: Automata Coding Challenge",
                "type": "CODING",
                "duration_minutes": 40,
                "question_count": 2,
                "description": "Automated code analysis for correctness, execution time, and boundary test cases."
            },
        ],
        "features": [
            "AMCAT-style section timers",
            "Automata code correctness validator",
            "Wipro Turbo (High Performer) upgrade evaluation"
        ]
    },
    {
        "key": "ACCENTURE_COGNITIVE",
        "company_name": "Accenture",
        "platform_name": "Accenture Assessment Portal",
        "title": "Accenture Cognitive & Technical Assessment Pattern",
        "description": "Two integrated stages: Cognitive + Technical Assessment followed by a live Coding Assessment.",
        "duration_minutes": 90,
        "passing_score_percentage": 65.0,
        "allow_section_switching": True,
        "sections": [
            {
                "id": "acc_cognitive",
                "name": "Stage 1: Cognitive Assessment",
                "type": "APTITUDE",
                "duration_minutes": 35,
                "question_count": 20,
                "description": "Critical thinking, abstract reasoning, and English fluency."
            },
            {
                "id": "acc_technical",
                "name": "Stage 2: Technical Essentials",
                "type": "TECHNICAL_MCQ",
                "duration_minutes": 25,
                "question_count": 15,
                "description": "Pseudocode, Cloud Fundamentals, Network Security, MS Office."
            },
            {
                "id": "acc_coding",
                "name": "Stage 3: Coding Sandbox",
                "type": "CODING",
                "duration_minutes": 30,
                "question_count": 2,
                "description": "Hands-on data structures and algorithmic manipulation."
            },
        ],
        "features": [
            "Advanced Application Engineering Analyst (AAEA) cutoff tracker",
            "Comprehensive technical domain MCQs + live code sandbox"
        ]
    }
]


# ── Assessment Pattern Templates ──────────────────────────────────────────────
PATTERN_TEMPLATES = [
    {
        "key": "CODING_ONLY",
        "title": "Pure Coding & Algorithms (Product SDE)",
        "category": "CODING_ONLY",
        "description": "Pure coding assessment for product companies (Google, Amazon style). Evaluates Data Structures, Algorithms, Time Complexity, and Edge Case Handling in our secure compiler sandbox.",
        "icon": "Code2",
        "emoji": "🖥️",
        "color": "#3B82F6",
        "gradient": "linear-gradient(135deg, rgba(59, 130, 246, 0.2), rgba(59, 130, 246, 0.05))",
        "duration_minutes": 60,
        "passing_score_percentage": 70.0,
        "allow_section_switching": True,
        "sections": [
            {
                "id": "sec_core_dsa",
                "name": "Core Data Structures & Algorithms",
                "type": "CODING",
                "duration_minutes": 25,
                "question_count": 1,
                "description": "Arrays, Strings, Hash Maps, Two Pointers problem solving.",
                "difficulty_mix": {"easy": 50, "medium": 50, "hard": 0}
            },
            {
                "id": "sec_adv_dsa",
                "name": "Advanced Problem Solving & Optimization",
                "type": "CODING",
                "duration_minutes": 35,
                "question_count": 1,
                "description": "Trees, Graphs, Dynamic Programming, or Greedy Optimization with hidden unit test cases.",
                "difficulty_mix": {"easy": 0, "medium": 60, "hard": 40}
            }
        ],
        "features": [
            "Live Code Execution Sandbox (Python, Java, C++, JS)",
            "Automated Hidden Test Case Runner",
            "Time & Memory Complexity Profiling",
            "Anti-Paste & Code Plagiarism Radar"
        ],
        "usage_count": 128,
        "is_default": True,
        "is_popular": True
    },
    {
        "key": "TECHNICAL_MCQ",
        "title": "Technical Fundamentals + MCQs",
        "category": "TECHNICAL_MCQ",
        "description": "Evaluates Computer Science core concepts including Operating Systems, Database Management (DBMS & SQL), Computer Networks, OOP principles, and code output prediction.",
        "icon": "Puzzle",
        "emoji": "🧩",
        "color": "#8B5CF6",
        "gradient": "linear-gradient(135deg, rgba(139, 92, 246, 0.2), rgba(139, 92, 246, 0.05))",
        "duration_minutes": 50,
        "passing_score_percentage": 60.0,
        "allow_section_switching": True,
        "sections": [
            {
                "id": "sec_cs_ds",
                "name": "Data Structures & Code Output",
                "type": "TECHNICAL_MCQ",
                "duration_minutes": 15,
                "question_count": 10,
                "description": "Time complexity, recursion tree, pointers, code snippet output prediction.",
                "difficulty_mix": {"easy": 30, "medium": 50, "hard": 20}
            },
            {
                "id": "sec_cs_dbms",
                "name": "DBMS, SQL & Indexing",
                "type": "TECHNICAL_MCQ",
                "duration_minutes": 15,
                "question_count": 10,
                "description": "Relational algebra, normalization, transactions, SQL joins and indexing.",
                "difficulty_mix": {"easy": 40, "medium": 40, "hard": 20}
            },
            {
                "id": "sec_cs_os_cn",
                "name": "Operating Systems & Networking",
                "type": "TECHNICAL_MCQ",
                "duration_minutes": 20,
                "question_count": 10,
                "description": "Process scheduling, deadlocks, virtual memory, TCP/IP, and OSI model.",
                "difficulty_mix": {"easy": 30, "medium": 50, "hard": 20}
            }
        ],
        "features": [
            "Instant Automated MCQ Evaluation",
            "Configurable Negative Marking Support",
            "Question Shuffling & Anti-Screen Sharing",
            "Comprehensive Domain Breakdown"
        ],
        "usage_count": 94,
        "is_default": True,
        "is_popular": False
    },
    {
        "key": "APTITUDE_REASONING",
        "title": "Quantitative Aptitude & Logical Reasoning",
        "category": "APTITUDE_REASONING",
        "description": "Designed for Data Analysts, Business Operations, Finance, and Non-Programming roles. Zero coding questions; rigorously tests mathematical reasoning, pattern deduction, and data interpretation.",
        "icon": "Brain",
        "emoji": "🧠",
        "color": "#10B981",
        "gradient": "linear-gradient(135deg, rgba(16, 185, 129, 0.2), rgba(16, 185, 129, 0.05))",
        "duration_minutes": 50,
        "passing_score_percentage": 60.0,
        "allow_section_switching": True,
        "sections": [
            {
                "id": "sec_quants",
                "name": "Quantitative Aptitude",
                "type": "APTITUDE",
                "duration_minutes": 25,
                "question_count": 15,
                "description": "Percentages, profit & loss, algebra, ratios, time-speed-distance, probability.",
                "difficulty_mix": {"easy": 40, "medium": 40, "hard": 20}
            },
            {
                "id": "sec_logical",
                "name": "Logical & Analytical Reasoning",
                "type": "REASONING",
                "duration_minutes": 25,
                "question_count": 15,
                "description": "Syllogisms, blood relations, seating arrangements, coding-decoding, series completion.",
                "difficulty_mix": {"easy": 30, "medium": 50, "hard": 20}
            }
        ],
        "features": [
            "Pure Aptitude & Logic (No Programming Needed)",
            "Data Interpretation Charts & Tables",
            "Time per question pacing recommendations",
            "Suitable for Fresher & Analyst Screening"
        ],
        "usage_count": 112,
        "is_default": True,
        "is_popular": True
    },
    {
        "key": "VERBAL_APTITUDE",
        "title": "Verbal Ability & Applied Aptitude",
        "category": "VERBAL_APTITUDE",
        "description": "Ideal for Consulting, Management Trainee, Customer Support, Marketing, and Client Operations roles. Measures English comprehension, business communication, and quantitative problem solving.",
        "icon": "MessageSquare",
        "emoji": "🗣️",
        "color": "#EC4899",
        "gradient": "linear-gradient(135deg, rgba(236, 72, 153, 0.2), rgba(236, 72, 153, 0.05))",
        "duration_minutes": 45,
        "passing_score_percentage": 60.0,
        "allow_section_switching": True,
        "sections": [
            {
                "id": "sec_verbal_comm",
                "name": "English Verbal & Business Communication",
                "type": "VERBAL",
                "duration_minutes": 20,
                "question_count": 15,
                "description": "Reading comprehension, sentence correction, vocabulary in context, para-jumbles.",
                "difficulty_mix": {"easy": 50, "medium": 35, "hard": 15}
            },
            {
                "id": "sec_applied_quants",
                "name": "Applied Numerical Reasoning",
                "type": "APTITUDE",
                "duration_minutes": 25,
                "question_count": 15,
                "description": "Business arithmetic, averages, profit margins, data tables.",
                "difficulty_mix": {"easy": 40, "medium": 45, "hard": 15}
            }
        ],
        "features": [
            "Grammar & Syntax Proficiency Scoring",
            "Reading Comprehension Timed Passages",
            "Business Analytical Logic Scenarios",
            "Instant Recruiter Skill Heatmap"
        ],
        "usage_count": 67,
        "is_default": True,
        "is_popular": False
    },
    {
        "key": "FULL_CAMPUS",
        "title": "Comprehensive Campus Hiring Drive Pattern",
        "category": "FULL_CAMPUS",
        "description": "The complete all-in-one hiring pattern modelled on Tier-1 campus drives (TCS iON, Infosys, Wipro, Accenture). Combines Numerical, Logical, Verbal, and Hands-on Coding in structured sections.",
        "icon": "GraduationCap",
        "emoji": "🎓",
        "color": "#F59E0B",
        "gradient": "linear-gradient(135deg, rgba(245, 158, 11, 0.2), rgba(245, 158, 11, 0.05))",
        "duration_minutes": 90,
        "passing_score_percentage": 65.0,
        "allow_section_switching": False,
        "sections": [
            {
                "id": "sec_campus_num",
                "name": "Part A: Numerical Ability",
                "type": "APTITUDE",
                "duration_minutes": 20,
                "question_count": 15,
                "description": "Number systems, percentages, ratios, permutations, modern mathematics.",
                "difficulty_mix": {"easy": 40, "medium": 40, "hard": 20}
            },
            {
                "id": "sec_campus_reas",
                "name": "Part A: Logical Reasoning",
                "type": "REASONING",
                "duration_minutes": 20,
                "question_count": 15,
                "description": "Analytical problem solving, pattern matching, series, and deductions.",
                "difficulty_mix": {"easy": 30, "medium": 50, "hard": 20}
            },
            {
                "id": "sec_campus_verb",
                "name": "Part A: Verbal Communication",
                "type": "VERBAL",
                "duration_minutes": 20,
                "question_count": 15,
                "description": "Grammar, sentence completion, reading comprehension.",
                "difficulty_mix": {"easy": 40, "medium": 40, "hard": 20}
            },
            {
                "id": "sec_campus_code",
                "name": "Part B: Hands-On Coding Sandbox",
                "type": "CODING",
                "duration_minutes": 30,
                "question_count": 1,
                "description": "Algorithmic programming challenge tested against standard and hidden unit tests.",
                "difficulty_mix": {"easy": 20, "medium": 60, "hard": 20}
            }
        ],
        "features": [
            "Strict Sequential Section Locking (Campus Standard)",
            "Integrated Multi-Domain Coverage (Aptitude + CS + Coding)",
            "Automated Percentile & Score Cut-off Benchmarking",
            "Batch Candidate Upload & Invitation Dispatch"
        ],
        "usage_count": 245,
        "is_default": True,
        "is_popular": True
    },
    {
        "key": "CUSTOM_BLANK",
        "title": "Custom Pattern from Scratch",
        "category": "CUSTOM",
        "description": "Build your own custom pattern from ground up. Add bespoke sections, choose individual timers, select specific question banks, and set custom passing criteria.",
        "icon": "Edit3",
        "emoji": "✏️",
        "color": "#6366F1",
        "gradient": "linear-gradient(135deg, rgba(99, 102, 241, 0.2), rgba(99, 102, 241, 0.05))",
        "duration_minutes": 60,
        "passing_score_percentage": 60.0,
        "allow_section_switching": True,
        "sections": [
            {
                "id": "sec_custom_1",
                "name": "Section 1: General Assessment",
                "type": "MIXED",
                "duration_minutes": 60,
                "question_count": 20,
                "description": "Configure custom questions from your company question bank.",
                "difficulty_mix": {"easy": 33, "medium": 34, "hard": 33}
            }
        ],
        "features": [
            "100% Fully Configurable Sections & Timers",
            "Flexible or Sequential Navigation",
            "Save as Reusable Company Template",
            "Granular Question Bank Attachment"
        ],
        "usage_count": 52,
        "is_default": True,
        "is_popular": False
    }
]


# ── Helper to resolve assessment details ──────────────────────────────────────
async def build_assessment_response(assessment: Assessment, db: AsyncSession) -> AssessmentResponse:
    insp = inspect(assessment)
    if insp.expired or insp.expired_attributes:
        await db.refresh(assessment)

    stmt = (
        select(AssessmentQuestion, Question)
        .join(Question, AssessmentQuestion.question_id == Question.id)
        .where(AssessmentQuestion.assessment_id == assessment.id, Question.deleted_at.is_(None))
        .order_by(AssessmentQuestion.order_index.asc())
    )
    result = await db.execute(stmt)
    rows = result.all()

    q_items = []
    total_pts = 0.0
    for link, q in rows:
        pts = link.points_override if link.points_override is not None else q.points
        total_pts += pts
        q_items.append(
            AssessmentQuestionResponse(
                id=link.id,
                question_id=q.id,
                title=q.title,
                content_markdown=q.content_markdown,
                question_type=q.question_type,
                difficulty=q.difficulty,
                points=pts,
                section_name=link.section_name or "General",
                order_index=link.order_index,
            )
        )

    # Determine if drive is active
    # SQLite returns tz-naive datetimes; normalise to UTC before comparing
    now = datetime.now(timezone.utc)
    def _as_utc(dt: Optional[datetime]) -> Optional[datetime]:
        if dt is None:
            return None
        return dt if dt.tzinfo is not None else dt.replace(tzinfo=timezone.utc)

    drive_start_utc = _as_utc(assessment.drive_start_time)
    drive_end_utc   = _as_utc(assessment.drive_end_time)
    is_active = True
    if drive_start_utc and now < drive_start_utc:
        is_active = False
    if drive_end_utc and now > drive_end_utc:
        is_active = False

    return AssessmentResponse(
        id=assessment.id,
        company_id=assessment.company_id,
        title=assessment.title,
        slug=assessment.slug,
        description=assessment.description,
        instructions=assessment.instructions,
        duration_minutes=assessment.duration_minutes,
        passing_score_percentage=assessment.passing_score_percentage,
        shuffle_questions=assessment.shuffle_questions,
        shuffle_options=assessment.shuffle_options,
        company_pattern=getattr(assessment, "company_pattern", "CUSTOM"),
        drive_start_time=assessment.drive_start_time,
        drive_end_time=assessment.drive_end_time,
        sections_config=assessment.sections_config,
        allow_section_switching=assessment.allow_section_switching,
        is_drive_active=is_active,
        status=assessment.status,
        total_questions=len(q_items),
        total_points=total_pts,
        questions=q_items,
        created_at=assessment.created_at,
        updated_at=assessment.updated_at,
    )


# ── Blueprint Routes ──────────────────────────────────────────────────────────
@router.get("/blueprints", response_model=List[Dict[str, Any]])
async def list_company_blueprints(
    current_user: CurrentUser = Depends(
        require_roles(RoleName.SUPER_ADMIN, RoleName.COMPANY_ADMIN, RoleName.RECRUITER, RoleName.QUESTION_MANAGER)
    ),
):
    """Retrieve pre-configured company assessment blueprints (TCS iON, Infosys InfyTQ, Wipro AMCAT, Accenture)."""
    return COMPANY_BLUEPRINTS


@router.post("/create-from-blueprint", response_model=AssessmentResponse, status_code=status.HTTP_201_CREATED)
async def create_from_blueprint(
    payload: CreateFromBlueprintRequest,
    current_user: CurrentUser = Depends(
        require_roles(RoleName.SUPER_ADMIN, RoleName.COMPANY_ADMIN, RoleName.RECRUITER)
    ),
    db: AsyncSession = Depends(get_db),
):
    """Instantiate a complete company-pattern assessment from standard blueprint with sectional timers."""
    if not current_user.company_id and not current_user.is_super_admin():
        raise ForbiddenError("Company context is required to create an assessment")

    blueprint = next((b for b in COMPANY_BLUEPRINTS if b["key"] == payload.blueprint_key), None)
    if not blueprint:
        raise NotFoundError("Company blueprint pattern")

    comp_id = current_user.company_id
    title = payload.title or blueprint["title"]
    raw_slug = payload.slug or f"{blueprint['key'].lower()}-drive-{uuid.uuid4().hex[:6]}"
    slug = raw_slug.lower().strip()

    # Calculate drive window if validity_hours given
    now = datetime.now(timezone.utc)
    drive_start = payload.drive_start_time or now
    drive_end = payload.drive_end_time
    if not drive_end and payload.validity_hours:
        drive_end = drive_start + timedelta(hours=payload.validity_hours)

    assessment = Assessment(
        company_id=comp_id,
        title=title,
        slug=slug,
        description=blueprint["description"],
        instructions=f"Official {blueprint['company_name']} ({blueprint['platform_name']}) assessment pattern. Ensure stable internet and webcam access.",
        duration_minutes=blueprint["duration_minutes"],
        passing_score_percentage=blueprint["passing_score_percentage"],
        shuffle_questions=False,
        shuffle_options=False,
        company_pattern=blueprint["key"],
        drive_start_time=drive_start,
        drive_end_time=drive_end,
        sections_config={"sections": blueprint["sections"]},
        allow_section_switching=blueprint["allow_section_switching"],
        status=AssessmentStatus.PUBLISHED,  # auto-ready for drive
        created_by=current_user.id,
    )
    db.add(assessment)
    await db.flush()

    # Auto-link questions from question banks to sections
    # Find existing questions matching company or global bank
    q_stmt = (
        select(Question)
        .where(Question.deleted_at.is_(None))
        .limit(25)
    )
    q_res = await db.execute(q_stmt)
    available_questions = q_res.scalars().all()

    sections = blueprint["sections"]
    q_idx = 0
    order_idx = 0
    for section in sections:
        sec_name = section["name"]
        # link 2-4 questions per section
        count = min(section.get("question_count", 4), 5)
        for _ in range(count):
            if q_idx < len(available_questions):
                q_obj = available_questions[q_idx]
                db.add(
                    AssessmentQuestion(
                        assessment_id=assessment.id,
                        question_id=q_obj.id,
                        section_name=sec_name,
                        order_index=order_idx,
                    )
                )
                order_idx += 1
                q_idx += 1

    await db.flush()

    await write_audit_log(
        db,
        user_id=current_user.id,
        company_id=comp_id,
        action="assessment.created_from_blueprint",
        resource_type="assessment",
        resource_id=str(assessment.id),
        metadata={"blueprint": payload.blueprint_key, "title": title},
    )

    return await build_assessment_response(assessment, db)


# ── Assessment Pattern Template Routes ────────────────────────────────────────
@router.get("/templates", response_model=List[Dict[str, Any]])
async def list_assessment_templates(
    category: Optional[str] = None,
    current_user: CurrentUser = Depends(
        require_roles(RoleName.SUPER_ADMIN, RoleName.COMPANY_ADMIN, RoleName.RECRUITER, RoleName.QUESTION_MANAGER)
    ),
    db: AsyncSession = Depends(get_db),
):
    """
    List all assessment pattern templates:
    1. Global platform pre-built patterns (Coding-Only, Tech+MCQ, Aptitude+Reasoning, Verbal+Aptitude, Full Campus, Custom)
    2. Company-specific saved custom templates
    """
    results = []
    # 1. Global built-in templates
    for tmpl in PATTERN_TEMPLATES:
        if not category or category == "ALL" or tmpl["category"] == category:
            results.append({
                **tmpl,
                "id": None,
                "is_company_custom": False,
            })

    # 2. Company custom templates
    if current_user.company_id:
        stmt = (
            select(AssessmentTemplate)
            .where(
                AssessmentTemplate.company_id == current_user.company_id,
                AssessmentTemplate.deleted_at.is_(None),
            )
            .order_by(AssessmentTemplate.usage_count.desc(), AssessmentTemplate.created_at.desc())
        )
        custom_rows = (await db.execute(stmt)).scalars().all()
        for c in custom_rows:
            if not category or category == "ALL" or c.category == category or category == "COMPANY_SAVED":
                sec_list = c.sections_config.get("sections", []) if c.sections_config else []
                results.append({
                    "id": str(c.id),
                    "key": c.key,
                    "title": c.title,
                    "category": c.category,
                    "description": c.description,
                    "icon": c.icon or "Layers",
                    "emoji": "🏢",
                    "color": c.color or "#6366F1",
                    "gradient": "linear-gradient(135deg, rgba(99, 102, 241, 0.2), rgba(99, 102, 241, 0.05))",
                    "duration_minutes": c.duration_minutes,
                    "passing_score_percentage": c.passing_score_percentage,
                    "allow_section_switching": c.allow_section_switching,
                    "sections": sec_list,
                    "features": c.features or ["Custom Company Template"],
                    "usage_count": c.usage_count,
                    "is_default": False,
                    "is_popular": c.usage_count > 10,
                    "is_company_custom": True,
                })

    return results


@router.post("/templates", status_code=status.HTTP_201_CREATED)
async def save_custom_template(
    payload: SaveTemplateRequest,
    current_user: CurrentUser = Depends(
        require_roles(RoleName.SUPER_ADMIN, RoleName.COMPANY_ADMIN, RoleName.RECRUITER)
    ),
    db: AsyncSession = Depends(get_db),
):
    """Save an assessment pattern as a reusable custom company template."""
    if not current_user.company_id and not current_user.is_super_admin():
        raise ForbiddenError("Company context required to save a template")

    key = f"custom-{uuid.uuid4().hex[:8]}"
    sections_data = [s.model_dump() for s in payload.sections]

    template = AssessmentTemplate(
        company_id=current_user.company_id,
        key=key,
        title=payload.title,
        category=payload.category,
        description=payload.description,
        icon=payload.icon or "Layers",
        color=payload.color or "#6366F1",
        duration_minutes=payload.duration_minutes,
        passing_score_percentage=payload.passing_score_percentage,
        allow_section_switching=payload.allow_section_switching,
        sections_config={"sections": sections_data},
        features=payload.features or ["Custom Company Template"],
        usage_count=0,
        is_public=False,
        created_by=current_user.id,
    )
    db.add(template)
    await db.flush()

    return {
        "id": str(template.id),
        "key": template.key,
        "title": template.title,
        "category": template.category,
        "duration_minutes": template.duration_minutes,
        "sections_count": len(sections_data),
        "message": "Custom template saved successfully",
    }


@router.delete("/templates/{template_id}")
async def delete_custom_template(
    template_id: uuid.UUID,
    current_user: CurrentUser = Depends(
        require_roles(RoleName.SUPER_ADMIN, RoleName.COMPANY_ADMIN)
    ),
    db: AsyncSession = Depends(get_db),
):
    """Delete a custom company template."""
    stmt = select(AssessmentTemplate).where(
        AssessmentTemplate.id == template_id,
        AssessmentTemplate.deleted_at.is_(None),
    )
    if not current_user.is_super_admin():
        stmt = stmt.where(AssessmentTemplate.company_id == current_user.company_id)

    template = (await db.execute(stmt)).scalar_one_or_none()
    if not template:
        raise NotFoundError("Template")

    template.deleted_at = datetime.now(timezone.utc)
    await db.flush()
    return {"status": "deleted", "template_id": str(template_id)}


@router.post("/create-from-template", response_model=AssessmentResponse, status_code=status.HTTP_201_CREATED)
async def create_from_template(
    payload: CreateFromTemplateRequest,
    current_user: CurrentUser = Depends(
        require_roles(RoleName.SUPER_ADMIN, RoleName.COMPANY_ADMIN, RoleName.RECRUITER)
    ),
    db: AsyncSession = Depends(get_db),
):
    """
    Instantiate a complete assessment from a Pattern Template.
    Supports built-in pattern keys ('CODING_ONLY', 'FULL_CAMPUS', etc.) or custom template UUID.
    Auto-populates and tags section questions from bank questions!
    """
    if not current_user.company_id and not current_user.is_super_admin():
        raise ForbiddenError("Company context is required to create an assessment")

    template_dict = None
    custom_record = None

    if payload.template_id:
        stmt = select(AssessmentTemplate).where(
            AssessmentTemplate.id == payload.template_id,
            AssessmentTemplate.deleted_at.is_(None),
        )
        if not current_user.is_super_admin():
            stmt = stmt.where(AssessmentTemplate.company_id == current_user.company_id)
        custom_record = (await db.execute(stmt)).scalar_one_or_none()
        if not custom_record:
            raise NotFoundError("Custom assessment template")

        template_dict = {
            "key": custom_record.key,
            "title": custom_record.title,
            "category": custom_record.category,
            "description": custom_record.description,
            "duration_minutes": custom_record.duration_minutes,
            "passing_score_percentage": custom_record.passing_score_percentage,
            "allow_section_switching": custom_record.allow_section_switching,
            "sections": custom_record.sections_config.get("sections", []) if custom_record.sections_config else [],
        }
        custom_record.usage_count += 1
    elif payload.template_key:
        template_dict = next((t for t in PATTERN_TEMPLATES if t["key"] == payload.template_key), None)
        if not template_dict:
            raise NotFoundError("Pattern template key")
        template_dict["usage_count"] = template_dict.get("usage_count", 0) + 1
    else:
        raise BadRequestError("Either template_key or template_id must be provided")

    comp_id = current_user.company_id
    title = payload.title or template_dict["title"]
    duration = payload.duration_minutes or template_dict["duration_minutes"]
    passing_score = payload.passing_score_percentage if payload.passing_score_percentage is not None else template_dict["passing_score_percentage"]
    allow_switching = payload.allow_section_switching if payload.allow_section_switching is not None else template_dict["allow_section_switching"]

    raw_slug = payload.slug or f"{template_dict['key'].lower().replace('_', '-')}-{uuid.uuid4().hex[:6]}"
    slug = raw_slug.lower().strip()

    now = datetime.now(timezone.utc)
    drive_end = now + timedelta(hours=payload.validity_hours or 72)

    assessment = Assessment(
        company_id=comp_id,
        title=title,
        slug=slug,
        description=template_dict.get("description"),
        instructions=f"Pattern: {template_dict['title']}. Complete all sections within the allotted timer.",
        duration_minutes=duration,
        passing_score_percentage=passing_score,
        shuffle_questions=False,
        shuffle_options=False,
        company_pattern=template_dict["category"],
        drive_start_time=now,
        drive_end_time=drive_end,
        sections_config={"sections": template_dict.get("sections", [])},
        allow_section_switching=allow_switching,
        status=AssessmentStatus.PUBLISHED,
        created_by=current_user.id,
    )
    db.add(assessment)
    await db.flush()

    # Intelligent Auto-linking of questions from database
    q_stmt = (
        select(Question)
        .where(Question.deleted_at.is_(None))
        .order_by(Question.created_at.desc())
        .limit(30)
    )
    available_questions = (await db.execute(q_stmt)).scalars().all()

    sections = template_dict.get("sections", [])
    q_idx = 0
    order_idx = 0
    for section in sections:
        sec_name = section["name"]
        count = min(section.get("question_count", 2), 4)
        for _ in range(count):
            if q_idx < len(available_questions):
                q_obj = available_questions[q_idx]
                db.add(
                    AssessmentQuestion(
                        assessment_id=assessment.id,
                        question_id=q_obj.id,
                        section_name=sec_name,
                        order_index=order_idx,
                    )
                )
                order_idx += 1
                q_idx += 1

    await db.flush()

    await write_audit_log(
        db,
        user_id=current_user.id,
        company_id=comp_id,
        action="assessment.created_from_template",
        resource_type="assessment",
        resource_id=str(assessment.id),
        metadata={"template": template_dict["key"], "title": title},
    )

    return await build_assessment_response(assessment, db)


# ── Assessment Routes ─────────────────────────────────────────────────────────
@router.get("", response_model=List[AssessmentResponse])
async def list_assessments(
    current_user: CurrentUser = Depends(
        require_roles(RoleName.SUPER_ADMIN, RoleName.COMPANY_ADMIN, RoleName.RECRUITER, RoleName.QUESTION_MANAGER)
    ),
    db: AsyncSession = Depends(get_db),
):
    """List all assessments created for the company workspace."""
    stmt = select(Assessment).where(Assessment.deleted_at.is_(None))
    if not current_user.is_super_admin():
        stmt = stmt.where(Assessment.company_id == current_user.company_id)
    stmt = stmt.order_by(Assessment.created_at.desc())
    result = await db.execute(stmt)
    assessments = result.scalars().all()

    return [await build_assessment_response(a, db) for a in assessments]


@router.post("", response_model=AssessmentResponse, status_code=status.HTTP_201_CREATED)
async def create_assessment(
    payload: AssessmentCreate,
    current_user: CurrentUser = Depends(
        require_roles(RoleName.SUPER_ADMIN, RoleName.COMPANY_ADMIN, RoleName.RECRUITER)
    ),
    db: AsyncSession = Depends(get_db),
):
    """Create a new technical assessment draft."""
    if not current_user.company_id and not current_user.is_super_admin():
        raise ForbiddenError("Company context is required to create an assessment")

    comp_id = current_user.company_id

    assessment = Assessment(
        company_id=comp_id,
        title=payload.title,
        slug=payload.slug.lower().strip(),
        description=payload.description,
        instructions=payload.instructions,
        duration_minutes=payload.duration_minutes,
        passing_score_percentage=payload.passing_score_percentage,
        shuffle_questions=payload.shuffle_questions,
        shuffle_options=payload.shuffle_options,
        company_pattern=payload.company_pattern,
        drive_start_time=payload.drive_start_time,
        drive_end_time=payload.drive_end_time,
        sections_config=payload.sections_config,
        allow_section_switching=payload.allow_section_switching,
        status=AssessmentStatus.DRAFT,
        created_by=current_user.id,
    )
    db.add(assessment)
    await db.flush()

    await write_audit_log(
        db,
        user_id=current_user.id,
        company_id=comp_id,
        action="assessment.created",
        resource_type="assessment",
        resource_id=str(assessment.id),
        metadata={"title": assessment.title, "slug": assessment.slug},
    )

    return await build_assessment_response(assessment, db)


@router.get("/{assessment_id}", response_model=AssessmentResponse)
async def get_assessment(
    assessment_id: uuid.UUID,
    current_user: CurrentUser = Depends(
        require_roles(RoleName.SUPER_ADMIN, RoleName.COMPANY_ADMIN, RoleName.RECRUITER, RoleName.QUESTION_MANAGER)
    ),
    db: AsyncSession = Depends(get_db),
):
    """Get assessment details including linked questions and scoring criteria."""
    stmt = select(Assessment).where(Assessment.id == assessment_id, Assessment.deleted_at.is_(None))
    if not current_user.is_super_admin():
        stmt = stmt.where(Assessment.company_id == current_user.company_id)

    res = await db.execute(stmt)
    assessment = res.scalar_one_or_none()
    if not assessment:
        raise NotFoundError("Assessment")

    return await build_assessment_response(assessment, db)


@router.put("/{assessment_id}", response_model=AssessmentResponse)
async def update_assessment(
    assessment_id: uuid.UUID,
    payload: AssessmentUpdate,
    current_user: CurrentUser = Depends(
        require_roles(RoleName.SUPER_ADMIN, RoleName.COMPANY_ADMIN, RoleName.RECRUITER)
    ),
    db: AsyncSession = Depends(get_db),
):
    """Update assessment metadata, time duration, and pass percentage."""
    stmt = select(Assessment).where(Assessment.id == assessment_id, Assessment.deleted_at.is_(None))
    if not current_user.is_super_admin():
        stmt = stmt.where(Assessment.company_id == current_user.company_id)

    assessment = (await db.execute(stmt)).scalar_one_or_none()
    if not assessment:
        raise NotFoundError("Assessment")

    for field, val in payload.dict(exclude_unset=True).items():
        setattr(assessment, field, val)

    await db.flush()
    await write_audit_log(
        db,
        user_id=current_user.id,
        company_id=assessment.company_id,
        action="assessment.updated",
        resource_type="assessment",
        resource_id=str(assessment.id),
    )
    return await build_assessment_response(assessment, db)


@router.post("/{assessment_id}/questions", response_model=AssessmentResponse)
async def attach_questions(
    assessment_id: uuid.UUID,
    payload: AttachQuestionRequest,
    current_user: CurrentUser = Depends(
        require_roles(RoleName.SUPER_ADMIN, RoleName.COMPANY_ADMIN, RoleName.RECRUITER)
    ),
    db: AsyncSession = Depends(get_db),
):
    """Attach one or more questions from question banks to the assessment."""
    stmt = select(Assessment).where(Assessment.id == assessment_id, Assessment.deleted_at.is_(None))
    if not current_user.is_super_admin():
        stmt = stmt.where(Assessment.company_id == current_user.company_id)

    assessment = (await db.execute(stmt)).scalar_one_or_none()
    if not assessment:
        raise NotFoundError("Assessment")

    # Get current max order index
    existing = await db.execute(
        select(AssessmentQuestion.order_index)
        .where(AssessmentQuestion.assessment_id == assessment.id)
        .order_by(AssessmentQuestion.order_index.desc())
    )
    max_idx = existing.scalars().first() or 0

    for q_id in payload.question_ids:
        # Check if already attached
        check_stmt = select(AssessmentQuestion).where(
            AssessmentQuestion.assessment_id == assessment_id,
            AssessmentQuestion.question_id == q_id,
        )
        if (await db.execute(check_stmt)).scalar_one_or_none():
            continue

        max_idx += 1
        db.add(
            AssessmentQuestion(
                assessment_id=assessment_id,
                question_id=q_id,
                section_name=payload.section_name or "General",
                order_index=max_idx,
            )
        )
    await db.flush()

    return await build_assessment_response(assessment, db)


@router.post("/{assessment_id}/schedule-drive", response_model=AssessmentResponse)
async def schedule_assessment_drive(
    assessment_id: uuid.UUID,
    payload: ScheduleDriveRequest,
    current_user: CurrentUser = Depends(
        require_roles(RoleName.SUPER_ADMIN, RoleName.COMPANY_ADMIN, RoleName.RECRUITER)
    ),
    db: AsyncSession = Depends(get_db),
):
    """Schedule or update assessment drive active validity window (hours or days)."""
    stmt = select(Assessment).where(Assessment.id == assessment_id, Assessment.deleted_at.is_(None))
    if not current_user.is_super_admin():
        stmt = stmt.where(Assessment.company_id == current_user.company_id)

    assessment = (await db.execute(stmt)).scalar_one_or_none()
    if not assessment:
        raise NotFoundError("Assessment")

    now = datetime.now(timezone.utc)
    drive_start = payload.drive_start_time or now
    drive_end = payload.drive_end_time
    if not drive_end and payload.validity_hours:
        drive_end = drive_start + timedelta(hours=payload.validity_hours)

    assessment.drive_start_time = drive_start
    assessment.drive_end_time = drive_end
    assessment.status = AssessmentStatus.PUBLISHED
    await db.flush()

    await write_audit_log(
        db,
        user_id=current_user.id,
        company_id=assessment.company_id,
        action="assessment.drive_scheduled",
        resource_type="assessment",
        resource_id=str(assessment.id),
        metadata={"drive_start": drive_start.isoformat(), "drive_end": drive_end.isoformat() if drive_end else None},
    )

    return await build_assessment_response(assessment, db)


@router.delete("/{assessment_id}/questions/{question_id}", response_model=AssessmentResponse)
async def detach_question(
    assessment_id: uuid.UUID,
    question_id: uuid.UUID,
    current_user: CurrentUser = Depends(
        require_roles(RoleName.SUPER_ADMIN, RoleName.COMPANY_ADMIN, RoleName.RECRUITER)
    ),
    db: AsyncSession = Depends(get_db),
):
    """Remove a question from an assessment."""
    stmt = select(Assessment).where(Assessment.id == assessment_id, Assessment.deleted_at.is_(None))
    if not current_user.is_super_admin():
        stmt = stmt.where(Assessment.company_id == current_user.company_id)

    assessment = (await db.execute(stmt)).scalar_one_or_none()
    if not assessment:
        raise NotFoundError("Assessment")

    await db.execute(
        delete(AssessmentQuestion).where(
            AssessmentQuestion.assessment_id == assessment_id,
            AssessmentQuestion.question_id == question_id,
        )
    )
    await db.flush()
    return await build_assessment_response(assessment, db)


@router.post("/{assessment_id}/publish", response_model=AssessmentResponse)
async def publish_assessment(
    assessment_id: uuid.UUID,
    current_user: CurrentUser = Depends(
        require_roles(RoleName.SUPER_ADMIN, RoleName.COMPANY_ADMIN, RoleName.RECRUITER)
    ),
    db: AsyncSession = Depends(get_db),
):
    """Publish an assessment to make it ready for candidate invitations."""
    stmt = select(Assessment).where(Assessment.id == assessment_id, Assessment.deleted_at.is_(None))
    if not current_user.is_super_admin():
        stmt = stmt.where(Assessment.company_id == current_user.company_id)

    assessment = (await db.execute(stmt)).scalar_one_or_none()
    if not assessment:
        raise NotFoundError("Assessment")

    # Ensure at least 1 question is attached
    count_stmt = select(AssessmentQuestion).where(AssessmentQuestion.assessment_id == assessment_id)
    links = (await db.execute(count_stmt)).scalars().all()
    if not links:
        raise BadRequestError("Cannot publish an assessment with zero questions")

    assessment.status = AssessmentStatus.PUBLISHED
    await db.flush()

    await write_audit_log(
        db,
        user_id=current_user.id,
        company_id=assessment.company_id,
        action="assessment.published",
        resource_type="assessment",
        resource_id=str(assessment.id),
    )
    return await build_assessment_response(assessment, db)
