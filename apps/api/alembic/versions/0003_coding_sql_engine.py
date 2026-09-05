"""Alembic migration – create Phase 3 tables (Coding & SQL Sandbox Engine).
"""

from alembic import op
import sqlalchemy as sa
import sqlalchemy.dialects.postgresql as pg

# revision identifiers, used by Alembic.
revision = "0003_coding_sql_engine"
down_revision = "0002_assessment_engine"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Coding Problems
    op.create_table(
        "coding_problems",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("company_id", sa.Uuid(), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=True, index=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=100), nullable=False, index=True),
        sa.Column("description_markdown", sa.Text(), nullable=False),
        sa.Column("difficulty", sa.String(length=50), server_default="MEDIUM", nullable=False),
        sa.Column("time_limit_ms", sa.Integer(), server_default=sa.text("2000"), nullable=False),
        sa.Column("memory_limit_mb", sa.Integer(), server_default=sa.text("256"), nullable=False),
        sa.Column("starter_code", sa.JSON(), nullable=False),
        sa.Column("solution_code", sa.JSON(), nullable=True),
        sa.Column("points", sa.Float(), server_default=sa.text("10.0"), nullable=False),
        sa.Column("tags", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )

    # 2. Coding Test Cases
    op.create_table(
        "coding_test_cases",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("problem_id", sa.Uuid(), sa.ForeignKey("coding_problems.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("input_data", sa.Text(), nullable=False),
        sa.Column("expected_output", sa.Text(), nullable=False),
        sa.Column("is_hidden", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("order_index", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    # 3. SQL Problems
    op.create_table(
        "sql_problems",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("company_id", sa.Uuid(), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=True, index=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=100), nullable=False, index=True),
        sa.Column("description_markdown", sa.Text(), nullable=False),
        sa.Column("difficulty", sa.String(length=50), server_default="MEDIUM", nullable=False),
        sa.Column("schema_sql", sa.Text(), nullable=False),
        sa.Column("solution_sql", sa.Text(), nullable=False),
        sa.Column("points", sa.Float(), server_default=sa.text("10.0"), nullable=False),
        sa.Column("tags", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )

    # 4. Candidate Code Submissions
    op.create_table(
        "candidate_code_submissions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("attempt_id", sa.Uuid(), sa.ForeignKey("assessment_attempts.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("problem_id", sa.Uuid(), sa.ForeignKey("coding_problems.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("language", sa.String(length=50), server_default="python", nullable=False),
        sa.Column("code", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=50), server_default="PENDING", nullable=False),
        sa.Column("passed_test_cases", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("total_test_cases", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("execution_time_ms", sa.Float(), server_default=sa.text("0.0"), nullable=False),
        sa.Column("output_logs", sa.Text(), nullable=True),
        sa.Column("score_awarded", sa.Float(), server_default=sa.text("0.0"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    # 5. Candidate SQL Submissions
    op.create_table(
        "candidate_sql_submissions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("attempt_id", sa.Uuid(), sa.ForeignKey("assessment_attempts.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("problem_id", sa.Uuid(), sa.ForeignKey("sql_problems.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("query", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=50), server_default="PENDING", nullable=False),
        sa.Column("execution_time_ms", sa.Float(), server_default=sa.text("0.0"), nullable=False),
        sa.Column("output_preview", sa.Text(), nullable=True),
        sa.Column("score_awarded", sa.Float(), server_default=sa.text("0.0"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("candidate_sql_submissions")
    op.drop_table("candidate_code_submissions")
    op.drop_table("sql_problems")
    op.drop_table("coding_test_cases")
    op.drop_table("coding_problems")
