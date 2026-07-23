import uuid
from collections import defaultdict
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import require_admin, get_current_user_optional
from app.models import Problem, TestCase, User, Contest, contest_problems
from app.schemas import (
    ProblemCreate,
    ProblemOut,
    ProblemUpdate,
    ProblemDetail,
    TestCaseCreate,
    TestCaseOut,
)

router = APIRouter(prefix="/problems", tags=["problems"])


async def _visible_problem_ids(db: AsyncSession) -> set | None:
    """
    Returns None if there's no filtering to do (fast path). Otherwise,
    the set of problem IDs a non-admin is allowed to see: any problem
    with no contest links at all, plus any problem linked to at least
    one contest that has already started. A problem hidden ONLY because
    every contest it belongs to hasn't started yet is excluded.
    """
    result = await db.execute(
        select(contest_problems.c.problem_id, Contest.start_time).join(
            Contest, Contest.id == contest_problems.c.contest_id
        )
    )
    links = result.all()
    if not links:
        return None  # no contest-linked problems exist at all -- nothing to hide

    now = datetime.now(timezone.utc)
    starts_by_problem = defaultdict(list)
    for problem_id, start_time in links:
        starts_by_problem[problem_id].append(start_time)

    hidden_ids = {
        problem_id
        for problem_id, starts in starts_by_problem.items()
        if all(s > now for s in starts)
    }
    return hidden_ids  # returned as "hidden", inverted where used below


@router.post("", response_model=ProblemOut, status_code=status.HTTP_201_CREATED)
async def create_problem(
    payload: ProblemCreate,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    existing = await db.execute(select(Problem).where(Problem.slug == payload.slug))
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(status_code=400, detail="A problem with this slug already exists")

    problem = Problem(slug=payload.slug, title=payload.title, statement=payload.statement, version=1)
    db.add(problem)
    await db.commit()
    await db.refresh(problem)
    return problem


@router.get("", response_model=list[ProblemOut])
async def list_problems(
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    result = await db.execute(select(Problem))
    problems = result.scalars().all()

    is_admin = current_user is not None and current_user.is_admin
    if is_admin:
        return problems

    hidden_ids = await _visible_problem_ids(db)
    if hidden_ids is None:
        return problems
    return [p for p in problems if p.id not in hidden_ids]


@router.get("/{slug}", response_model=ProblemDetail)
async def get_problem(
    slug: str,
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    result = await db.execute(select(Problem).where(Problem.slug == slug))
    problem = result.scalar_one_or_none()
    if problem is None:
        raise HTTPException(status_code=404, detail="Problem not found")

    is_admin = current_user is not None and current_user.is_admin
    if not is_admin:
        hidden_ids = await _visible_problem_ids(db)
        if hidden_ids is not None and problem.id in hidden_ids:
            # 404, not 403 -- don't reveal that a hidden problem exists.
            raise HTTPException(status_code=404, detail="Problem not found")

    # Public view only ever shows sample test cases -- hidden cases used
    # for actual grading are never exposed here.
    tc_result = await db.execute(
        select(TestCase).where(TestCase.problem_id == problem.id, TestCase.is_sample.is_(True))
    )
    sample_cases = tc_result.scalars().all()

    return ProblemDetail(
        id=problem.id,
        slug=problem.slug,
        title=problem.title,
        statement=problem.statement,
        version=problem.version,
        sample_test_cases=sample_cases,
    )


@router.patch("/{slug}", response_model=ProblemOut)
async def update_problem(
    slug: str,
    payload: ProblemUpdate,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    result = await db.execute(select(Problem).where(Problem.slug == slug))
    problem = result.scalar_one_or_none()
    if problem is None:
        raise HTTPException(status_code=404, detail="Problem not found")

    # Deliberately does NOT bump version -- title/statement edits don't
    # change grading correctness. Only test case changes do (below).
    if payload.title is not None:
        problem.title = payload.title
    if payload.statement is not None:
        problem.statement = payload.statement

    await db.commit()
    await db.refresh(problem)
    return problem


@router.delete("/{slug}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_problem(
    slug: str,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    result = await db.execute(select(Problem).where(Problem.slug == slug))
    problem = result.scalar_one_or_none()
    if problem is None:
        raise HTTPException(status_code=404, detail="Problem not found")
    await db.delete(problem)
    await db.commit()


# --- Test case management ---


@router.post("/{slug}/test-cases", response_model=TestCaseOut, status_code=status.HTTP_201_CREATED)
async def add_test_case(
    slug: str,
    payload: TestCaseCreate,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    result = await db.execute(select(Problem).where(Problem.slug == slug))
    problem = result.scalar_one_or_none()
    if problem is None:
        raise HTTPException(status_code=404, detail="Problem not found")

    test_case = TestCase(
        problem_id=problem.id,
        stdin=payload.stdin,
        expected_output=payload.expected_output,
        is_sample=payload.is_sample,
    )
    db.add(test_case)

    # The version bump actually happening for real -- adding a test case
    # changes what "correct" means for this problem.
    problem.version += 1

    await db.commit()
    await db.refresh(test_case)
    return test_case


@router.get("/{slug}/test-cases", response_model=list[TestCaseOut])
async def list_test_cases(
    slug: str,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    # Admin-only: shows hidden cases too, unlike the public detail
    # endpoint above.
    result = await db.execute(select(Problem).where(Problem.slug == slug))
    problem = result.scalar_one_or_none()
    if problem is None:
        raise HTTPException(status_code=404, detail="Problem not found")

    tc_result = await db.execute(select(TestCase).where(TestCase.problem_id == problem.id))
    return tc_result.scalars().all()


@router.delete("/{slug}/test-cases/{test_case_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_test_case(
    slug: str,
    test_case_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    result = await db.execute(select(Problem).where(Problem.slug == slug))
    problem = result.scalar_one_or_none()
    if problem is None:
        raise HTTPException(status_code=404, detail="Problem not found")

    tc_result = await db.execute(
        select(TestCase).where(TestCase.id == test_case_id, TestCase.problem_id == problem.id)
    )
    test_case = tc_result.scalar_one_or_none()
    if test_case is None:
        raise HTTPException(status_code=404, detail="Test case not found")

    await db.delete(test_case)
    problem.version += 1

    await db.commit()
