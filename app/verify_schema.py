import asyncio

from sqlalchemy import select

from app.core.db import async_session
from app.models import User, Problem, TestCase, Submission


async def main():
    async with async_session() as session:
        user = User(username="alice", email="alice@example.com", password_hash="fakehash")
        problem = Problem(
            slug="two-sum",
            title="Two Sum",
            statement="Given nums, return indices of the two that sum to target.",
            version=1,
        )
        session.add_all([user, problem])
        await session.flush()  # assigns IDs without committing yet

        test_case = TestCase(
            problem_id=problem.id,
            stdin="2 7 11 15\n9",
            expected_output="0 1",
            is_sample=True,
        )
        submission = Submission(
            user_id=user.id,
            problem_id=problem.id,
            problem_version=problem.version,  # the snapshot
            language="python",
            source_code="print('hello')",
            overall_verdict="ACCEPTED",
        )
        session.add_all([test_case, submission])
        await session.commit()

        submission_id = submission.id
        print("Inserted user:", user.id, user.username)
        print("Inserted problem:", problem.id, problem.title, "version:", problem.version)
        print("Inserted test_case:", test_case.id, "for problem:", test_case.problem_id)
        print("Inserted submission:", submission.id, "problem_version snapshot:", submission.problem_version)

    # Fresh session, prove the row is really durable, not just cached
    # in-memory from the same transaction.
    async with async_session() as session:
        result = await session.execute(select(Submission).where(Submission.id == submission_id))
        fetched = result.scalar_one()
        print("\nFetched back in a new session:")
        print(" ", fetched.id, fetched.overall_verdict, fetched.language, "v" + str(fetched.problem_version))

    print("\nSCHEMA VERIFICATION PASSED")


if __name__ == "__main__":
    asyncio.run(main())
