from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload
from app.models.question import Question
from app.models.choice import Choice

async def create_question_with_choices(session, test_id: int, text: str, points: float = 1.0, is_open_answer: bool = False, choices: list[dict] | None = None):
    """
    Creates a Question and its Choices (if provided).
    choices: list of dicts {value, ordinal, is_correct}
    """
    q = Question(test_id=test_id, text=text, points=points, is_open_answer=is_open_answer)
    session.add(q)
    await session.flush()  # get q.id
    if choices:
        for c in choices:
            ch = Choice(question_id=q.id, value=c["value"], ordinal=c.get("ordinal"), is_correct=c.get("is_correct", False))
            session.add(ch)
    await session.flush()   # вместо commit
    await session.refresh(q)
    return q

async def get_question_with_choices(session, question_id: int):
    q = select(Question).options(selectinload(Question.choices)).where(Question.id == question_id)
    res = await session.execute(q)
    return res.scalars().first()

async def list_questions_for_test(session, test_id: int, limit: int = 100, offset: int = 0):
    q = select(Question).where(Question.test_id == test_id).limit(limit).offset(offset)
    res = await session.execute(q)
    return res.scalars().all()

async def delete_question(session, question_id: int):
    await session.execute(delete(Question).where(Question.id == question_id))
    await session.flush()