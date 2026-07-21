from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.models import Submission, User

router = APIRouter(prefix="/leaderboard", tags=["leaderboard"])


@router.get("")
async def get_leaderboard(db: AsyncSession = Depends(get_db)):
    solved_count = func.count(func.distinct(Submission.problem_id))

    result = await db.execute(
        select(User.username, solved_count.label("solved_count"))
        .join(Submission, Submission.user_id == User.id)
        .where(Submission.overall_verdict == "ACCEPTED")
        .group_by(User.id, User.username)
        .order_by(solved_count.desc())
    )

    return [{"username": row.username, "solved_count": row.solved_count} for row in result.all()]
