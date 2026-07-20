import os
import json

from celery import Celery
import redis as redis_sync
from sqlalchemy import select

from app.core.db_sync import SyncSessionLocal
from app.models import Submission, TestCase
from runner.judge import judge_submission
from runner.persistence import save_test_case_results

broker_url = os.environ.get("CELERY_BROKER_URL", "redis://redis:6379/0")
celery_app = Celery("devmentor", broker=broker_url, backend=broker_url)

UPDATES_CHANNEL = "submission_updates"


@celery_app.task(name="judge_submission_task")
def judge_submission_task(submission_id: str):
    session = SyncSessionLocal()
    try:
        submission = session.get(Submission, submission_id)
        if submission is None:
            return {"error": "submission not found"}

        # Grading always uses ALL test cases (sample + hidden), unlike
        # the public problem-detail endpoint which only shows samples.
        test_case_rows = (
            session.execute(select(TestCase).where(TestCase.problem_id == submission.problem_id))
            .scalars()
            .all()
        )
        test_cases = [
            {"stdin": tc.stdin, "expected_output": tc.expected_output} for tc in test_case_rows
        ]

        result = judge_submission(submission.source_code, test_cases, language=submission.language)

        submission.overall_verdict = result["overall_verdict"]
        session.commit()

        # Reuses the exact persistence function we already built and
        # tested standalone -- no new persistence logic here.
        save_test_case_results(str(submission.id), result)

        # Notify anyone connected via WebSocket. judge-worker can't touch
        # the api container's live socket directly, so this goes through
        # Redis pub/sub -- the api process subscribes to this channel and
        # forwards it to the right connection.
        r = redis_sync.Redis.from_url(broker_url)
        r.publish(
            UPDATES_CHANNEL,
            json.dumps({"submission_id": str(submission.id), "overall_verdict": result["overall_verdict"]}),
        )

        return {"overall_verdict": result["overall_verdict"]}
    finally:
        session.close()
