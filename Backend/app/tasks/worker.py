import asyncio
import json
import logging
from typing import Optional

from app.cache.redis_cache import (
    NS_LEADERBOARD,
    NS_TEST_SUMMARY,
    bump_cache_namespace,
    get_redis_client,
)
from app.db.session import AsyncSessionLocal
from app.models.answer import Answer
from app.repositories import analytics_repo, test_attempt_repo
from app.services.ai_gamification_service import AI_GAMIFY_QUEUE, process_ai_gamification_job
from app.services.challenge_service import ChallengeEventType, record_event
from app.services import reward_service
from app.tasks.task_queue import ANALYTICS_REFRESH_QUEUE

logger = logging.getLogger("worker")
OPEN_GRADING_MAX_RETRIES = 5
IDEMPOTENCY_DONE_TTL_SECONDS = 30 * 24 * 3600
IDEMPOTENCY_LOCK_TTL_SECONDS = 5 * 60


def _normalize_open_grading_payload(job_payload: str) -> dict:
    data = json.loads(job_payload)
    if not isinstance(data, dict):
        raise ValueError("Open grading payload must be a JSON object")
    return data


async def _requeue_open_grading_job(data: dict, retries: int) -> None:
    payload = dict(data)
    payload["retries"] = int(retries)
    redis = get_redis_client()
    await redis.rpush("grading:open", json.dumps(payload))


async def _claim_idempotent_job(kind: str, identifier: int | str | None) -> tuple[bool, tuple[object, str, str] | None]:
    if identifier is None:
        return True, None

    done_key = f"celery:done:{kind}:{identifier}"
    lock_key = f"celery:lock:{kind}:{identifier}"
    try:
        redis = get_redis_client()
        if await redis.get(done_key):
            logger.info("Skipping duplicate %s job id=%s", kind, identifier)
            return False, None
        acquired = await redis.set(lock_key, "1", ex=IDEMPOTENCY_LOCK_TTL_SECONDS, nx=True)
        if not acquired:
            logger.info("Skipping already-running %s job id=%s", kind, identifier)
            return False, None
        return True, (redis, done_key, lock_key)
    except Exception:
        logger.exception("Idempotency check failed for %s job id=%s; continuing without guard", kind, identifier)
        return True, None


async def _mark_idempotent_job_done(context: tuple[object, str, str] | None) -> None:
    if context is None:
        return
    redis, done_key, lock_key = context
    try:
        await redis.set(done_key, "1", ex=IDEMPOTENCY_DONE_TTL_SECONDS)
        await redis.delete(lock_key)
    except Exception:
        logger.exception("Failed to mark idempotent job done: %s", done_key)


async def _release_idempotent_job_lock(context: tuple[object, str, str] | None) -> None:
    if context is None:
        return
    redis, _done_key, lock_key = context
    try:
        await redis.delete(lock_key)
    except Exception:
        logger.exception("Failed to release idempotent job lock: %s", lock_key)


async def process_job(
    job_payload: str,
    *,
    requeue_on_missing: bool = True,
    raise_errors: bool = False,
) -> None:
    try:
        data = _normalize_open_grading_payload(job_payload)
    except Exception:
        logger.exception("Invalid job payload (not json): %s", job_payload)
        if raise_errors:
            raise
        return

    answer_id_raw = data.get("answer_id")
    retries = int(data.get("retries") or 0)
    try:
        answer_id = int(answer_id_raw) if answer_id_raw is not None else None
    except (TypeError, ValueError):
        answer_id = None
    user_id = data.get("user_id")
    logger.info(
        "Open answer queued for manual grading: answer_id=%s user_id=%s retries=%s",
        answer_id,
        user_id,
        retries,
    )

    if answer_id is None:
        logger.warning("Job missing answer_id: %s", data)
        return

    # Ensure record exists and run light post-process hooks for stable state.
    async with AsyncSessionLocal() as session:
        try:
            ans: Optional[Answer] = await session.get(Answer, answer_id)
            if ans is None:
                await session.rollback()
                if requeue_on_missing and retries < OPEN_GRADING_MAX_RETRIES:
                    await _requeue_open_grading_job(data, retries + 1)
                    logger.warning(
                        "Answer %s not found in DB, requeued open-grading job (attempt %s/%s)",
                        answer_id,
                        retries + 1,
                        OPEN_GRADING_MAX_RETRIES,
                    )
                else:
                    logger.error(
                        "Answer %s not found in DB after %s retries, dropping open-grading job",
                        answer_id,
                        retries,
                    )
                if raise_errors:
                    raise LookupError(f"Answer {answer_id} not found")
                return

            if ans.attempt_id is not None:
                attempt = await test_attempt_repo.get_attempt(session, int(ans.attempt_id))
                if attempt is not None:
                    await test_attempt_repo.refresh_attempt_scores(session, attempt)

            await session.commit()
            logger.info("Open answer %s is pending manual grading", answer_id)
        except Exception:
            await session.rollback()
            logger.exception("Failed to process open grading job for answer_id=%s", answer_id)
            if raise_errors:
                raise
            return

    try:
        await bump_cache_namespace(NS_LEADERBOARD, NS_TEST_SUMMARY)
    except Exception:
        logger.exception("Failed to invalidate caches after open grading postprocess for answer_id=%s", answer_id)


async def process_answer_postprocess(job_payload: str, *, raise_errors: bool = False) -> None:
    try:
        data = json.loads(job_payload)
    except Exception:
        logger.exception("Invalid analytics job payload: %s", job_payload)
        if raise_errors:
            raise
        return

    job_type = str(data.get("job_type") or "answer")
    user_id = data.get("user_id")
    test_id = data.get("test_id")
    attempt_id = data.get("attempt_id")
    points_delta = float(data.get("points_delta") or 0.0)
    mark_active = bool(data.get("mark_active"))

    if user_id is None:
        logger.warning("Analytics job missing user_id: %s", data)
        if raise_errors:
            raise ValueError("Analytics job missing user_id")
        return

    idempotency_context: tuple[object, str, str] | None = None
    if job_type == "attempt_complete" and attempt_id is not None:
        should_run, idempotency_context = await _claim_idempotent_job("answers_postprocess", int(attempt_id))
        if not should_run:
            return

    async with AsyncSessionLocal() as session:
        try:
            if job_type == "attempt_complete":
                await reward_service.sync_user_rewards(session, int(user_id))
                await record_event(
                    session,
                    user_id=int(user_id),
                    event_type=ChallengeEventType.ATTEMPT_COMPLETED,
                    increment=1,
                )
                await record_event(
                    session,
                    user_id=int(user_id),
                    event_type=ChallengeEventType.STREAK_DAY,
                    increment=1,
                )
            else:
                if test_id is None:
                    logger.warning("Analytics answer job missing test_id: %s", data)
                    await session.rollback()
                    await _release_idempotent_job_lock(idempotency_context)
                    if raise_errors:
                        raise ValueError("Analytics answer job missing test_id")
                    return
                if points_delta != 0 or mark_active:
                    await analytics_repo.create_or_update_analytics(
                        session,
                        user_id=user_id,
                        points_delta=points_delta,
                        mark_active=mark_active,
                    )
                if attempt_id is not None:
                    attempt = await test_attempt_repo.get_attempt(session, int(attempt_id))
                    if attempt is not None:
                        await test_attempt_repo.refresh_attempt_scores(session, attempt)
            await session.commit()
            await _mark_idempotent_job_done(idempotency_context)
        except Exception:
            await session.rollback()
            await _release_idempotent_job_lock(idempotency_context)
            logger.exception("Failed to process answer postprocess job: %s", data)
            if raise_errors:
                raise
            return

    try:
        await bump_cache_namespace(NS_LEADERBOARD, NS_TEST_SUMMARY)
    except Exception:
        logger.exception("Failed to invalidate caches after answer postprocess for test=%s user=%s", test_id, user_id)


async def process_analytics_refresh(job_payload: str, *, raise_errors: bool = False) -> None:
    try:
        data = json.loads(job_payload)
    except Exception:
        logger.exception("Invalid analytics refresh payload: %s", job_payload)
        if raise_errors:
            raise
        return

    user_id = data.get("user_id")
    source_event = str(data.get("source_event") or "analytics_refresh")
    namespaces = data.get("namespaces") or [NS_LEADERBOARD, NS_TEST_SUMMARY]
    if not isinstance(namespaces, list):
        namespaces = [NS_LEADERBOARD, NS_TEST_SUMMARY]

    if user_id is not None:
        async with AsyncSessionLocal() as session:
            try:
                await analytics_repo.sync_user_gamification_side_effects(
                    session,
                    user_id=int(user_id),
                    source_event=source_event,
                )
                await session.commit()
            except Exception:
                await session.rollback()
                logger.exception("Failed to refresh analytics side effects for user_id=%s", user_id)
                if raise_errors:
                    raise
                return

    try:
        await bump_cache_namespace(*(str(namespace) for namespace in namespaces if namespace))
    except Exception:
        logger.exception("Failed to invalidate caches after analytics refresh: %s", data)
        if raise_errors:
            raise


async def run_worker() -> None:
    r = get_redis_client()
    logger.info(
        "Worker started: polling grading:open, answers:postprocess, %s and %s",
        AI_GAMIFY_QUEUE,
        ANALYTICS_REFRESH_QUEUE,
    )
    while True:
        try:
            # BLPOP returns tuple (key, value) or None
            item = await r.blpop(["grading:open", "answers:postprocess", AI_GAMIFY_QUEUE, ANALYTICS_REFRESH_QUEUE], timeout=5)
            if not item:
                # timeout - loop again (allows graceful shutdown)
                await asyncio.sleep(0.1)
                continue
            queue_name, payload = item
            if queue_name == "grading:open":
                await process_job(payload)
            elif queue_name == "answers:postprocess":
                await process_answer_postprocess(payload)
            elif queue_name == AI_GAMIFY_QUEUE:
                try:
                    parsed = json.loads(payload)
                    job_id = int(parsed["job_id"])
                except Exception:
                    logger.exception("Invalid AI job payload: %s", payload)
                    continue
                await process_ai_gamification_job(job_id)
            elif queue_name == ANALYTICS_REFRESH_QUEUE:
                await process_analytics_refresh(payload)
        except asyncio.CancelledError:
            logger.info("Worker cancelled, exiting")
            break
        except Exception:
            logger.exception("Worker loop error, sleeping briefly")
            await asyncio.sleep(1)


if __name__ == "__main__":
    import sys
    logging.basicConfig(stream=sys.stdout, level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    try:
        asyncio.run(run_worker())
    except KeyboardInterrupt:
        logger.info("Worker stopped by KeyboardInterrupt")
