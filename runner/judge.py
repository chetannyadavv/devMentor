from runner.sandbox import run_python_submission, run_cpp_submission, run_java_submission


def normalize_output(text: str) -> str:
    """
    Matches how most real judges compare output: trailing whitespace on
    each line doesn't matter, and trailing blank lines at the end don't
    matter. Everything else does.
    """
    lines = text.replace("\r\n", "\n").split("\n")
    lines = [line.rstrip() for line in lines]
    while lines and lines[-1] == "":
        lines.pop()
    return "\n".join(lines)


RUNNERS = {
    "python": run_python_submission,
    "cpp": run_cpp_submission,
    "java": run_java_submission,
}

COMPILED_LANGUAGES = {"cpp", "java"}


def judge_single_case(
    source_code: str, stdin_data: str, expected_output: str, language: str = "python", **kwargs
) -> dict:
    run_fn = RUNNERS[language]
    run_result = run_fn(source_code, stdin_data=stdin_data, **kwargs)

    if run_result.get("compile_error"):
        verdict = "COMPILE_ERROR"
    elif run_result["timed_out"]:
        verdict = "TIME_LIMIT_EXCEEDED"
    elif run_result["exit_code"] != 0:
        verdict = "RUNTIME_ERROR"
    elif normalize_output(run_result["stdout"]) == normalize_output(expected_output):
        verdict = "ACCEPTED"
    else:
        verdict = "WRONG_ANSWER"

    return {
        "verdict": verdict,
        **run_result,
    }


def judge_submission(source_code: str, test_cases: list, language: str = "python", **kwargs) -> dict:
    """
    test_cases: list of {"stdin": str, "expected_output": str}
    For compiled languages, a compile error fails every test case
    immediately, without re-running the (broken) compile per case --
    matches how real judges behave.
    """
    if language in COMPILED_LANGUAGES:
        compile_check = RUNNERS[language](source_code, stdin_data="", **kwargs)
        if compile_check.get("compile_error"):
            results = []
            for i, _ in enumerate(test_cases):
                results.append(
                    {
                        "verdict": "COMPILE_ERROR",
                        "test_case_index": i,
                        "stderr": compile_check["stderr"],
                        "stdout": "",
                        "exit_code": compile_check["exit_code"],
                        "runtime_seconds": compile_check["runtime_seconds"],
                        "timed_out": False,
                        "compile_error": True,
                    }
                )
            return {"overall_verdict": "COMPILE_ERROR", "test_case_results": results}

    results = []
    for i, case in enumerate(test_cases):
        result = judge_single_case(
            source_code,
            stdin_data=case["stdin"],
            expected_output=case["expected_output"],
            language=language,
            **kwargs,
        )
        result["test_case_index"] = i
        results.append(result)

    overall = "ACCEPTED" if all(r["verdict"] == "ACCEPTED" for r in results) else "FAILED"

    return {
        "overall_verdict": overall,
        "test_case_results": results,
    }
