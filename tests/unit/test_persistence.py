from sqlalchemy import select

from app.core.db_sync import SyncSessionLocal
from app.models import User, Problem, Submission
from runner.judge import judge_submission
from runner.persistence import save_test_case_results, get_test_case_results


def _get_or_create_fixtures(session):
    user = session.execute(
        select(User).where(User.username == "pytest_fixture_user")
    ).scalar_one_or_none()
    if user is None:
        user = User(
            username="pytest_fixture_user",
            email="pytest_fixture@example.com",
            password_hash="not-a-real-hash",
        )
        session.add(user)
        session.flush()

    problem = session.execute(
        select(Problem).where(Problem.slug == "pytest-fixture-problem")
    ).scalar_one_or_none()
    if problem is None:
        problem = Problem(
            slug="pytest-fixture-problem",
            title="Pytest Fixture Problem",
            statement="Used only by the persistence test.",
            version=1,
        )
        session.add(problem)
        session.flush()

    return user, problem


def test_persistence_round_trip():
    session = SyncSessionLocal()
    try:
        user, problem = _get_or_create_fixtures(session)

        submission = Submission(
            user_id=user.id,
            problem_id=problem.id,
            problem_version=problem.version,
            language="python",
            source_code="print('test')",
            overall_verdict=None,
        )
        session.add(submission)
        session.commit()
        submission_id = str(submission.id)
    finally:
        session.close()

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
