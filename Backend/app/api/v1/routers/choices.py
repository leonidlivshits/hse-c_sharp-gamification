from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.schemas.question import ChoiceCreate, ChoiceRead
from app.repositories import choice_repo

router = APIRouter()


@router.get("/question/{question_id}", response_model=List[ChoiceRead], status_code=status.HTTP_200_OK)
async def list_choices(question_id: int, db: AsyncSession = Depends(get_db)):
    items = await choice_repo.list_choices_for_question(db, question_id)
    return items


@router.post("/", response_model=ChoiceRead, status_code=status.HTTP_201_CREATED)
async def create_choice(payload: ChoiceCreate, db: AsyncSession = Depends(get_db)):
    ch = await choice_repo.create_choice(
        db,
        question_id=payload.question_id,
        value=payload.value,
        ordinal=payload.ordinal,
        is_correct=payload.is_correct,
    )
    return ch


@router.delete("/{choice_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_choice(choice_id: int, db: AsyncSession = Depends(get_db)):
    await choice_repo.delete_choice(db, choice_id)
    return {}