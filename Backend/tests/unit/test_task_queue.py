import pytest

from app.core.config import settings
from app.tasks import task_queue

pytestmark = pytest.mark.asyncio


class _FakeRedis:
    def __init__(self):
        self.rpush_calls: list[tuple[str, str]] = []

    async def rpush(self, queue_name: str, payload: str):
        self.rpush_calls.append((queue_name, payload))


async def test_enqueue_answers_postprocess_uses_celery_backend(monkeypatch):
    calls = []

    def fake_send(task_name: str, payload: dict, *, queue: str):
        calls.append((task_name, payload, queue))

    monkeypatch.setattr(settings, "background_tasks_backend", "celery")
    monkeypatch.setattr(task_queue, "_send_celery_task", fake_send)

    await task_queue.enqueue_answers_postprocess(
        user_id=7,
        test_id=11,
        attempt_id=13,
        job_type="attempt_complete",
        source_event="attempt_completed",
    )

    assert calls == [
        (
            "answers_postprocess",
            {
                "job_type": "attempt_complete",
                "user_id": 7,
                "test_id": 11,
                "attempt_id": 13,
                "points_delta": 0.0,
                "answers_count": 0,
                "mark_active": False,
                "source_event": "attempt_completed",
            },
            "answers",
        )
    ]


async def test_enqueue_open_answer_grading_keeps_redis_fallback(monkeypatch):
    fake_redis = _FakeRedis()
    monkeypatch.setattr(settings, "background_tasks_backend", "redis")
    monkeypatch.setattr(task_queue, "get_redis_client", lambda: fake_redis)

    await task_queue.enqueue_open_answer_grading(answer_id=5, user_id=9)

    assert len(fake_redis.rpush_calls) == 1
    queue_name, payload = fake_redis.rpush_calls[0]
    assert queue_name == "grading:open"
    assert '"answer_id": 5' in payload
    assert '"user_id": 9' in payload
