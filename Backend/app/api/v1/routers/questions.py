from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.schemas.question import QuestionCreate, QuestionRead
from app.repositories import question_repo

router = APIRouter()


@router.post("/", response_model=QuestionRead, status_code=status.HTTP_201_CREATED)
async def create_question(payload: QuestionCreate, db: AsyncSession = Depends(get_db)):
    """
    Create a question. payload may include 'choices' list (value, ordinal, is_correct).
    """
    q = await question_repo.create_question_with_choices(
        db,
        test_id=payload.test_id,
        text=payload.text,
        points=payload.points,
        is_open_answer=payload.is_open_answer,
        choices=[c.model_dump() for c in (payload.choices or [])] if payload.choices else None,
    )
    return q


@router.get("/test/{test_id}", response_model=List[QuestionRead], status_code=status.HTTP_200_OK)
async def list_questions_for_test(test_id: int, limit: int = 100, offset: int = 0, db: AsyncSession = Depends(get_db)):
    qs = await question_repo.list_questions_for_test(db, test_id=test_id, limit=limit, offset=offset)
    return qs


@router.get("/{question_id}", response_model=QuestionRead, status_code=status.HTTP_200_OK)
async def get_question(question_id: int, db: AsyncSession = Depends(get_db)):
    q = await question_repo.get_question_with_choices(db, question_id)
    if not q:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found")
    return q


@router.delete("/{question_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_question(question_id: int, db: AsyncSession = Depends(get_db)):
    await question_repo.delete_question(db, question_id)
    return {}