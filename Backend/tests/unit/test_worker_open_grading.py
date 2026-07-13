import json
from types import SimpleNamespace

import pytest

from app.models.answer import Answer
from app.tasks import worker

pytestmark = pytest.mark.asyncio


class _FakeAsyncSessionCtx:
    def __init__(self, *, answer):
        self._answer = answer
        self.commits = 0
        self.rollbacks = 0

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def get(self, model, pk):
        del model, pk
        return self._answer

    async def commit(self):
        self.commits += 1

    async def rollback(self):
        self.rollbacks += 1


class _FakeRedis:
    def __init__(self):
        self.rpush_calls: list[tuple[str, str]] = []

    async def rpush(self, queue_name: str, payload: str):
        self.rpush_calls.append((queue_name, payload))


class _FakeIdempotencyRedis:
    def __init__(self):
        self.values: dict[str, str] = {}

    async def get(self, key: str):
        return self.values.get(key)

    async def set(self, key: str, value: str, ex=None, nx: bool = False):
        del ex
        if nx and key in self.values:
            return False
        self.values[key] = value
        return True

    async def delete(self, key: str):
        self.values.pop(key, None)


async def test_process_job_requeues_when_answer_is_temporarily_missing(monkeypatch):
    fake_redis = _FakeRedis()
    fake_session = _FakeAsyncSessionCtx(answer=None)

    monkeypatch.setattr(worker, "get_redis_client", lambda: fake_redis)
    monkeypatch.setattr(worker, "AsyncSessionLocal", lambda: fake_session)

    await worker.process_job(json.dumps({"answer_id": 42, "user_id": 7, "retries": 1}))

    assert fake_session.rollbacks == 1
    assert len(fake_redis.rpush_calls) == 1
    queue_name, payload = fake_redis.rpush_calls[0]
    assert queue_name == "grading:open"
    parsed = json.loads(payload)
    assert parsed["answer_id"] == 42
    assert parsed["retries"] == 2


async def test_process_job_refreshes_attempt_and_invalidates_cache(monkeypatch):
    answer = Answer(user_id=1, test_id=2, question_id=3, answer_payload="text", attempt_id=5)
    answer.id = 77
    fake_session = _FakeAsyncSessionCtx(answer=answer)

    calls = {"get_attempt": 0, "refresh_attempt_scores": 0, "cache": 0}

    async def _fake_get_attempt(session, attempt_id: int):
        del session
        calls["get_attempt"] += 1
        assert attempt_id == 5
        return SimpleNamespace(id=5, user_id=1, test_id=2)

    async def _fake_refresh_attempt_scores(session, attempt):
        del session, attempt
        calls["refresh_attempt_scores"] += 1
        return None

    async def _fake_bump_cache_namespace(*namespaces: str):
        assert set(namespaces) == {"leaderboard", "test_summary"}
        calls["cache"] += 1

    monkeypatch.setattr(worker, "AsyncSessionLocal", lambda: fake_session)
    monkeypatch.setattr(worker.test_attempt_repo, "get_attempt", _fake_get_attempt)
    monkeypatch.setattr(worker.test_attempt_repo, "refresh_attempt_scores", _fake_refresh_attempt_scores)
    monkeypatch.setattr(worker, "bump_cache_namespace", _fake_bump_cache_namespace)

    await worker.process_job(json.dumps({"answer_id": 77, "user_id": 1}))

    assert fake_session.commits == 1
    assert calls["get_attempt"] == 1
    assert calls["refresh_attempt_scores"] == 1
    assert calls["cache"] == 1


async def test_process_answer_postprocess_attempt_complete_runs_deferred_side_effects(monkeypatch):
    fake_session = _FakeAsyncSessionCtx(answer=None)
    calls = {"rewards_sync": 0, "events": [], "cache": 0}

    async def _fake_sync_user_rewards(session, user_id: int):
        assert session is fake_session
        assert user_id == 17
        calls["rewards_sync"] += 1

    async def _fake_record_event(session, *, user_id, event_type, increment=1):
        assert session is fake_session
        assert user_id == 17
        calls["events"].append((event_type.value, increment))
        return []

    async def _fake_bump_cache_namespace(*namespaces: str):
        assert set(namespaces) == {"leaderboard", "test_summary"}
        calls["cache"] += 1

    monkeypatch.setattr(worker, "AsyncSessionLocal", lambda: fake_session)
    monkeypatch.setattr(
        worker.reward_service,
        "sync_user_rewards",
        _fake_sync_user_rewards,
    )
    monkeypatch.setattr(worker, "record_event", _fake_record_event)
    monkeypatch.setattr(worker, "bump_cache_namespace", _fake_bump_cache_namespace)

    await worker.process_answer_postprocess(json.dumps({"job_type": "attempt_complete", "user_id": 17}))

    assert fake_session.commits == 1
    assert calls["rewards_sync"] == 1
    assert ("attempt_completed", 1) in calls["events"]
    assert ("streak_day", 1) in calls["events"]
    assert calls["cache"] == 1


async def test_process_answer_postprocess_attempt_complete_is_idempotent(monkeypatch):
    fake_session = _FakeAsyncSessionCtx(answer=None)
    fake_redis = _FakeIdempotencyRedis()
    calls = {"rewards_sync": 0, "events": [], "cache": 0}

    async def _fake_sync_user_rewards(session, user_id: int):
        assert session is fake_session
        assert user_id == 17
        calls["rewards_sync"] += 1

    async def _fake_record_event(session, *, user_id, event_type, increment=1):
        assert session is fake_session
        assert user_id == 17
        calls["events"].append((event_type.value, increment))
        return []

    async def _fake_bump_cache_namespace(*namespaces: str):
        assert set(namespaces) == {"leaderboard", "test_summary"}
        calls["cache"] += 1

    monkeypatch.setattr(worker, "get_redis_client", lambda: fake_redis)
    monkeypatch.setattr(worker, "AsyncSessionLocal", lambda: fake_session)
    monkeypatch.setattr(worker.reward_service, "sync_user_rewards", _fake_sync_user_rewards)
    monkeypatch.setattr(worker, "record_event", _fake_record_event)
    monkeypatch.setattr(worker, "bump_cache_namespace", _fake_bump_cache_namespace)

    payload = json.dumps({"job_type": "attempt_complete", "user_id": 17, "attempt_id": 99})
    await worker.process_answer_postprocess(payload)
    await worker.process_answer_postprocess(payload)

    assert fake_session.commits == 1
    assert calls["rewards_sync"] == 1
    assert calls["events"].count(("attempt_completed", 1)) == 1
    assert calls["events"].count(("streak_day", 1)) == 1
    assert calls["cache"] == 1
