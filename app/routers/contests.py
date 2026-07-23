import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import require_admin
from app.models import Contest, Problem, Submission, User, contest_problems
from app.schemas import ContestCreate, ContestOut, ContestDetail, ContestProblemOut

router = APIRouter(prefix="/contests", tags=["contests"])


def _status_for(contest: Contest, now: datetime) -> str:
    if now < contest.start_time:
        return "upcoming"
    elif now > contest.end_time:
        return "ended"
    else:
        return "active"


@router.post("", response_model=ContestOut, status_code=status.HTTP_201_CREATED)
async def create_contest(
    payload: ContestCreate,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    contest = Contest(title=payload.title, start_time=payload.start_time, end_time=payload.end_time)
    db.add(contest)
    await db.flush()

    if payload.problem_slugs:
        result = await db.execute(select(Problem).where(Problem.slug.in_(payload.problem_slugs)))
        problems = result.scalars().all()
        for problem in problems:
            await db.execute(contest_problems.insert().values(contest_id=contest.id, problem_id=problem.id))

    await db.commit()
    await db.refresh(contest)

    now = datetime.now(timezone.utc)
    return ContestOut(
        id=contest.id,
        title=contest.title,
        start_time=contest.start_time,
        end_time=contest.end_time,
        status=_status_for(contest, now),
    )


@router.get("", response_model=list[ContestOut])
async def list_contests(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Contest))
    contests = result.scalars().all()
    now = datetime.now(timezone.utc)
    return [
        ContestOut(
            id=c.id, title=c.title, start_time=c.start_time, end_time=c.end_time,
            status=_status_for(c, now),
        )
        for c in contests
    ]


@router.get("/{contest_id}", response_model=ContestDetail)
async def get_contest(contest_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    contest = await db.get(Contest, contest_id)
    if contest is None:
        raise HTTPException(status_code=404, detail="Contest not found")

    result = await db.execute(
        select(Problem)
        .join(contest_problems, contest_problems.c.problem_id == Problem.id)
        .where(contest_problems.c.contest_id == contest_id)
    )
    problems = result.scalars().all()
    now = datetime.now(timezone.utc)

    return ContestDetail(
        id=contest.id,
        title=contest.title,
        start_time=contest.start_time,
        end_time=contest.end_time,
        status=_status_for(contest, now),
        problems=[ContestProblemOut(id=p.id, slug=p.slug, title=p.title) for p in problems],
    )


@router.post("/{contest_id}/problems/{slug}", status_code=status.HTTP_204_NO_CONTENT)
async def attach_problem(
    contest_id: uuid.UUID,
    slug: str,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    contest = await db.get(Contest, contest_id)
    if contest is None:
        raise HTTPException(status_code=404, detail="Contest not found")

    result = await db.execute(select(Problem).where(Problem.slug == slug))
    problem = result.scalar_one_or_none()
    if problem is None:
        raise HTTPException(status_code=404, detail="Problem not found")

    await db.execute(contest_problems.insert().values(contest_id=contest_id, problem_id=problem.id))
    await db.commit()


@router.delete("/{contest_id}/problems/{slug}", status_code=status.HTTP_204_NO_CONTENT)
async def detach_problem(
    contest_id: uuid.UUID,
    slug: str,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    result = await db.execute(select(Problem).where(Problem.slug == slug))
    problem = result.scalar_one_or_none()
    if problem is None:
        raise HTTPException(status_code=404, detail="Problem not found")

    await db.execute(
        contest_problems.delete().where(
            contest_problems.c.contest_id == contest_id,
            contest_problems.c.problem_id == problem.id,
        )
    )
    await db.commit()


@router.get("/{contest_id}/leaderboard")
async def contest_leaderboard(contest_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    contest = await db.get(Contest, contest_id)
    if contest is None:
        raise HTTPException(status_code=404, detail="Contest not found")

    cp_result = await db.execute(
        select(contest_problems.c.problem_id).where(contest_problems.c.contest_id == contest_id)
    )
    problem_ids = [row[0] for row in cp_result.all()]
    if not problem_ids:
        return []

    # Computed at query time from submitted_at falling in the window --
    # not a stored flag on the submission -- so if the window is ever
    # changed later, eligibility recalculates automatically rather than
    # being frozen at submit time.
    solved_count = func.count(func.distinct(Submission.problem_id))
    result = await db.execute(
        select(User.username, solved_count.label("solved_count"))
        .join(Submission, Submission.user_id == User.id)
        .where(
            Submission.overall_verdict == "ACCEPTED",
            Submission.problem_id.in_(problem_ids),
            Submission.submitted_at >= contest.start_time,
            Submission.submitted_at <= contest.end_time,
        )
        .group_by(User.id, User.username)
        .order_by(solved_count.desc())
    )
    return [{"username": row.username, "solved_count": row.solved_count} for row in result.all()]
