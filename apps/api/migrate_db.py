"""
Comprehensive SQLite migration for AssessIQ.
Adds every column that exists in SQLAlchemy models but was missing from the old DB.
Safe to run multiple times (skips if column already exists).
"""
import sqlite3

DB_PATH = "assessiq.db"

MIGRATIONS = [
    # ── assessments (Phase 8: company pattern + drive window + sections)
    "ALTER TABLE assessments ADD COLUMN company_pattern TEXT NOT NULL DEFAULT 'CUSTOM'",
    "ALTER TABLE assessments ADD COLUMN drive_start_time TIMESTAMP",
    "ALTER TABLE assessments ADD COLUMN drive_end_time TIMESTAMP",
    "ALTER TABLE assessments ADD COLUMN sections_config TEXT",
    "ALTER TABLE assessments ADD COLUMN allow_section_switching BOOLEAN NOT NULL DEFAULT 1",

    # ── assessment_questions (Phase 8: section name per question)
    "ALTER TABLE assessment_questions ADD COLUMN section_name TEXT DEFAULT 'General'",

    # ── assessment_attempts (Phase 9: AI ranking rationale)
    "ALTER TABLE assessment_attempts ADD COLUMN ai_ranking_rationale TEXT",

    # ── candidate_invitations (no new fields needed, but added for safety)

    # ── questions (Phase 9: Leak Radar)
    "ALTER TABLE questions ADD COLUMN usage_count INTEGER NOT NULL DEFAULT 0",
    "ALTER TABLE questions ADD COLUMN leak_risk_score REAL NOT NULL DEFAULT 0.0",
    "ALTER TABLE questions ADD COLUMN leak_last_checked_at TIMESTAMP",
    "ALTER TABLE questions ADD COLUMN is_suspected_leaked BOOLEAN NOT NULL DEFAULT 0",

    # ── companies (Phase 8 enterprise fields)
    "ALTER TABLE companies ADD COLUMN domain TEXT",
    "ALTER TABLE companies ADD COLUMN logo_url TEXT",
    "ALTER TABLE companies ADD COLUMN website TEXT",
    "ALTER TABLE companies ADD COLUMN industry TEXT",
    "ALTER TABLE companies ADD COLUMN size_bucket TEXT",
    "ALTER TABLE companies ADD COLUMN plan_tier TEXT NOT NULL DEFAULT 'FREE'",
    "ALTER TABLE companies ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT 1",

    # ── candidates (Phase 9: skill passport / consent)
    "ALTER TABLE candidates ADD COLUMN resume_url TEXT",
    "ALTER TABLE candidates ADD COLUMN linkedin_url TEXT",
    "ALTER TABLE candidates ADD COLUMN github_url TEXT",
    "ALTER TABLE candidates ADD COLUMN skills TEXT",
    "ALTER TABLE candidates ADD COLUMN experience_years INTEGER",
    "ALTER TABLE candidates ADD COLUMN education TEXT",
    "ALTER TABLE candidates ADD COLUMN consent_given BOOLEAN NOT NULL DEFAULT 0",
    "ALTER TABLE candidates ADD COLUMN consent_given_at TIMESTAMP",
    "ALTER TABLE candidates ADD COLUMN gdpr_erasure_requested BOOLEAN NOT NULL DEFAULT 0",
]

def run():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    ok_count = 0
    skip_count = 0
    for sql in MIGRATIONS:
        try:
            cursor.execute(sql)
            print(f"  OK   : {sql[:80]}")
            ok_count += 1
        except sqlite3.OperationalError as e:
            print(f"  SKIP : {e}")
            skip_count += 1
    conn.commit()
    conn.close()
    print(f"\nMigration complete. Applied: {ok_count}  Already existed: {skip_count}")

if __name__ == "__main__":
    run()
