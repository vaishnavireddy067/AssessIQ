"""
AssessIQ — Database Seeder (Phase 1, 2 & 3 Engine)
Seeds default roles, super admin, demo company, question banks, MCQs, Coding Challenges, SQL problems, published assessments, and demo test links.
Run via: python scripts/seed_initial_data.py
"""
import asyncio
import os
import sys
import uuid
from datetime import datetime, timezone, timedelta

# Add parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import AsyncSessionLocal, engine, Base
from core.security import hash_password
from core.rbac import RoleName
from modules.roles.models import Role, UserRole
from modules.companies.models import Company, CompanyPlan
from modules.users.models import User
from modules.candidates.models import Candidate
from modules.assessments.models import (
    QuestionBank, Question, QuestionOption, Assessment, AssessmentQuestion,
    CandidateInvitation, QuestionType, DifficultyLevel, AssessmentStatus, InvitationStatus
)
from modules.coding.models import CodingProblem, CodingTestCase, SqlProblem


DEFAULT_ROLES = [
    (RoleName.SUPER_ADMIN.value, "Platform Super Administrator with full global access"),
    (RoleName.COMPANY_ADMIN.value, "Organization Administrator with full company tenant access"),
    (RoleName.RECRUITER.value, "Recruiter who manages assessments, invites candidates, and reviews results"),
    (RoleName.QUESTION_MANAGER.value, "Assessment author who manages question banks"),
    (RoleName.CANDIDATE.value, "Test taker who takes assessments"),
]


async def seed_data():
    print("=" * 75)
    print("[*] AssessIQ Database Seeder Starting (Company Patterns & Coding/SQL Engine)...")
    print("=" * 75)

    import modules.analytics.models  # ensure Phase 9 tables are registered in Base
    import modules.audit.models

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # SQLite safe schema upgrades for newly added columns
        from sqlalchemy import text
        for col, typedef in [
            ("company_pattern", "TEXT DEFAULT 'CUSTOM'"),
            ("drive_start_time", "TIMESTAMP NULL"),
            ("drive_end_time", "TIMESTAMP NULL"),
            ("sections_config", "JSON NULL"),
            ("allow_section_switching", "BOOLEAN DEFAULT 1"),
        ]:
            try:
                await conn.execute(text(f"ALTER TABLE assessments ADD COLUMN {col} {typedef}"))
            except Exception:
                pass
        try:
            await conn.execute(text("ALTER TABLE assessment_questions ADD COLUMN section_name TEXT DEFAULT 'General'"))
        except Exception:
            pass

    async with AsyncSessionLocal() as db:
        # 1. Seed Roles
        print("\n[1/7] Seeding RBAC Roles...")
        role_map = {}
        for role_name, description in DEFAULT_ROLES:
            stmt = select(Role).where(Role.name == role_name)
            result = await db.execute(stmt)
            role_obj = result.scalar_one_or_none()
            if not role_obj:
                role_obj = Role(name=role_name, description=description)
                db.add(role_obj)
                await db.flush()
                print(f"  + Created Role: {role_name}")
            else:
                print(f"  [OK] Role Exists: {role_name}")
            role_map[role_name] = role_obj

        # 2. Seed Super Admin
        print("\n[2/7] Seeding Super Admin...")
        superadmin_email = os.getenv("SUPERADMIN_EMAIL", "superadmin@assessiq.com")
        superadmin_pass = os.getenv("SUPERADMIN_PASSWORD", "AssessIQ2026!Super")

        stmt = select(User).where(User.email == superadmin_email)
        super_admin = (await db.execute(stmt)).scalar_one_or_none()

        if not super_admin:
            super_admin = User(
                email=superadmin_email,
                hashed_password=hash_password(superadmin_pass),
                first_name="Platform",
                last_name="Admin",
                company_id=None,
                is_active=True,
                is_email_verified=True,
            )
            db.add(super_admin)
            await db.flush()

            db.add(UserRole(
                user_id=super_admin.id,
                role_id=role_map[RoleName.SUPER_ADMIN.value].id,
                company_id=None,
            ))
            await db.flush()
            print(f"  + Created Super Admin: {superadmin_email}")
        else:
            print(f"  [OK] Super Admin Exists: {superadmin_email}")

        # 3. Seed Demo Company
        print("\n[3/7] Seeding Demo Company (Acme Corp)...")
        demo_slug = "acme"
        stmt = select(Company).where(Company.slug == demo_slug)
        demo_company = (await db.execute(stmt)).scalar_one_or_none()

        if not demo_company:
            demo_company = Company(
                name="Acme Corporation",
                slug=demo_slug,
                domain="acme.com",
                website="https://acme.example.com",
                industry="Software & Cloud Services",
                size="100-500",
                plan=CompanyPlan.BUSINESS,
                is_active=True,
            )
            db.add(demo_company)
            await db.flush()

            comp_admin = User(
                email="admin@acme.com",
                hashed_password=hash_password("AcmeAdmin2026!"),
                first_name="Alice",
                last_name="Director",
                company_id=demo_company.id,
                is_active=True,
                is_email_verified=True,
            )
            db.add(comp_admin)
            await db.flush()

            db.add(UserRole(
                user_id=comp_admin.id,
                role_id=role_map[RoleName.COMPANY_ADMIN.value].id,
                company_id=demo_company.id,
            ))

            recruiter = User(
                email="recruiter@acme.com",
                hashed_password=hash_password("AcmeRecruiter2026!"),
                first_name="Bob",
                last_name="Hiring",
                company_id=demo_company.id,
                is_active=True,
                is_email_verified=True,
            )
            db.add(recruiter)
            await db.flush()

            db.add(UserRole(
                user_id=recruiter.id,
                role_id=role_map[RoleName.RECRUITER.value].id,
                company_id=demo_company.id,
            ))
            print("  + Created Company Admin: admin@acme.com / AcmeAdmin2026!")
            print("  + Created Recruiter: recruiter@acme.com / AcmeRecruiter2026!")
        else:
            print(f"  [OK] Demo Company Exists: {demo_company.name}")

        # 4. Seed Global Candidate
        print("\n[4/7] Seeding Global Candidate...")
        cand_email = "candidate@example.com"
        stmt = select(User).where(User.email == cand_email)
        demo_candidate = (await db.execute(stmt)).scalar_one_or_none()

        if not demo_candidate:
            demo_candidate = User(
                email=cand_email,
                hashed_password=hash_password("Candidate2026!"),
                first_name="Jane",
                last_name="Developer",
                company_id=None,
                is_active=True,
                is_email_verified=True,
            )
            db.add(demo_candidate)
            await db.flush()

            db.add(UserRole(
                user_id=demo_candidate.id,
                role_id=role_map[RoleName.CANDIDATE.value].id,
                company_id=None,
            ))

            cand_profile = Candidate(
                user_id=demo_candidate.id,
                resume_url="https://github.com/janedev/resume",
            )
            db.add(cand_profile)
            await db.flush()
            print("  + Created Demo Candidate: candidate@example.com / Candidate2026!")
        else:
            print(f"  [OK] Demo Candidate Exists: {cand_email}")
            cand_profile_res = await db.execute(select(Candidate).where(Candidate.user_id == demo_candidate.id))
            cand_profile = cand_profile_res.scalar_one_or_none()

        # 5. Seed Question Banks & Technical MCQs
        print("\n[5/7] Seeding Technical Question Banks & MCQs...")
        bank_stmt = select(QuestionBank).where(QuestionBank.name == "Python & Backend Engineering", QuestionBank.company_id == demo_company.id)
        py_bank = (await db.execute(bank_stmt)).scalar_one_or_none()

        seeded_questions = []
        if not py_bank:
            py_bank = QuestionBank(
                name="Python & Backend Engineering",
                description="Core Python, concurrency, memory management, asyncio, and API architecture.",
                category="Backend",
                company_id=demo_company.id,
                is_active=True,
            )
            db.add(py_bank)
            await db.flush()

            q1 = Question(
                bank_id=py_bank.id,
                company_id=demo_company.id,
                title="Python Global Interpreter Lock (GIL)",
                content_markdown="Which statement accurately describes the effect of Python's **Global Interpreter Lock (GIL)** in CPython?",
                question_type=QuestionType.MCQ_SINGLE,
                difficulty=DifficultyLevel.MEDIUM,
                points=2.0,
                explanation="CPython's GIL prevents multiple native threads from executing Python bytecode simultaneously, making multithreading CPU-bound tasks in single processes ineffective for multi-core parallelism.",
                tags=["python", "concurrency", "cpython"],
            )
            db.add(q1)
            await db.flush()
            seeded_questions.append(q1)

            db.add_all([
                QuestionOption(question_id=q1.id, option_text="It prevents multi-core parallelism for CPU-bound tasks in a single process", is_correct=True, order_index=0),
                QuestionOption(question_id=q1.id, option_text="It prevents I/O-bound operations from executing asynchronously", is_correct=False, order_index=1),
                QuestionOption(question_id=q1.id, option_text="It automatically compiles Python bytecode to native assembly ahead-of-time", is_correct=False, order_index=2),
                QuestionOption(question_id=q1.id, option_text="It disables garbage collection in multi-threaded programs", is_correct=False, order_index=3),
            ])

            q2 = Question(
                bank_id=py_bank.id,
                company_id=demo_company.id,
                title="Asyncio Event Loop Mechanics",
                content_markdown="In Python `asyncio`, what happens when a coroutine executes a synchronous blocking call such as `time.sleep(5)`?",
                question_type=QuestionType.MCQ_SINGLE,
                difficulty=DifficultyLevel.HARD,
                points=3.0,
                explanation="A synchronous blocking call blocks the entire operating system thread hosting the event loop, pausing all other concurrent tasks until the blocking call finishes.",
                tags=["asyncio", "python", "performance"],
            )
            db.add(q2)
            await db.flush()
            seeded_questions.append(q2)

            db.add_all([
                QuestionOption(question_id=q2.id, option_text="It blocks the entire event loop thread, stopping all other tasks from running", is_correct=True, order_index=0),
                QuestionOption(question_id=q2.id, option_text="Asyncio automatically delegates synchronous calls to an internal background thread", is_correct=False, order_index=1),
                QuestionOption(question_id=q2.id, option_text="The event loop preempts the coroutine and continues processing other tasks", is_correct=False, order_index=2),
                QuestionOption(question_id=q2.id, option_text="A RuntimeError is raised immediately", is_correct=False, order_index=3),
            ])
            print("  + Seeded MCQ Questions in Python & Backend Engineering")
        else:
            print("  [OK] Question Bank Exists: Python & Backend Engineering")
            q_res = await db.execute(select(Question).where(Question.bank_id == py_bank.id))
            seeded_questions = list(q_res.scalars().all())

        # Seed Aptitude & Reasoning Banks for Company Patterns
        apt_bank_stmt = select(QuestionBank).where(QuestionBank.name == "Quantitative & Numerical Ability", QuestionBank.company_id == demo_company.id)
        apt_bank = (await db.execute(apt_bank_stmt)).scalar_one_or_none()
        all_apt_questions = []

        if not apt_bank:
            apt_bank = QuestionBank(
                name="Quantitative & Numerical Ability",
                description="Percentages, Profit & Loss, Speed-Time-Distance, Permutations, Probability, and Algebra for company tests.",
                category="Aptitude",
                company_id=demo_company.id,
                is_active=True,
            )
            db.add(apt_bank)
            await db.flush()

            qa1 = Question(
                bank_id=apt_bank.id,
                company_id=demo_company.id,
                title="Work and Time Efficiency",
                content_markdown="A can complete a project in 12 days and B can complete it in 18 days. If they work together for 4 days, what fraction of the work remains?",
                question_type=QuestionType.MCQ_SINGLE,
                difficulty=DifficultyLevel.EASY,
                points=1.0,
                explanation="1 day work = 1/12 + 1/18 = 5/36. In 4 days, work done = 4 * 5/36 = 20/36 = 5/9. Remaining work = 1 - 5/9 = 4/9.",
                tags=["aptitude", "time-and-work", "tcs-ion", "wipro"],
            )
            db.add(qa1)
            await db.flush()
            db.add_all([
                QuestionOption(question_id=qa1.id, option_text="4/9", is_correct=True, order_index=0),
                QuestionOption(question_id=qa1.id, option_text="5/9", is_correct=False, order_index=1),
                QuestionOption(question_id=qa1.id, option_text="1/3", is_correct=False, order_index=2),
                QuestionOption(question_id=qa1.id, option_text="7/18", is_correct=False, order_index=3),
            ])
            all_apt_questions.append(qa1)

            qa2 = Question(
                bank_id=apt_bank.id,
                company_id=demo_company.id,
                title="Compound Interest vs Simple Interest",
                content_markdown="The difference between compound interest (compounded annually) and simple interest on a sum of money at 10% per annum for 2 years is $45. Find the principal sum.",
                question_type=QuestionType.MCQ_SINGLE,
                difficulty=DifficultyLevel.MEDIUM,
                points=1.0,
                explanation="Difference for 2 years = P * (R/100)^2. 45 = P * (10/100)^2 = P * (1/100) => P = $4,500.",
                tags=["aptitude", "interest", "tcs-ion", "infosys"],
            )
            db.add(qa2)
            await db.flush()
            db.add_all([
                QuestionOption(question_id=qa2.id, option_text="$4,500", is_correct=True, order_index=0),
                QuestionOption(question_id=qa2.id, option_text="$4,000", is_correct=False, order_index=1),
                QuestionOption(question_id=qa2.id, option_text="$5,000", is_correct=False, order_index=2),
                QuestionOption(question_id=qa2.id, option_text="$3,800", is_correct=False, order_index=3),
            ])
            all_apt_questions.append(qa2)
            print("  + Seeded Quantitative Aptitude Question Bank")
        else:
            q_res = await db.execute(select(Question).where(Question.bank_id == apt_bank.id))
            all_apt_questions = list(q_res.scalars().all())

        # Seed Reasoning & Verbal Bank
        reas_bank_stmt = select(QuestionBank).where(QuestionBank.name == "Logical Reasoning & Verbal Ability", QuestionBank.company_id == demo_company.id)
        reas_bank = (await db.execute(reas_bank_stmt)).scalar_one_or_none()
        all_reas_questions = []

        if not reas_bank:
            reas_bank = QuestionBank(
                name="Logical Reasoning & Verbal Ability",
                description="Syllogisms, Blood Relations, Coding-Decoding, Sentence Completion, and Technical Pseudocode.",
                category="Reasoning",
                company_id=demo_company.id,
                is_active=True,
            )
            db.add(reas_bank)
            await db.flush()

            qr1 = Question(
                bank_id=reas_bank.id,
                company_id=demo_company.id,
                title="Syllogism Deductive Logic",
                content_markdown="**Statements:**\n1. All algorithms are programs.\n2. Some programs are scalable.\n\n**Conclusions:**\nI. Some algorithms are scalable.\nII. Some programs are algorithms.",
                question_type=QuestionType.MCQ_SINGLE,
                difficulty=DifficultyLevel.EASY,
                points=1.0,
                explanation="Statement 1 (All A are B) converts to 'Some B are A', so Conclusion II holds. Conclusion I is uncertain.",
                tags=["reasoning", "syllogism", "tcs-ion", "wipro"],
            )
            db.add(qr1)
            await db.flush()
            db.add_all([
                QuestionOption(question_id=qr1.id, option_text="Only conclusion II follows", is_correct=True, order_index=0),
                QuestionOption(question_id=qr1.id, option_text="Only conclusion I follows", is_correct=False, order_index=1),
                QuestionOption(question_id=qr1.id, option_text="Both I and II follow", is_correct=False, order_index=2),
                QuestionOption(question_id=qr1.id, option_text="Neither I nor II follows", is_correct=False, order_index=3),
            ])
            all_reas_questions.append(qr1)

            qr2 = Question(
                bank_id=reas_bank.id,
                company_id=demo_company.id,
                title="Pseudocode Loop Complexity",
                content_markdown="Consider the following pseudocode segment:\n```text\nint count = 0;\nfor (int i = 1; i <= n; i = i * 2) {\n    for (int j = 1; j <= n; j++) {\n        count++;\n    }\n}\n```\nWhat is the asymptotic time complexity?",
                question_type=QuestionType.MCQ_SINGLE,
                difficulty=DifficultyLevel.MEDIUM,
                points=2.0,
                explanation="Outer loop runs log2(n) times, inner loop runs n times => Total operations = O(n log n).",
                tags=["pseudocode", "time-complexity", "infosys", "accenture"],
            )
            db.add(qr2)
            await db.flush()
            db.add_all([
                QuestionOption(question_id=qr2.id, option_text="O(n log n)", is_correct=True, order_index=0),
                QuestionOption(question_id=qr2.id, option_text="O(n^2)", is_correct=False, order_index=1),
                QuestionOption(question_id=qr2.id, option_text="O(log n)", is_correct=False, order_index=2),
                QuestionOption(question_id=qr2.id, option_text="O(n)", is_correct=False, order_index=3),
            ])
            all_reas_questions.append(qr2)
            print("  + Seeded Logical Reasoning & Verbal Question Bank")
        else:
            q_res = await db.execute(select(Question).where(Question.bank_id == reas_bank.id))
            all_reas_questions = list(q_res.scalars().all())

        # 6. Seed Coding Challenges & SQL Problems
        print("\n[6/7] Seeding Algorithmic Coding Challenges & SQL Problems...")
        cp_stmt = select(CodingProblem).where(CodingProblem.slug == "two-sum-target-finder", CodingProblem.company_id == demo_company.id)
        coding_prob = (await db.execute(cp_stmt)).scalar_one_or_none()

        if not coding_prob:
            coding_prob = CodingProblem(
                company_id=demo_company.id,
                title="Two Sum — Target Pair Indices",
                slug="two-sum-target-finder",
                description_markdown="Given an array of integers `nums` and an integer `target`, return the *indices of the two numbers such that they add up to target*.\n\n### Input Format\n- Line 1: `target` (Integer)\n- Line 2: Space-separated integers (`nums`)\n\n### Output Format\n- Print the two 0-based indices separated by a space (e.g. `0 1`).",
                difficulty=DifficultyLevel.EASY,
                time_limit_ms=2000,
                memory_limit_mb=256,
                starter_code={
                    "python": "import sys\n\ndef solve():\n    lines = sys.stdin.read().strip().splitlines()\n    if len(lines) < 2:\n        return\n    target = int(lines[0])\n    nums = [int(x) for x in lines[1].split()]\n    \n    # Write your O(n) hash map solution below\n    seen = {}\n    for i, num in enumerate(nums):\n        comp = target - num\n        if comp in seen:\n            print(f\"{seen[comp]} {i}\")\n            return\n        seen[num] = i\n\nsolve()\n",
                    "javascript": "const fs = require('fs');\n\nfunction solve() {\n    const input = fs.readFileSync(0, 'utf-8').trim().split('\\n');\n    if (input.length < 2) return;\n    const target = parseInt(input[0]);\n    const nums = input[1].split(' ').map(Number);\n    \n    const map = new Map();\n    for (let i = 0; i < nums.length; i++) {\n        const comp = target - nums[i];\n        if (map.has(comp)) {\n            console.log(`${map.get(comp)} ${i}`);\n            return;\n        }\n        map.set(nums[i], i);\n    }\n}\nsolve();\n"
                },
                points=10.0,
                tags=["algorithms", "hash-table", "arrays"],
            )
            db.add(coding_prob)
            await db.flush()

            # Seed Test Cases (Sample + Hidden)
            db.add_all([
                CodingTestCase(problem_id=coding_prob.id, input_data="9\n2 7 11 15", expected_output="0 1", is_hidden=False, order_index=0, explanation="nums[0] + nums[1] == 2 + 7 == 9"),
                CodingTestCase(problem_id=coding_prob.id, input_data="6\n3 2 4", expected_output="1 2", is_hidden=False, order_index=1, explanation="nums[1] + nums[2] == 2 + 4 == 6"),
                CodingTestCase(problem_id=coding_prob.id, input_data="6\n3 3", expected_output="0 1", is_hidden=True, order_index=2),
                CodingTestCase(problem_id=coding_prob.id, input_data="20\n1 5 13 8 7", expected_output="2 4", is_hidden=True, order_index=3),
            ])
            print(f"  + Seeded Coding Challenge: {coding_prob.title} (4 test cases)")

        # Seed SQL Problem
        sql_stmt = select(SqlProblem).where(SqlProblem.slug == "top-spending-customers", SqlProblem.company_id == demo_company.id)
        sql_prob = (await db.execute(sql_stmt)).scalar_one_or_none()

        if not sql_prob:
            sql_schema = """
CREATE TABLE customers (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    country TEXT NOT NULL
);

CREATE TABLE orders (
    id INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL,
    amount REAL NOT NULL,
    order_date TEXT NOT NULL,
    FOREIGN KEY (customer_id) REFERENCES customers(id)
);

INSERT INTO customers VALUES (1, 'Alice Corp', 'USA'), (2, 'Beta LLC', 'UK'), (3, 'Gamma GmbH', 'Germany'), (4, 'Delta Inc', 'USA');
INSERT INTO orders VALUES (101, 1, 1200.00, '2026-01-15'), (102, 1, 850.00, '2026-02-10'), (103, 2, 400.00, '2026-01-20'), (104, 3, 3500.00, '2026-03-01'), (105, 4, 150.00, '2026-02-28');
"""
            sql_solution = """
SELECT c.name, SUM(o.amount) as total_spent
FROM customers c
JOIN orders o ON c.id = o.customer_id
GROUP BY c.id, c.name
HAVING SUM(o.amount) > 1000
ORDER BY total_spent DESC;
"""
            sql_prob = SqlProblem(
                company_id=demo_company.id,
                title="High-Value Customers Aggregation",
                slug="top-spending-customers",
                description_markdown="Write an SQL query to find the **name** and **total_spent** for each customer whose cumulative order amount exceeds **$1,000**.\n\nOrder the results in descending order by `total_spent`.",
                difficulty=DifficultyLevel.MEDIUM,
                schema_sql=sql_schema,
                solution_sql=sql_solution,
                points=10.0,
                tags=["sql", "joins", "group-by", "aggregation"],
            )
            db.add(sql_prob)
            await db.flush()
            print(f"  + Seeded SQL Challenge: {sql_prob.title}")

        # 7. Seed Company-Specific Mock Assessment Drives
        print("\n[7/7] Seeding Prebuilt Company Mock Drives (TCS iON, Infosys, Wipro, Accenture)...")

        # 7.1 TCS iON NQT Mock Assessment
        tcs_ass_stmt = select(Assessment).where(Assessment.slug == "tcs-ion-nqt-mock-drive", Assessment.company_id == demo_company.id)
        tcs_ass = (await db.execute(tcs_ass_stmt)).scalar_one_or_none()
        now = datetime.now(timezone.utc)

        if not tcs_ass:
            tcs_ass = Assessment(
                company_id=demo_company.id,
                title="TCS iON NQT / Digital & Ninja Pattern Mock Assessment",
                slug="tcs-ion-nqt-mock-drive",
                description="Official TCS iON National Qualifier Test (NQT) pattern covering Foundation Section and Advanced Section with sequential section locking.",
                instructions="Part A Foundation Section consists of Numerical, Verbal, and Reasoning Ability. Part B contains Advanced Coding.",
                duration_minutes=90,
                passing_score_percentage=65.0,
                shuffle_questions=False,
                shuffle_options=False,
                company_pattern="TCS_ION",
                drive_start_time=now - timedelta(hours=1),
                drive_end_time=now + timedelta(days=7),
                sections_config={
                    "sections": [
                        {"id": "tcs_num", "name": "Part A: Numerical Ability", "type": "APTITUDE", "duration_minutes": 25},
                        {"id": "tcs_reas", "name": "Part A: Reasoning Ability", "type": "REASONING", "duration_minutes": 25},
                        {"id": "tcs_code", "name": "Part B: Advanced Hands-On Coding", "type": "CODING", "duration_minutes": 40},
                    ]
                },
                allow_section_switching=False,
                status=AssessmentStatus.PUBLISHED,
                created_by=comp_admin.id if 'comp_admin' in locals() else None,
            )
            db.add(tcs_ass)
            await db.flush()

            # Attach questions to TCS sections
            if all_apt_questions:
                db.add(AssessmentQuestion(assessment_id=tcs_ass.id, question_id=all_apt_questions[0].id, section_name="Part A: Numerical Ability", order_index=0))
            if all_reas_questions:
                db.add(AssessmentQuestion(assessment_id=tcs_ass.id, question_id=all_reas_questions[0].id, section_name="Part A: Reasoning Ability", order_index=1))
            if seeded_questions:
                db.add(AssessmentQuestion(assessment_id=tcs_ass.id, question_id=seeded_questions[0].id, section_name="Part B: Advanced Hands-On Coding", order_index=2))
            await db.flush()

            # Seed demo invitation for TCS test
            db.add(CandidateInvitation(
                company_id=demo_company.id,
                assessment_id=tcs_ass.id,
                candidate_id=cand_profile.id if cand_profile else None,
                candidate_email="candidate@example.com",
                candidate_name="Jane Developer",
                token="tcs-nqt-demo-token",
                status=InvitationStatus.PENDING,
                expires_at=now + timedelta(days=7),
            ))
            print("  + Created TCS iON Pattern Assessment Drive: /exam/tcs-nqt-demo-token")

        # 7.2 Infosys InfyTQ / Springboard Assessment
        infy_ass_stmt = select(Assessment).where(Assessment.slug == "infosys-infytq-specialist-drive", Assessment.company_id == demo_company.id)
        infy_ass = (await db.execute(infy_ass_stmt)).scalar_one_or_none()

        if not infy_ass:
            infy_ass = Assessment(
                company_id=demo_company.id,
                title="Infosys Specialist Programmer (DSE/SP) & SE Assessment",
                slug="infosys-infytq-specialist-drive",
                description="Infosys InfyTQ assessment pattern evaluating analytical reasoning, pseudocode prediction, and live programming.",
                instructions="Navigate across modular sections. Negative marking applies on pseudocode sections.",
                duration_minutes=90,
                passing_score_percentage=65.0,
                company_pattern="INFOSYS_INFYTQ",
                drive_start_time=now - timedelta(hours=1),
                drive_end_time=now + timedelta(days=7),
                sections_config={
                    "sections": [
                        {"id": "infy_reas", "name": "Section 1: Reasoning Ability", "type": "REASONING", "duration_minutes": 25},
                        {"id": "infy_pseudo", "name": "Section 2: Technical & Pseudocode", "type": "TECHNICAL_MCQ", "duration_minutes": 30},
                        {"id": "infy_code", "name": "Section 3: Hands-On Coding & SQL", "type": "CODING_AND_SQL", "duration_minutes": 35},
                    ]
                },
                allow_section_switching=True,
                status=AssessmentStatus.PUBLISHED,
                created_by=comp_admin.id if 'comp_admin' in locals() else None,
            )
            db.add(infy_ass)
            await db.flush()

            if all_reas_questions:
                db.add(AssessmentQuestion(assessment_id=infy_ass.id, question_id=all_reas_questions[0].id, section_name="Section 1: Reasoning Ability", order_index=0))
                if len(all_reas_questions) > 1:
                    db.add(AssessmentQuestion(assessment_id=infy_ass.id, question_id=all_reas_questions[1].id, section_name="Section 2: Technical & Pseudocode", order_index=1))
            if seeded_questions:
                db.add(AssessmentQuestion(assessment_id=infy_ass.id, question_id=seeded_questions[0].id, section_name="Section 3: Hands-On Coding & SQL", order_index=2))
            await db.flush()

            db.add(CandidateInvitation(
                company_id=demo_company.id,
                assessment_id=infy_ass.id,
                candidate_id=cand_profile.id if cand_profile else None,
                candidate_email="candidate@example.com",
                candidate_name="Jane Developer",
                token="infosys-demo-token",
                status=InvitationStatus.PENDING,
                expires_at=now + timedelta(days=7),
            ))
            print("  + Created Infosys Pattern Assessment Drive: /exam/infosys-demo-token")

        # 7.3 General Full-Stack Assessment
        ass_stmt = select(Assessment).where(Assessment.slug == "fullstack-backend-assessment", Assessment.company_id == demo_company.id)
        demo_assessment = (await db.execute(ass_stmt)).scalar_one_or_none()

        if not demo_assessment:
            demo_assessment = Assessment(
                company_id=demo_company.id,
                title="Full-Stack Backend & Systems Engineering Assessment",
                slug="fullstack-backend-assessment",
                description="Technical evaluation of Python concurrency, asynchronous programming, database indexing, and algorithmic problem solving.",
                instructions="Read each question carefully. You have 30 minutes to complete the test. Once started, the timer cannot be paused.",
                duration_minutes=30,
                passing_score_percentage=60.0,
                shuffle_questions=False,
                shuffle_options=False,
                company_pattern="CUSTOM",
                drive_start_time=now - timedelta(hours=1),
                drive_end_time=now + timedelta(days=30),
                status=AssessmentStatus.PUBLISHED,
                created_by=comp_admin.id if 'comp_admin' in locals() else None,
            )
            db.add(demo_assessment)
            await db.flush()

            for idx, q in enumerate(seeded_questions):
                db.add(AssessmentQuestion(
                    assessment_id=demo_assessment.id,
                    question_id=q.id,
                    section_name="Backend Core",
                    order_index=idx + 1,
                ))
            await db.flush()

        demo_token = "demo-token-123"
        inv_stmt = select(CandidateInvitation).where(CandidateInvitation.token == demo_token)
        demo_invitation = (await db.execute(inv_stmt)).scalar_one_or_none()

        if not demo_invitation:
            demo_invitation = CandidateInvitation(
                company_id=demo_company.id,
                assessment_id=demo_assessment.id,
                candidate_id=cand_profile.id if cand_profile else None,
                candidate_email="candidate@example.com",
                candidate_name="Jane Developer",
                token=demo_token,
                status=InvitationStatus.PENDING,
                expires_at=datetime.now(timezone.utc) + timedelta(days=30),
            )
            db.add(demo_invitation)
            await db.flush()
            print(f"  + Created Demo Invitation Token: {demo_token} (URL: /exam/{demo_token})")
        else:
            print(f"  [OK] Demo Invitation Token Exists: {demo_token}")

        await db.commit()

    print("\n" + "=" * 75)
    print("[SUCCESS] AssessIQ Database Seeding Complete!")
    print("=" * 75)
    print("\nCandidate Assessment Drives Ready to Test:")
    print("  -> TCS iON Pattern: http://localhost:3000/exam/tcs-nqt-demo-token")
    print("  -> Infosys Pattern: http://localhost:3000/exam/infosys-demo-token")
    print("  -> Full-Stack Drive: http://localhost:3000/exam/demo-token-123")
    print("=" * 75)


if __name__ == "__main__":
    asyncio.run(seed_data())
