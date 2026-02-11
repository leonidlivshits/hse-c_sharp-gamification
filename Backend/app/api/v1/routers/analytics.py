from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.repositories import analytics_repo, test_repo
from typing import List

router = APIRouter()


@router.get("/leaderboard", status_code=200)
async def get_leaderboard(limit: int = 50, offset: int = 0, db: AsyncSession = Depends(get_db)):
    data = await analytics_repo.get_leaderboard(db, limit=limit, offset=offset)
    return data


@router.get("/tests/{test_id}/summary", status_code=200)
async def get_test_summary(test_id: int, db: AsyncSession = Depends(get_db)):
    summary = await test_repo.test_summary(db, test_id)
    if summary is None:
        raise HTTPException(status_code=404, detail="Test not found or no data")
    return summary


@router.get("/questions/{question_id}/stats", status_code=200)
async def question_stats(question_id: int, db: AsyncSession = Depends(get_db)):
    stats = await analytics_repo.question_statistics(db, question_id)
    return stats


@router.get("/users/{user_id}", status_code=200)
async def user_analytics(user_id: int, db: AsyncSession = Depends(get_db)):
    a = await analytics_repo.get_user_analytics(db, user_id)
    if not a:
        raise HTTPException(status_code=404, detail="Analytics not found for user")
    # serialize simple
    return {
        "user_id": a.user_id,
        "total_points": a.total_points,
        "tests_taken": a.tests_taken,
        "last_active": a.last_active,
        "streak_days": a.streak_days,
        "current_level_id": a.current_level_id,
    }
