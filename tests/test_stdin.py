from runner.sandbox import run_python_submission

code = """
a, b = map(int, input().split())
print(a + b)
"""

result = run_python_submission(code, stdin_data="3 4\n")
print(result)
assert result["exit_code"] == 0, f"expected exit 0, got {result}"
assert result["stdout"].strip() == "7", f"expected '7', got {result['stdout']!r}"
print("STDIN TEST PASSED")
