import pytest
import asyncio

from app.db.session import AsyncSessionLocal
from app.models.user import User
from app.models.test_ import Test as TestModel
from app.models.question import Question
from app.models.choice import Choice
from app.repositories import analytics_repo
from app.services.answer_service import submit_answer
from app.models.answer import Answer

@pytest.mark.asyncio
async def test_submit_mcq_full_flow():
    async with AsyncSessionLocal() as session:
        # create user
        user = User(username="int_user", password_hash="x")
        session.add(user)
        await session.commit()
        await session.refresh(user)

        # create test
        test = TestModel(title="integration test")
        session.add(test)
        await session.commit()
        await session.refresh(test)

        # create question
        q = Question(test_id=test.id, text="Integr Q", points=4.0, is_open_answer=False)
        session.add(q)
        await session.commit()
        await session.refresh(q)

        # create correct choice
        c = Choice(question_id=q.id, value="OK", ordinal=1, is_correct=True)
        session.add(c)
        await session.commit()
        await session.refresh(c)

        # submit answer (MCQ)
        ans = await submit_answer(session, user_id=user.id, test_id=test.id, question_id=q.id, payload=str(c.id))

        # reload answer from DB
        db_ans = await session.get(Answer, ans.id)
        assert db_ans is not None
        assert db_ans.score == pytest.approx(4.0)

        # analytics
        analytics = await analytics_repo.get_user_analytics(session, user.id)
        assert analytics is not None
        assert analytics.total_points >= 4.0
