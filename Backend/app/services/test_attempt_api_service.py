from __future__ import annotations

import json
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import add_post_commit_task
from app.cache.redis_cache import get_redis_client
from app.core.config import settings
from app.core.test_attempts import AttemptBlockReason, build_attempt_view_state, is_deadline_passed
from app.repositories import test_attempt_repo
from app.schemas.test_attempt import TestAttemptQuotaRead, TestAttemptStateRead
from app.services.test_runtime import utcnow
from app.tasks.task_queue import enqueue_answers_postprocess


def resolve_block_reason_from_policy_error(exc: Exception) -> AttemptBlockReason | None:
    code = getattr(exc, "code", "")
    if code in {"no_attempts", "deadline_passed", "time_limit_exceeded"}:
        return code
    return None


async def build_attempt_quota_payload(
    db: AsyncSession,
    *,
    test_id: int,
    max_attempts: int,
    deadline: datetime | None,
    user_id: int,
    forced_block_reason: AttemptBlockReason | None = None,
) -> TestAttemptQuotaRead:
    completed_attempts = await test_attempt_repo.count_completed_attempts_for_user_test(db, user_id, test_id)
    active_attempt = await test_attempt_repo.get_active_attempt(db, user_id, test_id)
    attempt_state = build_attempt_view_state(
        max_attempts=max_attempts,
        completed_attempts=completed_attempts,
        has_active_attempt=active_attempt is not None,
        deadline_passed=is_deadline_passed(deadline),
        forced_block_reason=forced_block_reason,
    )
    return TestAttemptQuotaRead(
        test_id=test_id,
        max_attempts=attempt_state["max_attempts"],
        completed_attempts=attempt_state["completed_attempts"],
        remaining_attempts=attempt_state["remaining_attempts"],
        has_active_attempt=attempt_state["has_active_attempt"],
        ui_status=attempt_state["ui_status"],
        progress_state=attempt_state["progress_state"],
        attempt_state=attempt_state["attempt_state"],
        can_start=attempt_state["can_start"],
        can_resume=attempt_state["can_resume"],
        block_reason=attempt_state["block_reason"],
    )


def build_attempt_state_payload(
    *,
    test,
    attempt,
    expired_reason: str | None = None,
) -> TestAttemptStateRead:
    reference_time = attempt.completed_at or utcnow()
    elapsed_seconds = max(int((reference_time - attempt.started_at).total_seconds()), 0)

    remaining_seconds: int | None = None
    time_limit_minutes = test.time_limit_minutes
    if time_limit_minutes is not None:
        total_limit_seconds = int(time_limit_minutes) * 60
        remaining_seconds = max(total_limit_seconds - elapsed_seconds, 0)

    inferred_reason = expired_reason
    if inferred_reason is None and time_limit_minutes is not None and remaining_seconds == 0:
        inferred_reason = "time_limit"
    if inferred_reason is None and test.deadline is not None and reference_time >= test.deadline:
        inferred_reason = "deadline"

    return TestAttemptStateRead(
        attempt_id=attempt.id,
        test_id=attempt.test_id,
        status=attempt.status,
        started_at=attempt.started_at,
        completed_at=attempt.completed_at,
        time_limit_minutes=time_limit_minutes,
        elapsed_seconds=elapsed_seconds,
        remaining_seconds=remaining_seconds,
        is_expired=inferred_reason in {"time_limit", "deadline"},
        expired_reason=inferred_reason,
    )


def schedule_attempt_completion_postprocess(
    db: AsyncSession,
    *,
    user_id: int,
    test_id: int,
    attempt_id: int,
    points_delta: float = 0.0,
    answers_count: int = 0,
) -> None:
    async def enqueue_after_commit() -> None:
        try:
            if settings.get_background_tasks_backend() != "celery":
                redis = get_redis_client()
                payload = {
                    "job_type": "attempt_complete",
                    "user_id": int(user_id),
                    "test_id": int(test_id),
                    "attempt_id": int(attempt_id),
                    "points_delta": float(points_delta or 0.0),
                    "answers_count": int(answers_count or 0),
                    "source_event": "attempt_completed",
                }
                await redis.rpush("answers:postprocess", json.dumps(payload))
                return
            await enqueue_answers_postprocess(
                user_id=int(user_id),
                test_id=int(test_id),
                attempt_id=int(attempt_id),
                job_type="attempt_complete",
                points_delta=float(points_delta or 0.0),
                answers_count=int(answers_count or 0),
                source_event="attempt_completed",
            )
        except Exception:
            # Queue failures must not break successful submit responses.
            pass

    add_post_commit_task(db, enqueue_after_commit)
