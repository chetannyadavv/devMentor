import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import require_admin
from app.models import Problem, TestCase, User
from app.schemas import (
    ProblemCreate,
    ProblemOut,
    ProblemUpdate,
    ProblemDetail,
    TestCaseCreate,
    TestCaseOut,
)

router = APIRouter(prefix="/problems", tags=["problems"])


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
async def list_problems(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Problem))
    return result.scalars().all()


@router.get("/{slug}", response_model=ProblemDetail)
async def get_problem(slug: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Problem).where(Problem.slug == slug))
    problem = result.scalar_one_or_none()
    if problem is None:
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
