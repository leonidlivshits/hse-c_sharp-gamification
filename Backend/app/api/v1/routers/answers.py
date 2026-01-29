# app/api/v1/routers/answers.py
from fastapi import APIRouter, Depends, HTTPException
from app.api.deps import get_db
from app.schemas.answer import AnswerCreate, AnswerRead
from app.services import answer_service

router = APIRouter()

@router.post("/", response_model=AnswerRead)
async def submit_answer(payload: AnswerCreate, db=Depends(get_db)):
    ans = await answer_service.submit_answer(db, payload.user_id, payload.test_id, payload.question_id, payload.answer_payload)
    if not ans:
        raise HTTPException(status_code=500, detail="Failed to submit answer")
    return ans
