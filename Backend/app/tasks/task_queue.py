from __future__ import annotations

import json
import logging
from typing import Any

from app.cache.redis_cache import get_redis_client
from app.core.config import settings

logger = logging.getLogger(__name__)

OPEN_GRADING_QUEUE = "grading:open"
ANSWERS_POSTPROCESS_QUEUE = "answers:postprocess"
AI_GAMIFY_QUEUE = "ai:gamify"
ANALYTICS_REFRESH_QUEUE = "analytics:refresh"


def _use_celery() -> bool:
    return settings.get_background_tasks_backend() == "celery"


def _send_celery_task(task_name: str, payload: dict[str, Any], *, queue: str) -> None:
    from app.tasks.celery_app import celery_app

    celery_app.send_task(task_name, args=[payload], queue=queue)


async def _enqueue_redis(queue_name: str, payload: dict[str, Any]) -> None:
    redis = get_redis_client()
    await redis.rpush(queue_name, json.dumps(payload))


async def enqueue_open_answer_grading(*, answer_id: int, user_id: int, retries: int = 0) -> None:
    payload = {"answer_id": int(answer_id), "user_id": int(user_id), "retries": int(retries)}
    if _use_celery():
        _send_celery_task("open_answer_grading", payload, queue="grading")
        return
    await _enqueue_redis(OPEN_GRADING_QUEUE, payload)


async def enqueue_answers_postprocess(
    *,
    user_id: int,
    test_id: int | None = None,
    attempt_id: int | None = None,
    job_type: str = "answer",
    points_delta: float = 0.0,
    answers_count: int = 0,
    mark_active: bool = False,
    source_event: str | None = None,
) -> None:
    payload: dict[str, Any] = {
        "job_type": job_type,
        "user_id": int(user_id),
        "test_id": int(test_id) if test_id is not None else None,
        "attempt_id": int(attempt_id) if attempt_id is not None else None,
        "points_delta": float(points_delta or 0.0),
        "answers_count": int(answers_count or 0),
        "mark_active": bool(mark_active),
    }
    if source_event is not None:
        payload["source_event"] = source_event
    if _use_celery():
        _send_celery_task("answers_postprocess", payload, queue="answers")
        return
    await _enqueue_redis(ANSWERS_POSTPROCESS_QUEUE, payload)


async def enqueue_ai_gamification_job(job_id: int) -> None:
    payload = {"job_id": int(job_id)}
    if _use_celery():
        _send_celery_task("ai_gamification", payload, queue="ai")
        return
    await _enqueue_redis(AI_GAMIFY_QUEUE, payload)


async def enqueue_analytics_refresh(
    *,
    user_id: int | None = None,
    source_event: str = "analytics_refresh",
    namespaces: list[str] | None = None,
) -> None:
    payload: dict[str, Any] = {
        "user_id": int(user_id) if user_id is not None else None,
        "source_event": source_event,
        "namespaces": namespaces or [],
    }
    if _use_celery():
        _send_celery_task("analytics_refresh", payload, queue="analytics")
        return
    await _enqueue_redis(ANALYTICS_REFRESH_QUEUE, payload)
