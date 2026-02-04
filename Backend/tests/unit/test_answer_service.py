import pytest
from unittest.mock import AsyncMock, MagicMock
from app.models.answer import Answer
from app.models.question import Question

import app.services.answer_service as answer_service_module

@pytest.mark.asyncio
async def test_submit_answer_autograde_mcq(monkeypatch):
    # Arrange
    mock_session = AsyncMock()
    q = Question(id=1, test_id=1, text="Q", points=3.0, is_open_answer=False)
    mock_session.get = AsyncMock(return_value=q)

    # record_answer returns a new Answer
    created = Answer(id=100, user_id=1, test_id=1, question_id=1, answer_payload="5")
    monkeypatch.setattr("app.services.answer_service.answer_repo.record_answer", AsyncMock(return_value=created))

    # grade_mcq_answer returns the same answer with score set
    graded = Answer(id=100, user_id=1, test_id=1, question_id=1, answer_payload="5", score=3.0)
    monkeypatch.setattr("app.services.answer_service.answer_repo.grade_mcq_answer", AsyncMock(return_value=graded))

    # patch analytics repo
    mock_analytics = AsyncMock()
    monkeypatch.setattr("app.services.answer_service.analytics_repo.create_or_update_analytics", mock_analytics)

    # patch cache invalidation
    mock_delete_pattern = AsyncMock()
    monkeypatch.setattr("app.services.answer_service.delete_pattern", mock_delete_pattern)

    # Act
    result = await answer_service_module.submit_answer(mock_session, user_id=1, test_id=1, question_id=1, payload="5")

    # Assert
    assert result is not None
    assert result.score == 3.0
    mock_analytics.assert_awaited()  # analytics was updated
    mock_delete_pattern.assert_awaited()  # cache invalidated


@pytest.mark.asyncio
async def test_submit_answer_open_queues_job(monkeypatch):
    # Arrange
    mock_session = AsyncMock()
    q = Question(id=2, test_id=1, text="Q2", points=1.0, is_open_answer=True)
    mock_session.get = AsyncMock(return_value=q)

    created = Answer(id=101, user_id=2, test_id=1, question_id=2, answer_payload="some text")
    monkeypatch.setattr("app.services.answer_service.answer_repo.record_answer", AsyncMock(return_value=created))

    # Use a fake redis client with rpush
    fake_redis = MagicMock()
    fake_redis.rpush = AsyncMock()
    monkeypatch.setattr("app.services.answer_service.get_redis_client", lambda: fake_redis)

    # patch cache invalidation (should still run)
    mock_delete_pattern = AsyncMock()
    monkeypatch.setattr("app.services.answer_service.delete_pattern", mock_delete_pattern)

    # Act
    result = await answer_service_module.submit_answer(mock_session, user_id=2, test_id=1, question_id=2, payload="some text")

    # Assert
    assert result is not None
    fake_redis.rpush.assert_awaited()
    mock_delete_pattern.assert_awaited()
