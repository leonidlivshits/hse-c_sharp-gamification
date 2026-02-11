from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.repositories import choice_repo

router = APIRouter()


@router.get("/question/{question_id}", status_code=status.HTTP_200_OK)
async def list_choices(question_id: int, db: AsyncSession = Depends(get_db)):
    items = await choice_repo.list_choices_for_question(db, question_id)
    return [
        {
            "id": getattr(c, "id", None),
            "question_id": getattr(c, "question_id", None),
            "value": getattr(c, "value", None),
            "ordinal": getattr(c, "ordinal", None),
            "is_correct": getattr(c, "is_correct", False),
        }
        for c in items
    ]


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_choice(payload: dict, db: AsyncSession = Depends(get_db)):
    # payload: question_id, value, ordinal?, is_correct?
    try:
        ch = await choice_repo.create_choice(
            db,
            question_id=payload["question_id"],
            value=payload["value"],
            ordinal=payload.get("ordinal"),
            is_correct=payload.get("is_correct", False),
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {
        "id": getattr(ch, "id", None),
        "question_id": getattr(ch, "question_id", None),
        "value": getattr(ch, "value", None),
        "ordinal": getattr(ch, "ordinal", None),
        "is_correct": getattr(ch, "is_correct", False),
    }


@router.delete("/{choice_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_choice(choice_id: int, db: AsyncSession = Depends(get_db)):
    await choice_repo.delete_choice(db, choice_id)
    return {}
