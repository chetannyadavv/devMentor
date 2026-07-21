"""
Unit tests for judge verdict logic (C++). Compile errors are the case
Python doesn't have, so this is genuinely separate coverage, not a
copy-paste of the Python tests.
"""
from runner.judge import judge_single_case, judge_submission


def test_accepted():
    code = """
#include <iostream>
int main() {
    int a, b;
    std::cin >> a >> b;
    std::cout << a + b << std::endl;
    return 0;
}
"""
    result = judge_single_case(code, stdin_data="3 4", expected_output="7", language="cpp")
    assert result["verdict"] == "ACCEPTED"


def test_compile_error():
    code = """
#include <iostream>
int main() {
    this is not valid c++ at all
}
"""
    result = judge_single_case(code, stdin_data="", expected_output="anything", language="cpp")
    assert result["verdict"] == "COMPILE_ERROR"


def test_runtime_error():
    code = """
#include <iostream>
int main() {
    int* p = nullptr;
    *p = 1;
    return 0;
}
"""
    result = judge_single_case(code, stdin_data="", expected_output="anything", language="cpp")
    assert result["verdict"] == "RUNTIME_ERROR"


def test_multi_case_compile_error_short_circuits():
    code = "int main() { this is broken }"
    test_cases = [
        {"stdin": "1 1", "expected_output": "2"},
        {"stdin": "2 2", "expected_output": "4"},
    ]
    result = judge_submission(code, test_cases, language="cpp")
    assert result["overall_verdict"] == "COMPILE_ERROR"
    assert all(r["verdict"] == "COMPILE_ERROR" for r in result["test_case_results"])
