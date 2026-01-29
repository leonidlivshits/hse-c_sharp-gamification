import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest_asyncio

from app.repositories import answer_repo
from app.models.answer import Answer
from app.models.choice import Choice
from app.models.question import Question


@pytest.mark.asyncio
async def test_grade_mcq_answer_correct_choice():
    # Arrange: create a fake answer with payload "2"
    ans = Answer(id=10, user_id=1, test_id=1, question_id=1, answer_payload="2", score=None)

    # mock session.get to return our answer
    mock_session = AsyncMock()
    mock_session.get = AsyncMock(return_value=ans)

    # prepare mock Choice and Question returned by execute().first()
    choice = Choice(id=2, question_id=1, value="a", is_correct=True)
    question = Question(id=1, test_id=1, text="Q", points=2.5, is_open_answer=False)

    # mock result of session.execute(stmt).first() -> (choice, question)
    mock_result = MagicMock()
    mock_result.first = MagicMock(return_value=(choice, question))
    mock_session.execute = AsyncMock(return_value=mock_result)

    # mock commit/refresh to be async no-op
    mock_session.commit = AsyncMock()
    mock_session.refresh = AsyncMock()

    # Act
    updated = await answer_repo.grade_mcq_answer(mock_session, ans.id)

    # Assert
    assert updated is not None
    # since choice.is_correct True and question.points=2.5 -> score should be 2.5
    assert float(updated.score) == 2.5
    # ensure commit was called
    mock_session.commit.assert_awaited()


@pytest.mark.asyncio
async def test_grade_mcq_answer_bad_payload_does_not_raise_and_leaves_score_none():
    # Arrange: answer with a non-integer payload
    ans = Answer(id=11, user_id=1, test_id=1, question_id=1, answer_payload="not-an-int", score=None)
    mock_session = AsyncMock()
    mock_session.get = AsyncMock(return_value=ans)

    # Ensure execute is not called (since parse fails). But even if called, it should be safe.
    mock_session.execute = AsyncMock()

    # Act - should not raise
    updated = await answer_repo.grade_mcq_answer(mock_session, ans.id)

    # Assert: returned object is the same answer with score unchanged (None)
    assert updated is not None
    assert updated.score is None
