from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.repositories import answer_repo, analytics_repo
from app.cache import redis_cache  # expects functions like delete_pattern
from typing import Optional

router = APIRouter()


def _answer_to_dict(a):
    return {
        "id": getattr(a, "id", None),
        "user_id": getattr(a, "user_id", None),
        "test_id": getattr(a, "test_id", None),
        "question_id": getattr(a, "question_id", None),
        "answer_payload": getattr(a, "answer_payload", None),
        "score": getattr(a, "score", None),
        "graded_by": getattr(a, "graded_by", None),
        "graded_at": getattr(a, "graded_at", None),
        "created_at": getattr(a, "created_at", None),
    }


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_answer(payload: dict, db: AsyncSession = Depends(get_db)):
    """
    payload: {user_id, test_id, question_id, answer_payload}
    Behaviour:
      - persist answer
      - try auto-grade (MCQ) synchronously
      - if graded: update analytics and invalidate leaderboard/test summary caches
      - for open answers: returns answer with score None (worker handles)
    """
    try:
        ans = await answer_repo.record_answer(db, payload["user_id"], payload["test_id"], payload["question_id"], payload.get("answer_payload"))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    # try auto-grade
    graded = await answer_repo.grade_mcq_answer(db, ans.id)
    # if grading produced / updated score -> update analytics and invalidate cache
    if graded and graded.score is not None:
        # increment analytics
        try:
            await analytics_repo.create_or_update_analytics(db, graded.user_id, points_delta=float(graded.score), mark_active=True)
        except Exception:
            # analytics best-effort: log, but don't fail request
            pass
        # invalidate relevant caches
        try:
            await redis_cache.delete_pattern("leaderboard*")
            await redis_cache.delete_pattern(f"test:{graded.test_id}:summary")
        except Exception:
            pass

    return _answer_to_dict(graded or ans)


@router.get("/{answer_id}", status_code=status.HTTP_200_OK)
async def get_answer(answer_id: int, db: AsyncSession = Depends(get_db)):
    a = await db.get(type(answer_repo).__name__ if False else None, answer_id)  # placeholder to avoid linter only
    # safer explicit fetch:
    from app.models.answer import Answer as AnswerModel
    a = await db.get(AnswerModel, answer_id)
    if not a:
        raise HTTPException(status_code=404, detail="Answer not found")
    return _answer_to_dict(a)


@router.get("/test/{test_id}", status_code=status.HTTP_200_OK)
async def get_answers_for_test(test_id: int, user_id: Optional[int] = None, limit: int = 100, offset: int = 0, db: AsyncSession = Depends(get_db)):
    answers = await answer_repo.get_answers_for_test(db, test_id=test_id, limit=limit, offset=offset)
    if user_id:
        answers = [a for a in answers if a.user_id == user_id]
    return [_answer_to_dict(a) for a in answers]
