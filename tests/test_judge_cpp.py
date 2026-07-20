from runner.judge import judge_single_case, judge_submission


def test_cpp_accepted():
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
    print("ACCEPTED case:", result["verdict"], result["stdout"])
    assert result["verdict"] == "ACCEPTED"


def test_cpp_compile_error():
    code = """
#include <iostream>
int main() {
    this is not valid c++ at all
}
"""
    result = judge_single_case(code, stdin_data="", expected_output="anything", language="cpp")
    print("COMPILE_ERROR case:", result["verdict"], result["stderr"][:100])
    assert result["verdict"] == "COMPILE_ERROR"


def test_cpp_runtime_error():
    code = """
#include <iostream>
int main() {
    int* p = nullptr;
    *p = 1;  // segfault
    return 0;
}
"""
    result = judge_single_case(code, stdin_data="", expected_output="anything", language="cpp")
    print("RUNTIME_ERROR case:", result["verdict"], "exit_code:", result["exit_code"])
    assert result["verdict"] == "RUNTIME_ERROR"


def test_cpp_tle():
    code = """
int main() {
    while (true) {}
}
"""
    result = judge_single_case(
        code, stdin_data="", expected_output="anything", language="cpp", timeout_seconds=2
    )
    print("TLE case:", result["verdict"], result["runtime_seconds"])
    assert result["verdict"] == "TIME_LIMIT_EXCEEDED"


def test_cpp_multi_case_compile_error_short_circuits():
    code = "int main() { this is broken }"
    test_cases = [
        {"stdin": "1 1", "expected_output": "2"},
        {"stdin": "2 2", "expected_output": "4"},
    ]
    result = judge_submission(code, test_cases, language="cpp")
    print("Overall verdict:", result["overall_verdict"])
    for r in result["test_case_results"]:
        print(f"  case {r['test_case_index']}: {r['verdict']}")
    assert result["overall_verdict"] == "COMPILE_ERROR"
    assert all(r["verdict"] == "COMPILE_ERROR" for r in result["test_case_results"])


if __name__ == "__main__":
    test_cpp_accepted()
    test_cpp_compile_error()
    test_cpp_runtime_error()
    test_cpp_tle()
    test_cpp_multi_case_compile_error_short_circuits()
    print("\nALL C++ JUDGE TESTS PASSED")
