# tests/integration/test_submit_answer_flow.py
import pytest
pytestmark = pytest.mark.asyncio

from app.repositories import analytics_repo
from app.models.user import User
from app.models.test_ import Test as TestModel
from app.models.question import Question
from app.models.choice import Choice
from app.models.answer import Answer
from app.services.answer_service import submit_answer

@pytest.mark.asyncio
async def test_submit_mcq_full_flow(db):
    """
    Full flow using the test 'db' session fixture (isolated per-test).
    Creates user/test/question/choice, submits answer via service, asserts grading and analytics update.
    """
    # create user
    user = User(username="int_user", password_hash="x")
    db.add(user)
    await db.flush()
    await db.refresh(user)

    # create test
    test = TestModel(title="integration test")
    db.add(test)
    await db.flush()
    await db.refresh(test)

    # create question
    q = Question(test_id=test.id, text="Integr Q", points=4.0, is_open_answer=False)
    db.add(q)
    await db.flush()
    await db.refresh(q)

    # create correct choice
    c = Choice(question_id=q.id, value="OK", ordinal=1, is_correct=True)
    db.add(c)
    await db.flush()
    await db.refresh(c)

    # submit answer (MCQ) — use service
    ans = await submit_answer(db, user_id=user.id, test_id=test.id, question_id=q.id, payload=str(c.id))

    # reload answer from DB
    db_ans = await db.get(Answer, ans.id)
    assert db_ans is not None
    assert db_ans.score == pytest.approx(4.0)

    # analytics
    analytics = await analytics_repo.get_user_analytics(db, user.id)
    assert analytics is not None
    assert analytics.total_points == pytest.approx(4.0)
