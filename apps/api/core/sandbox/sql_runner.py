"""
AssessIQ SQL Query Sandbox & Verification Engine.
Executes candidate SQL queries against isolated in-memory database schemas and grades results against reference solution datasets.
"""
import sqlite3
import time
from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel


class SqlStatus(str, Enum):
    ACCEPTED = "ACCEPTED"
    WRONG_OUTPUT = "WRONG_OUTPUT"
    SYNTAX_ERROR = "SYNTAX_ERROR"
    EXECUTION_ERROR = "EXECUTION_ERROR"


class SqlQueryResult(BaseModel):
    columns: List[str] = []
    rows: List[Dict[str, Any]] = []
    row_count: int = 0
    execution_time_ms: float = 0.0
    error_message: Optional[str] = None


class SqlVerificationSummary(BaseModel):
    status: SqlStatus
    passed: bool
    execution_time_ms: float
    candidate_result: SqlQueryResult
    expected_result: Optional[SqlQueryResult] = None
    error_message: Optional[str] = None


def execute_sqlite_query(schema_sql: str, query: str) -> tuple[bool, SqlQueryResult, Optional[str]]:
    """
    Executes a query against a fresh in-memory SQLite database initialized with schema_sql.
    Returns (success, SqlQueryResult, error_str).
    """
    start_time = time.perf_counter()
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
        # 1. Execute schema initialization (DDL + sample records)
        cursor.executescript(schema_sql)

        # 2. Execute target query
        cursor.execute(query)
        rows_raw = cursor.fetchall()
        elapsed_ms = round((time.perf_counter() - start_time) * 1000.0, 2)

        columns = [description[0] for description in cursor.description] if cursor.description else []
        rows = [dict(r) for r in rows_raw]

        return True, SqlQueryResult(
            columns=columns,
            rows=rows,
            row_count=len(rows),
            execution_time_ms=elapsed_ms,
        ), None
    except Exception as e:
        elapsed_ms = round((time.perf_counter() - start_time) * 1000.0, 2)
        err_msg = str(e)
        return False, SqlQueryResult(execution_time_ms=elapsed_ms, error_message=err_msg), err_msg
    finally:
        conn.close()


def normalize_row_dict(row: Dict[str, Any]) -> Dict[str, str]:
    """Normalize row column keys to lowercase and values to stripped strings."""
    return {str(k).lower().strip(): str(v).strip() if v is not None else "NULL" for k, v in row.items()}


def verify_sql_solution(
    schema_sql: str,
    candidate_query: str,
    solution_query: str,
) -> SqlVerificationSummary:
    """
    Grades candidate SQL query by executing candidate query vs solution query on the same schema.
    """
    # 1. Execute Candidate Query
    cand_ok, cand_res, cand_err = execute_sqlite_query(schema_sql, candidate_query)
    if not cand_ok:
        return SqlVerificationSummary(
            status=SqlStatus.SYNTAX_ERROR if "syntax" in (cand_err or "").lower() else SqlStatus.EXECUTION_ERROR,
            passed=False,
            execution_time_ms=cand_res.execution_time_ms,
            candidate_result=cand_res,
            error_message=cand_err,
        )

    # 2. Execute Reference Solution Query
    sol_ok, sol_res, sol_err = execute_sqlite_query(schema_sql, solution_query)
    if not sol_ok:
        # Schema or solution error in definition
        return SqlVerificationSummary(
            status=SqlStatus.EXECUTION_ERROR,
            passed=False,
            execution_time_ms=cand_res.execution_time_ms,
            candidate_result=cand_res,
            error_message=f"Reference solution execution failed: {sol_err}",
        )

    # 3. Compare Result Sets
    cand_norm_rows = [normalize_row_dict(r) for r in cand_res.rows]
    sol_norm_rows = [normalize_row_dict(r) for r in sol_res.rows]

    # Check Column Counts
    cand_cols = [c.lower().strip() for c in cand_res.columns]
    sol_cols = [c.lower().strip() for c in sol_res.columns]

    if len(cand_cols) != len(sol_cols):
        return SqlVerificationSummary(
            status=SqlStatus.WRONG_OUTPUT,
            passed=False,
            execution_time_ms=cand_res.execution_time_ms,
            candidate_result=cand_res,
            expected_result=sol_res,
            error_message=f"Column count mismatch: Expected {len(sol_cols)} columns ({sol_cols}), got {len(cand_cols)} columns ({cand_cols}).",
        )

    # Check Row Counts
    if len(cand_norm_rows) != len(sol_norm_rows):
        return SqlVerificationSummary(
            status=SqlStatus.WRONG_OUTPUT,
            passed=False,
            execution_time_ms=cand_res.execution_time_ms,
            candidate_result=cand_res,
            expected_result=sol_res,
            error_message=f"Row count mismatch: Expected {len(sol_norm_rows)} rows, but query returned {len(cand_norm_rows)} rows.",
        )

    # Compare Row Content (Order-agnostic or exact check)
    is_exact_match = (cand_norm_rows == sol_norm_rows)
    if not is_exact_match:
        # Try sorted match if queries didn't enforce specific ORDER BY
        cand_sorted = sorted([str(sorted(r.items())) for r in cand_norm_rows])
        sol_sorted = sorted([str(sorted(r.items())) for r in sol_norm_rows])
        is_exact_match = (cand_sorted == sol_sorted)

    if not is_exact_match:
        return SqlVerificationSummary(
            status=SqlStatus.WRONG_OUTPUT,
            passed=False,
            execution_time_ms=cand_res.execution_time_ms,
            candidate_result=cand_res,
            expected_result=sol_res,
            error_message="Query output rows do not match expected dataset.",
        )

    return SqlVerificationSummary(
        status=SqlStatus.ACCEPTED,
        passed=True,
        execution_time_ms=cand_res.execution_time_ms,
        candidate_result=cand_res,
        expected_result=sol_res,
        error_message=None,
    )
