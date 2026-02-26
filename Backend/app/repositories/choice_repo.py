from sqlalchemy import select, delete
from app.models.choice import Choice

async def list_choices_for_question(session, question_id: int):
    q = select(Choice).where(Choice.question_id == question_id).order_by(Choice.ordinal)
    res = await session.execute(q)
    return res.scalars().all()

async def create_choice(session, question_id: int, value: str, ordinal: int | None = None, is_correct: bool = False):
    ch = Choice(question_id=question_id, value=value, ordinal=ordinal, is_correct=is_correct)
    session.add(ch)
    await session.flush()
    await session.refresh(ch)
    return ch

async def delete_choice(session, choice_id: int):
    await session.execute(delete(Choice).where(Choice.id == choice_id))
    await session.flush()  # необязательно, но для единообразия