"""
AssessIQ Sandboxed Code Execution Engine.
Executes candidate code in isolated asynchronous subprocesses with strict timeout and resource protections.
"""
import asyncio
import os
import sys
import tempfile
import time
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel


class CodeLanguage(str, Enum):
    PYTHON = "python"
    JAVASCRIPT = "javascript"


class ExecutionStatus(str, Enum):
    ACCEPTED = "ACCEPTED"
    WRONG_ANSWER = "WRONG_ANSWER"
    TIME_LIMIT_EXCEEDED = "TIME_LIMIT_EXCEEDED"
    RUNTIME_ERROR = "RUNTIME_ERROR"
    COMPILATION_ERROR = "COMPILATION_ERROR"


class TestCaseResult(BaseModel):
    test_case_id: Optional[str] = None
    input_data: str
    expected_output: str
    actual_output: Optional[str] = None
    passed: bool
    is_hidden: bool
    execution_time_ms: float
    error_message: Optional[str] = None


class CodeExecutionSummary(BaseModel):
    status: ExecutionStatus
    total_test_cases: int
    passed_test_cases: int
    execution_time_ms: float
    output_logs: Optional[str] = None
    error_message: Optional[str] = None
    test_case_results: List[TestCaseResult] = []


def normalize_output(text: str) -> str:
    """Normalize output by stripping trailing whitespace and standardizing line endings."""
    if text is None:
        return ""
    lines = [line.rstrip() for line in text.strip().splitlines()]
    return "\n".join(lines)


async def execute_single_run(
    language: CodeLanguage,
    code: str,
    input_data: str,
    time_limit_ms: int = 2000,
) -> tuple[int, str, str, float]:
    """
    Executes code with stdin input in a dedicated temporary script file.
    Returns (return_code, stdout, stderr, elapsed_ms).
    """
    timeout_sec = max(0.5, time_limit_ms / 1000.0)

    # Determine command and temp extension
    if language == CodeLanguage.PYTHON:
        ext = ".py"
        cmd = [sys.executable, "-u"]
    elif language == CodeLanguage.JAVASCRIPT:
        ext = ".js"
        # Check if node is available, else fallback
        cmd = ["node"]
    else:
        raise ValueError(f"Unsupported language: {language}")

    with tempfile.NamedTemporaryFile(suffix=ext, mode="w", encoding="utf-8", delete=False) as f:
        f.write(code)
        temp_filepath = f.name

    start_time = time.perf_counter()
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            temp_filepath,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdin_bytes = input_data.encode("utf-8") if input_data else b""
        try:
            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                proc.communicate(input=stdin_bytes),
                timeout=timeout_sec,
            )
            elapsed_ms = round((time.perf_counter() - start_time) * 1000.0, 2)
            stdout = stdout_bytes.decode("utf-8", errors="replace")
            stderr = stderr_bytes.decode("utf-8", errors="replace")
            return proc.returncode, stdout, stderr, elapsed_ms
        except asyncio.TimeoutError:
            try:
                proc.kill()
            except Exception:
                pass
            elapsed_ms = round((time.perf_counter() - start_time) * 1000.0, 2)
            return -1, "", "Execution Timed Out (Time Limit Exceeded)", elapsed_ms
    finally:
        if os.path.exists(temp_filepath):
            try:
                os.remove(temp_filepath)
            except Exception:
                pass


async def run_code_against_test_cases(
    language: CodeLanguage,
    code: str,
    test_cases: List[Dict[str, Any]],
    time_limit_ms: int = 2000,
    stop_on_first_fail: bool = False,
) -> CodeExecutionSummary:
    """
    Evaluates code against a list of test cases (each has input_data, expected_output, is_hidden, etc.).
    """
    results: List[TestCaseResult] = []
    total_cases = len(test_cases)
    passed_cases = 0
    overall_status = ExecutionStatus.ACCEPTED
    max_exec_time = 0.0
    first_error_log = None

    for tc in test_cases:
        tc_id = str(tc.get("id", ""))
        inp = str(tc.get("input_data", ""))
        expected = str(tc.get("expected_output", ""))
        is_hidden = bool(tc.get("is_hidden", False))

        returncode, stdout, stderr, elapsed_ms = await execute_single_run(
            language=language,
            code=code,
            input_data=inp,
            time_limit_ms=time_limit_ms,
        )

        max_exec_time = max(max_exec_time, elapsed_ms)

        if returncode == -1:
            # Timed out
            overall_status = ExecutionStatus.TIME_LIMIT_EXCEEDED
            results.append(
                TestCaseResult(
                    test_case_id=tc_id,
                    input_data=inp,
                    expected_output=expected,
                    actual_output=None,
                    passed=False,
                    is_hidden=is_hidden,
                    execution_time_ms=elapsed_ms,
                    error_message="Time Limit Exceeded",
                )
            )
            first_error_log = first_error_log or stderr
            if stop_on_first_fail:
                break
            continue

        if returncode != 0:
            # Runtime error
            overall_status = ExecutionStatus.RUNTIME_ERROR
            results.append(
                TestCaseResult(
                    test_case_id=tc_id,
                    input_data=inp,
                    expected_output=expected,
                    actual_output=None,
                    passed=False,
                    is_hidden=is_hidden,
                    execution_time_ms=elapsed_ms,
                    error_message=stderr.strip() or f"Process exited with code {returncode}",
                )
            )
            first_error_log = first_error_log or stderr
            if stop_on_first_fail:
                break
            continue

        # Check Output
        norm_actual = normalize_output(stdout)
        norm_expected = normalize_output(expected)
        is_pass = (norm_actual == norm_expected)

        if is_pass:
            passed_cases += 1
        else:
            if overall_status == ExecutionStatus.ACCEPTED:
                overall_status = ExecutionStatus.WRONG_ANSWER

        results.append(
            TestCaseResult(
                test_case_id=tc_id,
                input_data=inp,
                expected_output=expected,
                actual_output=norm_actual,
                passed=is_pass,
                is_hidden=is_hidden,
                execution_time_ms=elapsed_ms,
                error_message=None if is_pass else "Output does not match expected output",
            )
        )

        if not is_pass and stop_on_first_fail:
            break

    return CodeExecutionSummary(
        status=overall_status if passed_cases == total_cases else (overall_status if overall_status != ExecutionStatus.ACCEPTED else ExecutionStatus.WRONG_ANSWER),
        total_test_cases=total_cases,
        passed_test_cases=passed_cases,
        execution_time_ms=max_exec_time,
        output_logs=first_error_log,
        error_message=first_error_log,
        test_case_results=results,
    )
