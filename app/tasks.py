import os
import json
import logging
import time

from celery import Celery
from celery.signals import setup_logging
import redis as redis_sync
from sqlalchemy import select

from app.core.db_sync import SyncSessionLocal
from app.core.logging_config import configure_logging
from app.metrics import submissions_total, judge_duration_seconds, active_sandboxes
from app.models import Submission, TestCase
from runner.judge import judge_submission
from runner.persistence import save_test_case_results


@setup_logging.connect
def on_setup_logging(**kwargs):
    # Celery runs its OWN logging setup during worker bootstrap, which
    # happens after this module is imported -- without this signal
    # override, Celery's default setup silently clobbers whatever
    # configure_logging() did. Connecting here makes Celery skip its
    # own setup and defer to ours entirely (documented Celery pattern).
    configure_logging()


logger = logging.getLogger("judge")

broker_url = os.environ.get("CELERY_BROKER_URL", "redis://redis:6379/0")
celery_app = Celery("devmentor", broker=broker_url, backend=broker_url)

UPDATES_CHANNEL = "submission_updates"


@celery_app.task(name="judge_submission_task")
def judge_submission_task(submission_id: str):
    session = SyncSessionLocal()
    try:
        submission = session.get(Submission, submission_id)
        if submission is None:
            logger.warning("submission not found", extra={"submission_id": submission_id})
            return {"error": "submission not found"}

        logger.info(
            "judging started",
            extra={"submission_id": submission_id, "language": submission.language},
        )

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

        # NOTE: this counts "a judging operation is in flight" as one
        # active sandbox -- an approximation, since judge_submission()
        # actually runs one container per test case sequentially, not
        # one container for the whole call. A fully precise per-
        # container count would mean instrumenting runner/sandbox.py
        # itself, which we've deliberately kept dependency-free so it
        # still runs standalone on the host without needing
        # prometheus_client installed there.
        active_sandboxes.inc()
        start = time.monotonic()
        try:
            result = judge_submission(submission.source_code, test_cases, language=submission.language)
        finally:
            duration = time.monotonic() - start
            active_sandboxes.dec()

        submission.overall_verdict = result["overall_verdict"]
        session.commit()

        save_test_case_results(str(submission.id), result)

        submissions_total.labels(language=submission.language, verdict=result["overall_verdict"]).inc()
        judge_duration_seconds.labels(language=submission.language).observe(duration)

        logger.info(
            "judging finished",
            extra={
                "submission_id": submission_id,
                "language": submission.language,
                "verdict": result["overall_verdict"],
                "duration_seconds": round(duration, 3),
            },
        )

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
