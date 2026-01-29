"""
Answer repository: persistence + MCQ autograder helper.

Functions:
- record_answer(session, user_id, test_id, question_id, payload)
- grade_mcq_answer(session, answer_id)
- get_answers_for_test(session, test_id, limit=100, offset=0)
"""
from typing import Optional, Tuple
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from app.models.answer import Answer
from app.models.choice import Choice
from app.models.question import Question


async def record_answer(session, user_id: int, test_id: int, question_id: int, payload: str) -> Answer:
    """
    Persist an Answer row and return it (fresh from DB).
    """
    a = Answer(user_id=user_id, test_id=test_id, question_id=question_id, answer_payload=payload)
    session.add(a)
    try:
        await session.commit()
        await session.refresh(a)
    except Exception:
        # rollback to keep session usable for caller
        await session.rollback()
        raise
    return a


async def grade_mcq_answer(session, answer_id: int) -> Optional[Answer]:
    """
    Auto-grade answer with MCQ: parses answer.answer_payload as int(choice_id),
    loads Choice and Question and sets score = question.points if choice.is_correct else 0.0.

    Returns the updated Answer (fresh from DB). If cannot auto-grade (bad payload / choice not found),
    returns the Answer unchanged (score may remain None).
    """
    # load the answer first
    try:
        answer = await session.get(Answer, answer_id)
    except SQLAlchemyError:
        return None

    if not answer:
        return None

    payload = answer.answer_payload
    if payload is None:
        # nothing to grade
        return answer

    # try parse as integer choice id
    try:
        choice_id = int(str(payload).strip())
    except (ValueError, TypeError):
        # not an MCQ choice id
        return answer

    stmt = (
        select(Choice, Question)
        .join(Question, Choice.question_id == Question.id)
        .where(Choice.id == choice_id)
    )

    try:
        res = await session.execute(stmt)
        row = res.first()
    except Exception:
        # DB error -> do not crash auto-grader; leave for manual grading
        return answer

    if not row:
        # choice not found, can't auto-grade
        return answer

    choice_obj, question_obj = row
    # compute score
    try:
        score = float(question_obj.points) if bool(choice_obj.is_correct) else 0.0
    except Exception:
        score = 0.0

    # persist score
    answer.score = score
    try:
        await session.commit()
        await session.refresh(answer)
    except Exception:
        await session.rollback()
        # if commit fails, leave answer as-is (caller can retry)
        return answer

    return answer


async def get_answers_for_test(session, test_id: int, limit: int = 100, offset: int = 0):
    stmt = select(Answer).where(Answer.test_id == test_id).limit(limit).offset(offset)
    res = await session.execute(stmt)
    return res.scalars().all()
