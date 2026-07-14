import pytest

from app.core.config import settings

pytestmark = pytest.mark.asyncio


def _patch_prometheus_runtime_collectors(monkeypatch):
    from app.observability import prometheus_metrics

    async def fake_queue_depth_samples():
        return ['hse_queue_depth{backend="celery",queue="answers"} 0.0']

    async def fake_celery_task_samples():
        return ['hse_celery_tasks_total{status="succeeded",task="answers_postprocess"} 1.0']

    async def fake_celery_duration_samples():
        return (
            ['hse_celery_task_duration_seconds_count{task="answers_postprocess"} 1.0'],
            ['hse_celery_task_duration_seconds_sum{task="answers_postprocess"} 0.01'],
            ['hse_celery_task_duration_seconds_max{task="answers_postprocess"} 0.01'],
        )

    async def fake_db_samples():
        return ["hse_db_up 1.0", "hse_db_latency_seconds 0.001"]

    async def fake_redis_samples():
        return ["hse_redis_up 1.0", "hse_redis_latency_seconds 0.001"]

    monkeypatch.setattr(prometheus_metrics, "_queue_depth_samples", fake_queue_depth_samples)
    monkeypatch.setattr(prometheus_metrics, "_celery_task_samples", fake_celery_task_samples)
    monkeypatch.setattr(prometheus_metrics, "_celery_duration_samples", fake_celery_duration_samples)
    monkeypatch.setattr(prometheus_metrics, "_db_samples", fake_db_samples)
    monkeypatch.setattr(prometheus_metrics, "_redis_samples", fake_redis_samples)


async def test_health_metrics_endpoint_returns_runtime_snapshot(client, monkeypatch):
    monkeypatch.setattr(settings, "app_env", "test")
    monkeypatch.setattr(settings, "monitoring_metrics_token", "")

    baseline_response = await client.get("/health/metrics")
    assert baseline_response.status_code == 200
    baseline_payload = baseline_response.json()
    baseline_requests_total = int(baseline_payload["requests_total"])

    live_response = await client.get("/health/live")
    assert live_response.status_code == 200

    snapshot_response = await client.get("/health/metrics")
    assert snapshot_response.status_code == 200
    payload = snapshot_response.json()

    assert payload["requests_total"] >= baseline_requests_total + 1
    assert payload["errors_total"] >= 0
    assert payload["rate_limited_total"] >= 0
    assert "status_class_counts" in payload
    assert "last_minute" in payload
    assert "top_endpoints" in payload
    assert isinstance(payload["top_endpoints"], list)


async def test_health_metrics_endpoint_requires_token_when_configured(client, monkeypatch):
    monkeypatch.setattr(settings, "monitoring_metrics_token", "metrics-secret-token")

    forbidden_no_header = await client.get("/health/metrics")
    assert forbidden_no_header.status_code == 403

    forbidden_wrong_header = await client.get("/health/metrics", headers={"X-Metrics-Token": "wrong-token"})
    assert forbidden_wrong_header.status_code == 403

    ok_response = await client.get("/health/metrics", headers={"X-Metrics-Token": "metrics-secret-token"})
    assert ok_response.status_code == 200

    ok_bearer_response = await client.get(
        "/health/metrics",
        headers={"Authorization": "Bearer metrics-secret-token"},
    )
    assert ok_bearer_response.status_code == 200


async def test_health_metrics_endpoint_requires_configured_token_outside_test_env(client, monkeypatch):
    monkeypatch.setattr(settings, "app_env", "production")
    monkeypatch.setattr(settings, "monitoring_metrics_token", "")

    response = await client.get("/health/metrics")
    assert response.status_code == 503
    assert "not configured" in response.json()["detail"].lower()


async def test_prometheus_metrics_endpoint_returns_text_exposition(client, monkeypatch):
    monkeypatch.setattr(settings, "app_env", "test")
    monkeypatch.setattr(settings, "monitoring_metrics_token", "")
    _patch_prometheus_runtime_collectors(monkeypatch)

    live_response = await client.get("/health/live")
    assert live_response.status_code == 200

    response = await client.get("/metrics")
    assert response.status_code == 200
    assert "text/plain" in response.headers["content-type"]
    body = response.text
    assert "# HELP hse_api_requests_total" in body
    assert "hse_api_request_duration_seconds_bucket" in body
    assert "# HELP hse_queue_depth" in body
    assert "# HELP hse_db_up" in body
    assert "# HELP hse_redis_up" in body


async def test_prometheus_metrics_endpoint_supports_bearer_token(client, monkeypatch):
    monkeypatch.setattr(settings, "monitoring_metrics_token", "metrics-secret-token")
    _patch_prometheus_runtime_collectors(monkeypatch)

    forbidden_response = await client.get("/metrics")
    assert forbidden_response.status_code == 403

    ok_response = await client.get(
        "/metrics",
        headers={"Authorization": "Bearer metrics-secret-token"},
    )
    assert ok_response.status_code == 200
