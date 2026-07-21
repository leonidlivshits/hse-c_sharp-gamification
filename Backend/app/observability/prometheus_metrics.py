from __future__ import annotations

import logging
import math
import re
import time
from typing import Iterable

from sqlalchemy import text

from app.cache.redis_cache import get_redis_client
from app.db.session import engine

logger = logging.getLogger(__name__)

try:
    from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest
except ModuleNotFoundError:  # pragma: no cover - safety net for stale dev images
    CONTENT_TYPE_LATEST = "text/plain; version=0.0.4; charset=utf-8"
    _FALLBACK_COLLECTORS: list["_FallbackMetric"] = []

    class _FallbackMetricChild:
        def __init__(self, parent: "_FallbackMetric", label_values: tuple[str, ...]) -> None:
            self.parent = parent
            self.label_values = label_values

        def inc(self, amount: float = 1.0) -> None:
            self.parent.values[self.label_values] = self.parent.values.get(self.label_values, 0.0) + float(amount)

        def dec(self, amount: float = 1.0) -> None:
            self.parent.values[self.label_values] = self.parent.values.get(self.label_values, 0.0) - float(amount)

        def observe(self, value: float) -> None:
            self.parent.observe(self.label_values, float(value))

    class _FallbackMetric:
        metric_type = "untyped"

        def __init__(self, name: str, documentation: str, labelnames: tuple[str, ...] = (), **kwargs) -> None:
            self.name = name
            self.documentation = documentation
            self.labelnames = tuple(labelnames)
            self.values: dict[tuple[str, ...], float] = {}
            self.buckets = tuple(float(bucket) for bucket in kwargs.get("buckets", ()))
            self.histograms: dict[tuple[str, ...], dict[str, object]] = {}
            _FALLBACK_COLLECTORS.append(self)

        def labels(self, *args, **kwargs) -> _FallbackMetricChild:
            if args and kwargs:
                raise ValueError("Use either positional or keyword labels")
            if kwargs:
                label_values = tuple(str(kwargs[name]) for name in self.labelnames)
            else:
                label_values = tuple(str(value) for value in args)
            if len(label_values) != len(self.labelnames):
                raise ValueError("Incorrect number of label values")
            return _FallbackMetricChild(self, label_values)

        def observe(self, label_values: tuple[str, ...], value: float) -> None:
            state = self.histograms.setdefault(
                label_values,
                {"count": 0.0, "sum": 0.0, "buckets": {bucket: 0.0 for bucket in self.buckets}},
            )
            state["count"] = float(state["count"]) + 1.0
            state["sum"] = float(state["sum"]) + value
            bucket_counts = state["buckets"]
            assert isinstance(bucket_counts, dict)
            for bucket in self.buckets:
                if value <= bucket:
                    bucket_counts[bucket] = float(bucket_counts[bucket]) + 1.0

        def _label_dict(self, label_values: tuple[str, ...], extra: dict[str, str] | None = None) -> dict[str, str]:
            labels = {name: value for name, value in zip(self.labelnames, label_values)}
            if extra:
                labels.update(extra)
            return labels

        def render(self) -> list[str]:
            lines = [f"# HELP {self.name} {self.documentation}", f"# TYPE {self.name} {self.metric_type}"]
            if self.metric_type != "histogram":
                for label_values, value in self.values.items():
                    lines.append(_sample(self.name, value, self._label_dict(label_values)))
                return lines

            for label_values, state in self.histograms.items():
                count = float(state["count"])
                total = float(state["sum"])
                bucket_counts = state["buckets"]
                assert isinstance(bucket_counts, dict)
                for bucket in self.buckets:
                    lines.append(
                        _sample(
                            f"{self.name}_bucket",
                            bucket_counts[bucket],
                            self._label_dict(label_values, {"le": str(bucket)}),
                        )
                    )
                lines.append(_sample(f"{self.name}_bucket", count, self._label_dict(label_values, {"le": "+Inf"})))
                lines.append(_sample(f"{self.name}_count", count, self._label_dict(label_values)))
                lines.append(_sample(f"{self.name}_sum", total, self._label_dict(label_values)))
            return lines

    class Counter(_FallbackMetric):
        metric_type = "counter"

    class Gauge(_FallbackMetric):
        metric_type = "gauge"

    class Histogram(_FallbackMetric):
        metric_type = "histogram"

    def generate_latest() -> bytes:
        lines: list[str] = []
        for collector in _FALLBACK_COLLECTORS:
            lines.extend(collector.render())
        return ("\n".join(lines) + "\n").encode("utf-8")

_UUID_SEGMENT_RE = re.compile(
    r"/[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}(?=/|$)"
)
_INT_SEGMENT_RE = re.compile(r"/\d+(?=/|$)")

CELERY_METRICS_KEY = "metrics:celery:tasks"

CELERY_QUEUE_NAMES = ("grading", "answers", "ai", "analytics")
LEGACY_QUEUE_NAMES = ("grading:open", "answers:postprocess", "ai:gamify", "analytics:refresh")

API_REQUESTS_TOTAL = Counter(
    "hse_api_requests_total",
    "Total HTTP API requests.",
    ("method", "path", "status"),
)
API_REQUEST_DURATION_SECONDS = Histogram(
    "hse_api_request_duration_seconds",
    "HTTP API request latency in seconds.",
    ("method", "path"),
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)
API_IN_PROGRESS = Gauge(
    "hse_api_requests_in_progress",
    "Current in-progress HTTP API requests.",
    ("method", "path"),
)


def normalize_path(path: str) -> str:
    normalized = _UUID_SEGMENT_RE.sub("/{id}", path)
    normalized = _INT_SEGMENT_RE.sub("/{id}", normalized)
    return normalized or "/"


def path_label_from_request(request) -> str:
    route = request.scope.get("route")
    route_path = getattr(route, "path", None)
    if route_path:
        return str(route_path)
    return normalize_path(request.url.path)


def record_api_request(*, method: str, path: str, status_code: int, duration_seconds: float) -> None:
    method_label = method.upper()
    path_label = normalize_path(path)
    status_label = str(int(status_code))
    API_REQUESTS_TOTAL.labels(method_label, path_label, status_label).inc()
    API_REQUEST_DURATION_SECONDS.labels(method_label, path_label).observe(max(float(duration_seconds), 0.0))


def api_request_started(*, method: str, path: str) -> None:
    API_IN_PROGRESS.labels(method.upper(), normalize_path(path)).inc()


def api_request_finished(*, method: str, path: str) -> None:
    API_IN_PROGRESS.labels(method.upper(), normalize_path(path)).dec()


async def record_celery_task_started(task_name: str) -> None:
    try:
        redis = get_redis_client()
        await redis.hincrby(CELERY_METRICS_KEY, f"{task_name}:started", 1)
    except Exception:
        logger.exception("Failed to record Celery task start metric: %s", task_name)


async def record_celery_task_finished(task_name: str, *, status: str, duration_seconds: float) -> None:
    safe_duration = max(float(duration_seconds), 0.0)
    try:
        redis = get_redis_client()
        pipe = redis.pipeline(transaction=False)
        pipe.hincrby(CELERY_METRICS_KEY, f"{task_name}:{status}", 1)
        pipe.hincrbyfloat(CELERY_METRICS_KEY, f"{task_name}:duration_seconds_sum", safe_duration)
        pipe.hincrby(CELERY_METRICS_KEY, f"{task_name}:duration_seconds_count", 1)
        await pipe.execute()

        current_max = await redis.hget(CELERY_METRICS_KEY, f"{task_name}:duration_seconds_max")
        try:
            current_max_value = float(current_max or 0.0)
        except (TypeError, ValueError):
            current_max_value = 0.0
        if safe_duration > current_max_value:
            await redis.hset(CELERY_METRICS_KEY, f"{task_name}:duration_seconds_max", safe_duration)
    except Exception:
        logger.exception("Failed to record Celery task finish metric: %s status=%s", task_name, status)


def _escape_label(value: str) -> str:
    return value.replace("\\", "\\\\").replace("\n", "\\n").replace('"', '\\"')


def _labels(labels: dict[str, str] | None = None) -> str:
    if not labels:
        return ""
    body = ",".join(f'{key}="{_escape_label(str(value))}"' for key, value in sorted(labels.items()))
    return "{" + body + "}"


def _sample(name: str, value: float | int, labels: dict[str, str] | None = None) -> str:
    numeric_value = float(value)
    if math.isnan(numeric_value) or math.isinf(numeric_value):
        numeric_value = 0.0
    return f"{name}{_labels(labels)} {numeric_value}"


def _metric_block(name: str, help_text: str, metric_type: str, samples: Iterable[str]) -> list[str]:
    lines = [f"# HELP {name} {help_text}", f"# TYPE {name} {metric_type}"]
    lines.extend(samples)
    return lines


async def _queue_depth_samples() -> list[str]:
    samples: list[str] = []
    try:
        redis = get_redis_client()
        for queue_name in CELERY_QUEUE_NAMES:
            samples.append(
                _sample(
                    "hse_queue_depth",
                    int(await redis.llen(queue_name)),
                    {"backend": "celery", "queue": queue_name},
                )
            )
        for queue_name in LEGACY_QUEUE_NAMES:
            samples.append(
                _sample(
                    "hse_queue_depth",
                    int(await redis.llen(queue_name)),
                    {"backend": "redis_list", "queue": queue_name},
                )
            )
    except Exception:
        logger.exception("Failed to collect queue depth metrics")
    return samples


async def _celery_task_samples() -> list[str]:
    samples: list[str] = []
    try:
        redis = get_redis_client()
        raw = await redis.hgetall(CELERY_METRICS_KEY)
    except Exception:
        logger.exception("Failed to collect Celery task metrics")
        raw = {}

    task_names = sorted({str(field).split(":", 1)[0] for field in raw.keys() if ":" in str(field)})
    for task_name in task_names:
        for status in ("started", "succeeded", "failed"):
            try:
                value = int(float(raw.get(f"{task_name}:{status}", 0) or 0))
            except (TypeError, ValueError):
                value = 0
            samples.append(
                _sample(
                    "hse_celery_tasks_total",
                    value,
                    {"task": task_name, "status": status},
                )
            )
    return samples


async def _celery_duration_samples() -> tuple[list[str], list[str], list[str]]:
    count_samples: list[str] = []
    sum_samples: list[str] = []
    max_samples: list[str] = []
    try:
        redis = get_redis_client()
        raw = await redis.hgetall(CELERY_METRICS_KEY)
    except Exception:
        logger.exception("Failed to collect Celery duration metrics")
        raw = {}

    task_names = sorted({str(field).split(":", 1)[0] for field in raw.keys() if ":" in str(field)})
    for task_name in task_names:
        labels = {"task": task_name}
        count_samples.append(_sample("hse_celery_task_duration_seconds_count", raw.get(f"{task_name}:duration_seconds_count", 0) or 0, labels))
        sum_samples.append(_sample("hse_celery_task_duration_seconds_sum", raw.get(f"{task_name}:duration_seconds_sum", 0) or 0, labels))
        max_samples.append(_sample("hse_celery_task_duration_seconds_max", raw.get(f"{task_name}:duration_seconds_max", 0) or 0, labels))
    return count_samples, sum_samples, max_samples


async def _db_samples() -> list[str]:
    started = time.perf_counter()
    up = 0
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        up = 1
    except Exception:
        logger.exception("Failed to collect DB health metric")
    latency = time.perf_counter() - started

    samples = [
        _sample("hse_db_up", up),
        _sample("hse_db_latency_seconds", latency),
    ]
    pool = getattr(engine.sync_engine, "pool", None)
    for attr_name, metric_name in (
        ("size", "hse_db_pool_size"),
        ("checkedin", "hse_db_pool_checked_in"),
        ("checkedout", "hse_db_pool_checked_out"),
        ("overflow", "hse_db_pool_overflow"),
    ):
        attr = getattr(pool, attr_name, None)
        if not callable(attr):
            continue
        try:
            samples.append(_sample(metric_name, attr()))
        except Exception:
            continue
    return samples


async def _redis_samples() -> list[str]:
    started = time.perf_counter()
    up = 0
    try:
        redis = get_redis_client()
        await redis.ping()
        up = 1
    except Exception:
        logger.exception("Failed to collect Redis health metric")
    return [
        _sample("hse_redis_up", up),
        _sample("hse_redis_latency_seconds", time.perf_counter() - started),
    ]


async def render_dynamic_prometheus_metrics() -> str:
    lines: list[str] = []

    lines.extend(
        _metric_block(
            "hse_queue_depth",
            "Current Redis/Celery queue depth.",
            "gauge",
            await _queue_depth_samples(),
        )
    )
    lines.extend(
        _metric_block(
            "hse_celery_tasks_total",
            "Celery task execution counters recorded by workers.",
            "counter",
            await _celery_task_samples(),
        )
    )
    duration_count, duration_sum, duration_max = await _celery_duration_samples()
    lines.extend(
        _metric_block(
            "hse_celery_task_duration_seconds_count",
            "Celery task duration observation count.",
            "counter",
            duration_count,
        )
    )
    lines.extend(
        _metric_block(
            "hse_celery_task_duration_seconds_sum",
            "Celery task duration sum in seconds.",
            "counter",
            duration_sum,
        )
    )
    lines.extend(
        _metric_block(
            "hse_celery_task_duration_seconds_max",
            "Maximum observed Celery task duration in seconds.",
            "gauge",
            duration_max,
        )
    )
    db_samples = await _db_samples()
    for metric_name, help_text in (
        ("hse_db_up", "Database availability."),
        ("hse_db_latency_seconds", "Database SELECT 1 latency."),
        ("hse_db_pool_size", "Configured database pool size."),
        ("hse_db_pool_checked_in", "Database pool checked-in connections."),
        ("hse_db_pool_checked_out", "Database pool checked-out connections."),
        ("hse_db_pool_overflow", "Database pool overflow connections."),
    ):
        metric_samples = [sample for sample in db_samples if sample.startswith(metric_name)]
        if metric_samples:
            lines.extend(_metric_block(metric_name, help_text, "gauge", metric_samples))

    redis_samples = await _redis_samples()
    lines.extend(
        _metric_block(
            "hse_redis_up",
            "Redis availability.",
            "gauge",
            [sample for sample in redis_samples if sample.startswith("hse_redis_up")],
        )
    )
    lines.extend(
        _metric_block(
            "hse_redis_latency_seconds",
            "Redis PING latency.",
            "gauge",
            [sample for sample in redis_samples if sample.startswith("hse_redis_latency_seconds")],
        )
    )

    return "\n".join(lines) + "\n"


async def prometheus_payload() -> bytes:
    base_payload = generate_latest()
    dynamic_payload = (await render_dynamic_prometheus_metrics()).encode("utf-8")
    return base_payload + b"\n" + dynamic_payload
