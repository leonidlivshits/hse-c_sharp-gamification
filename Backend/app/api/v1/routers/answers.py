from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.schemas.answer import AnswerCreate, AnswerRead
from app.services.answer_service import submit_answer
from app.repositories import answer_repo
from app.models.answer import Answer as AnswerModel

router = APIRouter()


@router.post("/", response_model=AnswerRead, status_code=status.HTTP_201_CREATED)
async def create_answer(payload: AnswerCreate, db: AsyncSession = Depends(get_db)):
    """
    Submit an answer. Uses the orchestration service which:
      - records the answer
      - auto-grades MCQ
      - updates analytics
      - enqueues open answers for manual grading
      - invalidates caches (best-effort)
    """
    ans = await submit_answer(db, payload.user_id, payload.test_id, payload.question_id, payload.answer_payload)
    if not ans:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to submit answer")
    return ans


@router.get("/{answer_id}", response_model=AnswerRead, status_code=status.HTTP_200_OK)
async def get_answer(answer_id: int, db: AsyncSession = Depends(get_db)):
    a = await db.get(AnswerModel, answer_id)
    if not a:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Answer not found")
    return a


@router.get("/test/{test_id}", response_model=List[AnswerRead], status_code=status.HTTP_200_OK)
async def get_answers_for_test(
    test_id: int,
    user_id: Optional[int] = None,
    limit: int = 100,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    answers = await answer_repo.get_answers_for_test(db, test_id=test_id, limit=limit, offset=offset)
    if user_id:
        answers = [a for a in answers if a.user_id == user_id]
    return answers


@router.post("/{answer_id}/grade", response_model=AnswerRead, status_code=status.HTTP_200_OK)
async def manual_grade_answer(answer_id: int, db: AsyncSession = Depends(get_db)):
    """
    Force re-grade an answer (MCQ auto-grader). Admin/helper endpoint.
    """
    graded = await answer_repo.grade_mcq_answer(db, answer_id)
    if not graded:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Answer not found or could not be graded")
    return graded