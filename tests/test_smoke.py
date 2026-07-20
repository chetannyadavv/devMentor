from runner.sandbox import run_python_submission

result = run_python_submission("print('hello from sandbox')")
print(result)
assert result["exit_code"] == 0
assert "hello from sandbox" in result["stdout"]
assert result["timed_out"] is False
print("SMOKE TEST PASSED")
