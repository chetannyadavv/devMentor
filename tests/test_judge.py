from runner.judge import judge_single_case, judge_submission, normalize_output


def test_normalize():
    assert normalize_output("7\n") == normalize_output("7")
    assert normalize_output("7 \n") == normalize_output("7")
    assert normalize_output("7\n\n\n") == normalize_output("7")
    assert normalize_output("7") != normalize_output("70")
    assert normalize_output("line1\nline2") == normalize_output("line1 \nline2\n")
    print("normalize_output tests PASSED")


def test_accepted():
    code = "print(sum(map(int, input().split())))"
    result = judge_single_case(code, stdin_data="3 4", expected_output="7\n")
    print("ACCEPTED case:", result["verdict"], result["stdout"])
    assert result["verdict"] == "ACCEPTED"


def test_wrong_answer():
    code = "print(999)"
    result = judge_single_case(code, stdin_data="3 4", expected_output="7\n")
    print("WRONG_ANSWER case:", result["verdict"], result["stdout"])
    assert result["verdict"] == "WRONG_ANSWER"


def test_runtime_error():
    code = "raise ValueError('boom')"
    result = judge_single_case(code, stdin_data="", expected_output="anything")
    print("RUNTIME_ERROR case:", result["verdict"], result["stderr"][:80])
    assert result["verdict"] == "RUNTIME_ERROR"


def test_tle():
    code = "while True: pass"
    result = judge_single_case(code, stdin_data="", expected_output="anything", timeout_seconds=2)
    print("TLE case:", result["verdict"], result["runtime_seconds"])
    assert result["verdict"] == "TIME_LIMIT_EXCEEDED"


def test_multi_case_submission():
    code = "print(sum(map(int, input().split())))"
    test_cases = [
        {"stdin": "3 4", "expected_output": "7"},
        {"stdin": "10 20", "expected_output": "30"},
        {"stdin": "1 1", "expected_output": "99"},  # deliberately wrong
    ]
    result = judge_submission(code, test_cases)
    print("Overall verdict:", result["overall_verdict"])
    for r in result["test_case_results"]:
        print(f"  case {r['test_case_index']}: {r['verdict']}")
    assert result["overall_verdict"] == "FAILED"
    assert result["test_case_results"][0]["verdict"] == "ACCEPTED"
    assert result["test_case_results"][1]["verdict"] == "ACCEPTED"
    assert result["test_case_results"][2]["verdict"] == "WRONG_ANSWER"


if __name__ == "__main__":
    test_normalize()
    test_accepted()
    test_wrong_answer()
    test_runtime_error()
    test_tle()
    test_multi_case_submission()
    print("\nALL JUDGE TESTS PASSED")
