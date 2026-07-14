from __future__ import annotations

import asyncio
import json
import logging
import time
from typing import Any

from app.core.config import settings
from app.observability.prometheus_metrics import record_celery_task_finished, record_celery_task_started
from app.services.ai_gamification_service import process_ai_gamification_job
from app.tasks import worker
from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


def _run_async(coro):
    return asyncio.run(coro)


def _max_retries() -> int:
    return max(int(settings.celery_task_max_retries), 0)


def _run_with_metrics(task_name: str, coro) -> None:
    started = time.perf_counter()
    _run_async(record_celery_task_started(task_name))
    try:
        _run_async(coro)
    except Exception:
        _run_async(
            record_celery_task_finished(
                task_name,
                status="failed",
                duration_seconds=time.perf_counter() - started,
            )
        )
        raise
    _run_async(
        record_celery_task_finished(
            task_name,
            status="succeeded",
            duration_seconds=time.perf_counter() - started,
        )
    )


@celery_app.task(
    bind=True,
    name="open_answer_grading",
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    retry_kwargs={"max_retries": _max_retries()},
)
def open_answer_grading(self, payload: dict[str, Any]) -> None:
    logger.info("Celery open_answer_grading task started: %s", payload)
    _run_with_metrics(
        "open_answer_grading",
        worker.process_job(
            json.dumps(payload),
            requeue_on_missing=False,
            raise_errors=True,
        ),
    )


@celery_app.task(
    bind=True,
    name="answers_postprocess",
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    retry_kwargs={"max_retries": _max_retries()},
)
def answers_postprocess(self, payload: dict[str, Any]) -> None:
    logger.info("Celery answers_postprocess task started: %s", payload)
    _run_with_metrics(
        "answers_postprocess",
        worker.process_answer_postprocess(json.dumps(payload), raise_errors=True),
    )


@celery_app.task(
    bind=True,
    name="ai_gamification",
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    retry_kwargs={"max_retries": _max_retries()},
)
def ai_gamification(self, payload: dict[str, Any]) -> None:
    job_id = int(payload["job_id"])
    logger.info("Celery ai_gamification task started: job_id=%s", job_id)
    _run_with_metrics("ai_gamification", process_ai_gamification_job(job_id))


@celery_app.task(
    bind=True,
    name="analytics_refresh",
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    retry_kwargs={"max_retries": _max_retries()},
)
def analytics_refresh(self, payload: dict[str, Any]) -> None:
    logger.info("Celery analytics_refresh task started: %s", payload)
    _run_with_metrics(
        "analytics_refresh",
        worker.process_analytics_refresh(json.dumps(payload), raise_errors=True),
    )
