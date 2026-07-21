import os
import uuid
import logging

from celery import Celery
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import get_current_user
from app.models import Problem, Submission, User
from app.schemas import SubmissionCreate, SubmissionOut

logger = logging.getLogger("api")
router = APIRouter(prefix="/submissions", tags=["submissions"])

ALLOWED_LANGUAGES = {"python", "cpp", "java"}

# A lightweight client purely for publishing jobs onto the queue -- this
# is the ONLY Celery-related object the api container needs. It never
# imports app.tasks, runner/, or the docker SDK: only judge-worker does.
_celery_client = Celery(broker=os.environ.get("CELERY_BROKER_URL", "redis://redis:6379/0"))


@router.post("", response_model=SubmissionOut, status_code=status.HTTP_202_ACCEPTED)
async def create_submission(
    payload: SubmissionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if payload.language not in ALLOWED_LANGUAGES:
        raise HTTPException(
            status_code=400, detail=f"language must be one of {sorted(ALLOWED_LANGUAGES)}"
        )

    result = await db.execute(select(Problem).where(Problem.slug == payload.problem_slug))
    problem = result.scalar_one_or_none()
    if problem is None:
        raise HTTPException(status_code=404, detail="Problem not found")

    submission = Submission(
        user_id=current_user.id,
        problem_id=problem.id,
        problem_version=problem.version,  # snapshot at submit time
        language=payload.language,
        source_code=payload.source_code,
        overall_verdict=None,  # pending until judge-worker picks it up
    )
    db.add(submission)
    await db.commit()
    await db.refresh(submission)

    # Enqueue by NAME -- doesn't require importing the task function.
    # This is the actual "returns immediately" behavior: publishing to
    # Redis is fast, we don't wait for judging.
    _celery_client.send_task("judge_submission_task", args=[str(submission.id)])

    logger.info(
        "submission accepted",
        extra={
            "submission_id": str(submission.id),
            "language": submission.language,
        },
    )

    return submission


@router.get("/{submission_id}")
async def get_submission(
    submission_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Submission).where(Submission.id == submission_id))
    submission = result.scalar_one_or_none()
    if submission is None:
        raise HTTPException(status_code=404, detail="Submission not found")
    if submission.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized to view this submission")

    # Raw query against test_case_results -- it's not an Alembic-managed
    # ORM table (known schema-drift item from earlier), so this reads it
    # directly rather than through a model.
    tc_result = await db.execute(
        text(
            """
            SELECT test_case_index, verdict, stdout, stderr, exit_code,
                   runtime_seconds, timed_out, compile_error
            FROM test_case_results
            WHERE submission_id = :sid
            ORDER BY test_case_index
            """
        ),
        {"sid": str(submission_id)},
    )
    columns = tc_result.keys()
    test_case_results = [dict(zip(columns, row)) for row in tc_result.fetchall()]

    return {
        "id": str(submission.id),
        "problem_id": str(submission.problem_id),
        "language": submission.language,
        "overall_verdict": submission.overall_verdict,
        "problem_version": submission.problem_version,
        "test_case_results": test_case_results,
    }
