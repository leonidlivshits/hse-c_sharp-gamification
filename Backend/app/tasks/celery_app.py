from __future__ import annotations

from celery import Celery

from app.core.config import settings


celery_app = Celery(
    "hse_csharp_gamification",
    broker=settings.get_celery_broker_url(),
    backend=settings.get_celery_result_backend(),
    include=["app.tasks.celery_tasks"],
)

celery_app.conf.update(
    accept_content=["json"],
    result_serializer="json",
    task_acks_late=True,
    task_default_queue="default",
    task_routes={
        "open_answer_grading": {"queue": "grading"},
        "answers_postprocess": {"queue": "answers"},
        "ai_gamification": {"queue": "ai"},
        "analytics_refresh": {"queue": "analytics"},
    },
    task_serializer="json",
    task_soft_time_limit=int(settings.celery_task_soft_time_limit_seconds),
    task_time_limit=int(settings.celery_task_time_limit_seconds),
    task_track_started=True,
    timezone="UTC",
    worker_concurrency=int(settings.celery_worker_concurrency),
    worker_prefetch_multiplier=1,
)
