import uuid

from runner.judge import judge_submission
from runner.persistence import save_test_case_results, get_test_case_results


def test_persistence_round_trip():
    submission_id = str(uuid.uuid4())

    code = "print(sum(map(int, input().split())))"
    test_cases = [
        {"stdin": "3 4", "expected_output": "7"},
        {"stdin": "1 1", "expected_output": "99"},  # deliberately wrong
    ]

    judge_result = judge_submission(code, test_cases, language="python")
    save_test_case_results(submission_id, judge_result)

    fetched = get_test_case_results(submission_id)

    assert len(fetched) == 2
    assert fetched[0]["verdict"] == "ACCEPTED"
    assert fetched[1]["verdict"] == "WRONG_ANSWER"
    assert fetched[0]["stdout"].strip() == "7"
