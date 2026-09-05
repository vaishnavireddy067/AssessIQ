"""
Test Suite for Sandboxed Code Execution Engine (Python & JavaScript).
"""
import pytest
from core.sandbox.code_runner import (
    CodeLanguage, ExecutionStatus, execute_single_run, run_code_against_test_cases
)


@pytest.mark.asyncio
async def test_python_code_execution_success():
    code = """
import sys
data = sys.stdin.read().strip()
nums = [int(x) for x in data.split()]
print(sum(nums))
"""
    returncode, stdout, stderr, elapsed_ms = await execute_single_run(
        language=CodeLanguage.PYTHON,
        code=code,
        input_data="10 20 30",
        time_limit_ms=2000,
    )
    assert returncode == 0
    assert stdout.strip() == "60"
    assert elapsed_ms > 0


@pytest.mark.asyncio
async def test_python_code_execution_timeout():
    infinite_loop_code = """
import time
while True:
    time.sleep(0.1)
"""
    returncode, stdout, stderr, elapsed_ms = await execute_single_run(
        language=CodeLanguage.PYTHON,
        code=infinite_loop_code,
        input_data="",
        time_limit_ms=500,  # 500ms max timeout
    )
    assert returncode == -1  # Timed out
    assert "Timed Out" in stderr


@pytest.mark.asyncio
async def test_run_code_against_test_cases_all_pass():
    # Two Sum solution reading from stdin: target on line 1, space-separated nums on line 2
    code = """
import sys
lines = sys.stdin.read().strip().splitlines()
if len(lines) >= 2:
    target = int(lines[0])
    nums = [int(x) for x in lines[1].split()]
    seen = {}
    ans = []
    for i, num in enumerate(nums):
        comp = target - num
        if comp in seen:
            ans = [seen[comp], i]
            break
        seen[num] = i
    print(f"{ans[0]} {ans[1]}")
"""
    test_cases = [
        {"id": "tc1", "input_data": "9\n2 7 11 15", "expected_output": "0 1", "is_hidden": False},
        {"id": "tc2", "input_data": "6\n3 2 4", "expected_output": "1 2", "is_hidden": False},
        {"id": "tc3", "input_data": "6\n3 3", "expected_output": "0 1", "is_hidden": True},
    ]

    summary = await run_code_against_test_cases(
        language=CodeLanguage.PYTHON,
        code=code,
        test_cases=test_cases,
        time_limit_ms=2000,
    )

    assert summary.status == ExecutionStatus.ACCEPTED
    assert summary.total_test_cases == 3
    assert summary.passed_test_cases == 3
    assert len(summary.test_case_results) == 3


@pytest.mark.asyncio
async def test_run_code_against_test_cases_wrong_answer():
    wrong_code = """
print("wrong output")
"""
    test_cases = [
        {"id": "tc1", "input_data": "1", "expected_output": "2", "is_hidden": False},
    ]
    summary = await run_code_against_test_cases(
        language=CodeLanguage.PYTHON,
        code=wrong_code,
        test_cases=test_cases,
        time_limit_ms=2000,
    )
    assert summary.status == ExecutionStatus.WRONG_ANSWER
    assert summary.passed_test_cases == 0
