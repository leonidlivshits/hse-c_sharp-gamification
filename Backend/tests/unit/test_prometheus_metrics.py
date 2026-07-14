import pytest

from app.observability import prometheus_metrics

pytestmark = pytest.mark.asyncio


class _FakePipeline:
    def __init__(self, redis):
        self.redis = redis
        self.calls = []

    def hincrby(self, key, field, amount):
        self.calls.append(("hincrby", key, field, amount))
        return self

    def hincrbyfloat(self, key, field, amount):
        self.calls.append(("hincrbyfloat", key, field, amount))
        return self

    async def execute(self):
        for operation, key, field, amount in self.calls:
            if operation == "hincrby":
                await self.redis.hincrby(key, field, amount)
            elif operation == "hincrbyfloat":
                await self.redis.hincrbyfloat(key, field, amount)
        return []


class _FakeRedis:
    def __init__(self):
        self.hashes = {}
        self.lists = {
            "grading": ["a", "b"],
            "answers": ["a"],
            "ai": [],
            "analytics": [],
        }

    def pipeline(self, transaction=False):
        del transaction
        return _FakePipeline(self)

    async def hincrby(self, key, field, amount):
        bucket = self.hashes.setdefault(key, {})
        bucket[field] = int(bucket.get(field, 0) or 0) + int(amount)
        return bucket[field]

    async def hincrbyfloat(self, key, field, amount):
        bucket = self.hashes.setdefault(key, {})
        bucket[field] = float(bucket.get(field, 0) or 0.0) + float(amount)
        return bucket[field]

    async def hget(self, key, field):
        return self.hashes.get(key, {}).get(field)

    async def hset(self, key, field, value):
        bucket = self.hashes.setdefault(key, {})
        bucket[field] = value
        return 1

    async def hgetall(self, key):
        return dict(self.hashes.get(key, {}))

    async def llen(self, key):
        return len(self.lists.get(key, []))

    async def ping(self):
        return True


async def test_celery_metrics_are_recorded_and_rendered_from_redis(monkeypatch):
    fake_redis = _FakeRedis()

    async def fake_db_samples():
        return [
            "hse_db_up 1.0",
            "hse_db_latency_seconds 0.001",
        ]

    monkeypatch.setattr(prometheus_metrics, "get_redis_client", lambda: fake_redis)
    monkeypatch.setattr(prometheus_metrics, "_db_samples", fake_db_samples)

    await prometheus_metrics.record_celery_task_started("answers_postprocess")
    await prometheus_metrics.record_celery_task_finished(
        "answers_postprocess",
        status="succeeded",
        duration_seconds=0.25,
    )

    rendered = await prometheus_metrics.render_dynamic_prometheus_metrics()

    assert 'hse_celery_tasks_total{status="started",task="answers_postprocess"} 1.0' in rendered
    assert 'hse_celery_tasks_total{status="succeeded",task="answers_postprocess"} 1.0' in rendered
    assert 'hse_celery_task_duration_seconds_count{task="answers_postprocess"} 1.0' in rendered
    assert 'hse_celery_task_duration_seconds_sum{task="answers_postprocess"} 0.25' in rendered
    assert 'hse_queue_depth{backend="celery",queue="grading"} 2.0' in rendered
