from sqlalchemy import select, delete, update
from app.models.answer import Answer
from app.models.choice import Choice
from app.models.question import Question

async def record_answer(session, user_id: int, test_id: int, question_id: int, payload: str):
    a = Answer(user_id=user_id, test_id=test_id, question_id=question_id, answer_payload=payload)
    session.add(a)
    await session.commit()
    await session.refresh(a)
    return a

async def grade_mcq_answer(session, answer_id: int):
    """
    Auto-grade MCQ: expects answer_payload contains choice id as string/int.
    Returns updated Answer instance (with score set).
    """
    q = await session.get(Answer, answer_id)
    if not q:
        return None

    # fetch question and choice
    try:
        choice_id = int(q.answer_payload)
    except Exception:
        # cannot auto-grade
        return q

    stmt = (
        select(Choice, Question)
        .join(Question, Choice.question_id == Question.id)
        .where(Choice.id == choice_id)
    )
    res = await session.execute(stmt)
    row = res.first()
    if not row:
        # choice not found
        return q
    choice, question = row
    score = float(question.points) if choice.is_correct else 0.0
    q.score = score
    await session.commit()
    await session.refresh(q)
    return q

async def get_answers_for_test(session, test_id: int, limit: int = 100, offset: int = 0):
    stmt = select(Answer).where(Answer.test_id == test_id).limit(limit).offset(offset)
    res = await session.execute(stmt)
    return res.scalars().all()
