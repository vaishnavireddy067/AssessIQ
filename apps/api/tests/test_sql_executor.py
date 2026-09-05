"""
Test Suite for SQL Sandbox Execution & Verification Engine.
"""
import pytest
from core.sandbox.sql_runner import execute_sqlite_query, verify_sql_solution, SqlStatus


SCHEMA_SQL = """
CREATE TABLE employees (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    department TEXT NOT NULL,
    salary INTEGER NOT NULL
);

INSERT INTO employees (id, name, department, salary) VALUES
(1, 'Alice', 'Engineering', 90000),
(2, 'Bob', 'Engineering', 85000),
(3, 'Charlie', 'Marketing', 65000),
(4, 'Diana', 'Marketing', 70000),
(5, 'Evan', 'Sales', 60000);
"""


def test_sql_execution_success():
    query = "SELECT department, AVG(salary) as avg_sal FROM employees GROUP BY department ORDER BY avg_sal DESC;"
    ok, result, err = execute_sqlite_query(SCHEMA_SQL, query)
    assert ok is True
    assert result.row_count == 3
    assert "avg_sal" in [c.lower() for c in result.columns]
    assert result.rows[0]["department"] == "Engineering"


def test_sql_execution_syntax_error():
    broken_query = "SELEC * FROM employees"
    ok, result, err = execute_sqlite_query(SCHEMA_SQL, broken_query)
    assert ok is False
    assert err is not None


def test_sql_solution_verification_accepted():
    candidate_query = """
    SELECT department, COUNT(*) as count 
    FROM employees 
    GROUP BY department 
    HAVING COUNT(*) > 1 
    ORDER BY count DESC;
    """
    solution_query = """
    SELECT department, COUNT(*) as count 
    FROM employees 
    GROUP BY department 
    HAVING COUNT(*) > 1 
    ORDER BY count DESC;
    """

    summary = verify_sql_solution(SCHEMA_SQL, candidate_query, solution_query)
    assert summary.status == SqlStatus.ACCEPTED
    assert summary.passed is True
    assert summary.candidate_result.row_count == 2


def test_sql_solution_verification_wrong_output():
    wrong_candidate_query = "SELECT department, COUNT(*) as count FROM employees GROUP BY department;"
    solution_query = "SELECT department, COUNT(*) as count FROM employees GROUP BY department HAVING COUNT(*) > 1;"

    summary = verify_sql_solution(SCHEMA_SQL, wrong_candidate_query, solution_query)
    assert summary.status == SqlStatus.WRONG_OUTPUT
    assert summary.passed is False
