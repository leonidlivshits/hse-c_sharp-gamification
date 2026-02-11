from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.repositories import question_repo

router = APIRouter()


def _question_to_dict(q):
    return {
        "id": getattr(q, "id", None),
        "test_id": getattr(q, "test_id", None),
        "text": getattr(q, "text", None),
        "points": getattr(q, "points", None),
        "is_open_answer": getattr(q, "is_open_answer", False),
    }


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_question(payload: dict, db: AsyncSession = Depends(get_db)):
    # payload: test_id, text, points?, is_open_answer?, choices?
    try:
        q = await question_repo.create_question_with_choices(
            db,
            test_id=payload["test_id"],
            text=payload["text"],
            points=payload.get("points", 1.0),
            is_open_answer=payload.get("is_open_answer", False),
            choices=payload.get("choices"),
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    return _question_to_dict(q)


@router.get("/test/{test_id}", status_code=status.HTTP_200_OK)
async def list_questions_for_test(test_id: int, limit: int = 100, offset: int = 0, db: AsyncSession = Depends(get_db)):
    qs = await question_repo.list_questions_for_test(db, test_id=test_id, limit=limit, offset=offset)
    return [_question_to_dict(x) for x in qs]


@router.get("/{question_id}", status_code=status.HTTP_200_OK)
async def get_question(question_id: int, db: AsyncSession = Depends(get_db)):
    q = await question_repo.get_question_with_choices(db, question_id)
    if not q:
        raise HTTPException(status_code=404, detail="Question not found")
    # return question with loaded choices as simple dict
    data = _question_to_dict(q)
    choices = []
    if hasattr(q, "choices") and q.choices:
        for c in q.choices:
            choices.append({
                "id": getattr(c, "id", None),
                "value": getattr(c, "value", None),
                "ordinal": getattr(c, "ordinal", None),
                "is_correct": getattr(c, "is_correct", False),
            })
    data["choices"] = choices
    return data


@router.delete("/{question_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_question(question_id: int, db: AsyncSession = Depends(get_db)):
    await question_repo.delete_question(db, question_id)
    return {}
