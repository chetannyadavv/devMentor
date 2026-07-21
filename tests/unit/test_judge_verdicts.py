"""
Unit tests for judge verdict logic (Python). Pytest-ified version of
what we already proved by hand.
"""
from runner.judge import judge_single_case, judge_submission, normalize_output


def test_normalize_output_ignores_trailing_whitespace():
    assert normalize_output("7\n") == normalize_output("7")
    assert normalize_output("7 \n") == normalize_output("7")
    assert normalize_output("7\n\n\n") == normalize_output("7")
    assert normalize_output("7") != normalize_output("70")


def test_accepted():
    code = "print(sum(map(int, input().split())))"
    result = judge_single_case(code, stdin_data="3 4", expected_output="7\n")
    assert result["verdict"] == "ACCEPTED"


def test_wrong_answer():
    code = "print(999)"
    result = judge_single_case(code, stdin_data="3 4", expected_output="7\n")
    assert result["verdict"] == "WRONG_ANSWER"


def test_runtime_error():
    code = "raise ValueError('boom')"
    result = judge_single_case(code, stdin_data="", expected_output="anything")
    assert result["verdict"] == "RUNTIME_ERROR"


def test_time_limit_exceeded():
    code = "while True: pass"
    result = judge_single_case(code, stdin_data="", expected_output="anything", timeout_seconds=2)
    assert result["verdict"] == "TIME_LIMIT_EXCEEDED"


def test_multi_case_submission_reports_each_case():
    code = "print(sum(map(int, input().split())))"
    test_cases = [
        {"stdin": "3 4", "expected_output": "7"},
        {"stdin": "10 20", "expected_output": "30"},
        {"stdin": "1 1", "expected_output": "99"},  # deliberately wrong
    ]
    result = judge_submission(code, test_cases)
    assert result["overall_verdict"] == "FAILED"
    assert result["test_case_results"][0]["verdict"] == "ACCEPTED"
    assert result["test_case_results"][1]["verdict"] == "ACCEPTED"
    assert result["test_case_results"][2]["verdict"] == "WRONG_ANSWER"
