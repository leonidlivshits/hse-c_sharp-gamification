from sqlalchemy import func, select
from Backend.app.models.answer import Answer
from Backend.app.models.question import Question
from app.models.test_ import Test

async def get_test(session, test_id: int):
    q = select(Test).where(Test.id == test_id)
    res = await session.execute(q)
    return res.scalars().first()

async def list_tests(session, published_only: bool = True, limit: int = 100):
    q = select(Test)
    if published_only:
        q = q.where(Test.published == True)
    q = q.limit(limit)
    res = await session.execute(q)
    return res.scalars().all()

async def create_test(session, title: str, description: str | None = None, time_limit_minutes: int | None = None, max_score: int | None = None, material_id: int | None = None):
    test = Test(title=title, description=description, time_limit_minutes=time_limit_minutes, max_score=max_score, material_id=material_id)
    session.add(test)
    await session.commit()
    await session.refresh(test)
    return test

async def test_summary(session, test_id: int):
    """
    Return summary stats for a test:
    - total_questions
    - total_attempts (answers)
    - avg_score_per_attempt (overall)
    - completion_rate (approx)
    """
    total_q = await session.scalar(select(func.count(Question.id)).where(Question.test_id == test_id))
    total_attempts = await session.scalar(select(func.count(Answer.id)).where(Answer.test_id == test_id))
    avg_score = await session.scalar(select(func.avg(Answer.score)).where(Answer.test_id == test_id))
    return {
        "test_id": test_id,
        "total_questions": total_q or 0,
        "total_attempts": total_attempts or 0,
        "avg_score": float(avg_score) if avg_score is not None else None,
    }
