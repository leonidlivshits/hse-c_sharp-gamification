from __future__ import annotations

import json
import logging
import re
from datetime import UTC, datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import add_post_commit_task
from app.api.v1.access import can_manage_material, can_manage_test
from app.cache.redis_cache import (
    NS_MATERIALS,
    NS_QUESTIONS,
    NS_TEST_CONTENT,
    NS_TESTS,
    bump_cache_namespace,
    get_redis_client,
)
from app.db.session import AsyncSessionLocal
from app.models.material_block import MaterialBlock
from app.models.user import User
from app.core.config import settings
from app.repositories import ai_gamification_repo, material_repo, question_repo, test_repo
from app.schemas.ai_gamification import (
    AIGamifyApplyRequest,
    AIGamifyDraft,
    AIGamifyRequest,
    AIGamifyTargetType,
)
from app.services.ai_service import (
    AIGamificationConfigError,
    AIGamificationDisabledError,
    ensure_ai_gamification_ready,
    generate_gamification_draft,
)
from app.tasks.task_queue import enqueue_ai_gamification_job


logger = logging.getLogger(__name__)

AI_GAMIFY_QUEUE = "ai:gamify"
AI_GAMIFY_DLQ = "ai:gamify:dlq"
AI_GAMIFY_RETRY_KEY_PREFIX = "ai:gamify:retry"
AI_GAMIFY_METRICS_KEY = "ai:gamify:metrics"


class AIGamificationDraftValidationError(ValueError):
    pass


_WORD_RE = re.compile(r"[A-Za-z\u0400-\u04FF0-9]+", re.UNICODE)
_SENTENCE_END_RE = re.compile(r"[.!?\u2026]")
_CODE_FENCE_RE = re.compile(r"```(?:[\w#+-]+)?\s*(.*?)```", re.IGNORECASE | re.DOTALL)
_CODE_LINE_RE = re.compile(
    r"(^\s*[{}]\s*$)|(;)|(\b(public|private|protected|internal|class|interface|struct|enum|delegate|event|void|return|new)\b)",
    re.IGNORECASE,
)


def _utc_day_key(now: datetime | None = None) -> str:
    effective_now = now or datetime.now(UTC)
    return effective_now.strftime("%Y%m%d")


def _seconds_until_next_utc_day(now: datetime | None = None) -> int:
    effective_now = now or datetime.now(UTC)
    next_day = datetime.combine((effective_now + timedelta(days=1)).date(), datetime.min.time(), tzinfo=UTC)
    return max(int((next_day - effective_now).total_seconds()), 1)


def _trim_source_text(source_text: str) -> str:
    limit = max(int(settings.ai_gamification_max_source_chars), 1000)
    if len(source_text) <= limit:
        return source_text
    marker = "\n\n[truncated]"
    cut = max(limit - len(marker), 1)
    return source_text[:cut] + marker


async def enforce_ai_daily_quota(current_user: User) -> None:
    daily_quota = int(settings.ai_gamification_daily_quota_per_user)
    if daily_quota <= 0:
        return

    day_key = _utc_day_key()
    redis_key = f"ai:quota:gamify:create:user:{current_user.id}:{day_key}"
    ttl_seconds = _seconds_until_next_utc_day()

    try:
        redis = get_redis_client()
        current = await redis.incr(redis_key)
        if current == 1:
            await redis.expire(redis_key, ttl_seconds)
    except Exception:
        logger.exception("AI quota check failed for user_id=%s", current_user.id)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="AI quota backend unavailable")

    if current > daily_quota:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Daily AI quota exceeded",
        )


async def _bump_ai_metric(metric_name: str, increment: int = 1) -> None:
    try:
        redis = get_redis_client()
        await redis.hincrby(AI_GAMIFY_METRICS_KEY, metric_name, int(increment))
    except Exception:
        logger.exception("Failed to bump AI metric '%s'", metric_name)


async def enqueue_ai_job(job_id: int) -> None:
    if settings.get_background_tasks_backend() != "celery":
        redis = get_redis_client()
        await redis.rpush(AI_GAMIFY_QUEUE, json.dumps({"job_id": int(job_id)}))
        return
    await enqueue_ai_gamification_job(int(job_id))


def _render_draft_text(draft: AIGamifyDraft) -> str:
    lines: list[str] = [f"Title: {draft.draft_title}", "", f"Story: {draft.story_frame}", ""]
    lines.append(f"Task goal: {draft.task_goal}")
    if draft.game_rules:
        lines.append("")
        lines.append("Game rules:")
        lines.extend([f"- {rule}" for rule in draft.game_rules])
    if draft.hints:
        lines.append("")
        lines.append("Hints:")
        lines.extend([f"- {hint}" for hint in draft.hints])
    if draft.acceptance_criteria:
        lines.append("")
        lines.append("Acceptance criteria:")
        lines.extend([f"- {criterion}" for criterion in draft.acceptance_criteria])
    if draft.rewards and (draft.rewards.xp or draft.rewards.badges):
        lines.append("")
        lines.append(f"XP reward: {draft.rewards.xp}")
        if draft.rewards.badges:
            lines.append(f"Badges: {', '.join(draft.rewards.badges)}")
    if draft.teacher_notes:
        lines.append("")
        lines.append(f"Teacher notes: {draft.teacher_notes}")
    return "\n".join(lines).strip()


def _validate_draft_quality(draft: AIGamifyDraft) -> None:
    def _normalize(value: str | None) -> str:
        if value is None:
            return ""
        return " ".join(value.strip().split())

    def _word_count(value: str) -> int:
        return len(_WORD_RE.findall(value))

    def _is_valid_title(value: str) -> bool:
        if len(value) < 5:
            return False
        return _word_count(value) >= 2 or len(value) >= 12

    def _is_sentence_like(value: str) -> bool:
        if len(value) < 20:
            return False
        if _word_count(value) < 5:
            return False
        return bool(_SENTENCE_END_RE.search(value)) or len(value) >= 40

    title = _normalize(draft.draft_title)
    story = _normalize(draft.story_frame)
    task_goal = _normalize(draft.task_goal)

    if not _is_valid_title(title):
        raise AIGamificationDraftValidationError("AI draft is semantically empty: draft_title")
    if not _is_sentence_like(story):
        raise AIGamificationDraftValidationError("AI draft is semantically empty: story_frame")
    if not _is_sentence_like(task_goal):
        raise AIGamificationDraftValidationError("AI draft is semantically empty: task_goal")


def _with_semantic_fallback_constraints(payload: AIGamifyRequest) -> AIGamifyRequest:
    extra_constraint = (
        "Mandatory: draft_title, story_frame and task_goal must be non-empty, concrete, "
        "and each at least one full sentence."
    )
    constraints = [*(payload.constraints or [])]
    if extra_constraint not in constraints:
        constraints.append(extra_constraint)
    return payload.model_copy(update={"constraints": constraints})


async def _generate_draft_with_semantic_fallback(
    *,
    payload: AIGamifyRequest,
    source_text: str,
):
    primary_result = await generate_gamification_draft(payload=payload, source_text=source_text)
    try:
        _validate_draft_quality(primary_result.draft)
        return primary_result
    except AIGamificationDraftValidationError as exc:
        logger.warning("AI semantic fallback for source_type=%s: %s", payload.source_type.value, exc)
        await _bump_ai_metric("jobs_semantic_fallback_used")

    fallback_payload = _with_semantic_fallback_constraints(payload)
    fallback_result = await generate_gamification_draft(payload=fallback_payload, source_text=source_text)
    _validate_draft_quality(fallback_result.draft)
    return fallback_result


def _resolve_source_text_for_code_preservation(job) -> str:
    if job.source_type == "raw_text":
        return str(job.raw_text or "")
    return str(job.source_snapshot or "")


def _resolve_apply_payload_for_job(job, payload: AIGamifyApplyRequest) -> AIGamifyApplyRequest:
    if payload.target_type is not None and payload.target_id is not None:
        return payload
    if payload.target_type is not None and payload.target_id is None:
        # Explicit target type + no id means "auto-create target".
        return payload
    if job.source_type in {"material", "question"} and job.source_id is not None:
        return payload.model_copy(
            update={
                "target_type": AIGamifyTargetType(job.source_type),
                "target_id": int(job.source_id),
            }
        )
    # For raw_text jobs without explicit target, default to creating a draft material.
    return payload.model_copy(update={"target_type": AIGamifyTargetType.MATERIAL, "target_id": None})


def _extract_code_snippets(text: str | None) -> list[str]:
    if not text:
        return []

    fenced = [block.strip() for block in _CODE_FENCE_RE.findall(text or "") if block and block.strip()]
    if fenced:
        return fenced

    blocks: list[str] = []
    current: list[str] = []
    lines = text.splitlines()
    for raw_line in lines:
        line = raw_line.rstrip()
        if _CODE_LINE_RE.search(line):
            current.append(line)
            continue
        if len(current) >= 2:
            blocks.append("\n".join(current).strip())
        current = []
    if len(current) >= 2:
        blocks.append("\n".join(current).strip())
    return [block for block in blocks if block]


def _append_preserved_code_if_needed(*, draft_text: str, source_text: str | None) -> str:
    source_blocks = _extract_code_snippets(source_text)
    if not source_blocks:
        return draft_text
    if _extract_code_snippets(draft_text):
        return draft_text

    preserved_blocks = "\n\n".join(f"```csharp\n{block}\n```" for block in source_blocks)
    preserved_section = f"[Preserved original code]\n{preserved_blocks}"
    return f"{draft_text}\n\n{preserved_section}".strip()


async def _apply_draft_to_material(
    db: AsyncSession,
    *,
    target_id: int,
    draft: AIGamifyDraft,
    apply_mode: str,
    current_user: User,
    preserve_source_text: str | None = None,
) -> int:
    material = await material_repo.get_material(db, target_id)
    if material is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Material not found")
    if current_user.role == "teacher" and not can_manage_material(current_user, material):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")

    draft_text = _render_draft_text(draft)
    draft_text = _append_preserved_code_if_needed(
        draft_text=draft_text,
        source_text=preserve_source_text,
    )
    if apply_mode == "replace":
        material.blocks = [
            MaterialBlock(
                block_type="text",
                title=draft.draft_title,
                body=draft_text,
                url=None,
                order_index=0,
            )
        ]
    else:
        next_order = max((int(block.order_index or 0) for block in material.blocks), default=-1) + 1
        material.blocks.append(
            MaterialBlock(
                block_type="text",
                title=draft.draft_title,
                body=draft_text,
                url=None,
                order_index=next_order,
            )
        )

    await db.flush()
    await db.refresh(material)
    return material.id


async def _apply_draft_to_question(
    db: AsyncSession,
    *,
    target_id: int,
    draft: AIGamifyDraft,
    apply_mode: str,
    current_user: User,
    preserve_source_text: str | None = None,
) -> int:
    question = await question_repo.get_question_with_choices(db, target_id)
    if question is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found")

    test = await test_repo.get_test(db, question.test_id)
    if test is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Test not found")
    if current_user.role == "teacher" and not can_manage_test(current_user, test):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")

    draft_text = _render_draft_text(draft)
    draft_text = _append_preserved_code_if_needed(
        draft_text=draft_text,
        source_text=preserve_source_text or question.text,
    )
    if apply_mode == "replace":
        question.text = draft_text
    else:
        base_text = (question.text or "").strip()
        append_text = f"[AI Gamification Draft]\n{draft_text}"
        question.text = f"{base_text}\n\n{append_text}" if base_text else append_text

    await db.flush()
    await db.refresh(question)
    return question.id


async def _auto_create_material_target_from_draft(
    db: AsyncSession,
    *,
    draft: AIGamifyDraft,
    source_text: str,
    current_user: User,
) -> int:
    # Teacher-owned draft by default; admin-created drafts are owned by admin user.
    title = (draft.draft_title or "AI Gamified Draft").strip()[:300] or "AI Gamified Draft"
    body = _render_draft_text(draft)
    body = _append_preserved_code_if_needed(draft_text=body, source_text=source_text)

    material = await material_repo.create_material(
        db,
        title=title,
        description=(draft.story_frame or "").strip() or None,
        author_id=current_user.id,
        material_type="lesson",
        status="draft",
        blocks=[
            {
                "block_type": "text",
                "title": title,
                "body": body,
                "url": None,
                "order_index": 0,
            }
        ],
    )
    return int(material.id)


async def _auto_create_question_target_from_draft(
    db: AsyncSession,
    *,
    job,
    draft: AIGamifyDraft,
    source_text: str,
    current_user: User,
) -> int:
    if job.source_type != "question" or job.source_id is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Auto-create for question target requires question source context",
        )

    source_question = await question_repo.get_question_with_choices(db, int(job.source_id))
    if source_question is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source question not found")

    source_test = await test_repo.get_test(db, int(source_question.test_id))
    if source_test is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source test not found")
    if current_user.role == "teacher" and not can_manage_test(current_user, source_test):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")

    text = _render_draft_text(draft)
    text = _append_preserved_code_if_needed(draft_text=text, source_text=source_text or source_question.text)

    copied_choices = [
        {
            "value": choice.value,
            "ordinal": int(choice.ordinal),
            "is_correct": bool(choice.is_correct),
        }
        for choice in sorted(source_question.choices, key=lambda item: int(item.ordinal or 0))
    ]

    created_question = await question_repo.create_question_with_choices(
        db,
        test_id=int(source_question.test_id),
        text=text,
        points=float(source_question.points),
        is_open_answer=bool(source_question.is_open_answer),
        material_urls=list(source_question.material_urls or []),
        choices=copied_choices,
    )
    return int(created_question.id)


def _request_from_job(job) -> AIGamifyRequest:
    return AIGamifyRequest.model_validate(
        {
            "source_type": job.source_type,
            "source_id": job.source_id,
            "raw_text": job.raw_text,
            "target_level": job.target_level,
            "language": job.language,
            "style": job.style,
            "tone": job.tone,
            "constraints": list(job.constraints_json or []),
        }
    )


async def _material_source_snapshot(db: AsyncSession, source_id: int, current_user: User) -> str:
    material = await material_repo.get_material(db, source_id)
    if material is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Material not found")
    if current_user.role == "teacher" and not can_manage_material(current_user, material):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")

    parts: list[str] = [
        f"Material title: {material.title}",
        f"Material type: {material.material_type}",
    ]
    if material.description:
        parts.append(f"Description: {material.description}")
    for block in sorted(material.blocks, key=lambda item: item.order_index):
        block_line = f"Block[{block.order_index}] type={block.block_type}"
        if block.title:
            block_line += f" title={block.title}"
        parts.append(block_line)
        if block.body:
            parts.append(block.body)
        if block.url:
            parts.append(f"URL: {block.url}")
    for attachment in sorted(material.attachments, key=lambda item: item.order_index):
        parts.append(
            f"Attachment[{attachment.order_index}] {attachment.file_kind}: {attachment.title} ({attachment.file_url})"
        )
    return "\n".join(parts)


async def _question_source_snapshot(db: AsyncSession, source_id: int, current_user: User) -> str:
    question = await question_repo.get_question_with_choices(db, source_id)
    if question is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found")

    test = await test_repo.get_test(db, question.test_id)
    if test is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Test not found")
    if current_user.role == "teacher" and not can_manage_test(current_user, test):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")

    parts: list[str] = [
        f"Question text: {question.text}",
        f"Points: {float(question.points)}",
        f"Is open answer: {bool(question.is_open_answer)}",
    ]
    if question.material_urls:
        parts.append(f"Material URLs: {', '.join(question.material_urls)}")
    for choice in sorted(question.choices, key=lambda item: int(item.ordinal or 0)):
        parts.append(f"Choice[{choice.ordinal}]: {choice.value}")
    return "\n".join(parts)


async def build_source_snapshot(db: AsyncSession, payload: AIGamifyRequest, current_user: User) -> str | None:
    if payload.source_type.value == "raw_text":
        raw_text = (payload.raw_text or "").strip()
        if not raw_text:
            return raw_text
        return _trim_source_text(raw_text)
    if payload.source_id is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="source_id is required")

    if payload.source_type.value == "material":
        snapshot = await _material_source_snapshot(db, payload.source_id, current_user)
        return _trim_source_text(snapshot)
    if payload.source_type.value == "question":
        snapshot = await _question_source_snapshot(db, payload.source_id, current_user)
        return _trim_source_text(snapshot)

    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported source_type")


async def create_ai_gamification_job(db: AsyncSession, payload: AIGamifyRequest, current_user: User):
    try:
        ensure_ai_gamification_ready()
    except AIGamificationDisabledError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))
    except AIGamificationConfigError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))

    await enforce_ai_daily_quota(current_user)

    source_snapshot = await build_source_snapshot(db, payload, current_user)
    job = await ai_gamification_repo.create_job(
        db,
        created_by_user_id=current_user.id,
        payload=payload,
        source_snapshot=source_snapshot,
    )

    async def enqueue_after_commit() -> None:
        try:
            await enqueue_ai_job(job.id)
        except Exception as exc:
            logger.exception("Failed to enqueue AI gamification job_id=%s", job.id)
            async with AsyncSessionLocal() as fail_session:
                failed_job = await ai_gamification_repo.get_job(fail_session, job.id)
                if failed_job is not None and failed_job.status == "pending":
                    await ai_gamification_repo.set_job_failed(
                        fail_session,
                        failed_job,
                        error_text=f"Queue unavailable: {exc}",
                    )
                    await fail_session.commit()

    add_post_commit_task(db, enqueue_after_commit)
    return job


async def list_ai_jobs_for_user(
    db: AsyncSession,
    *,
    current_user: User,
    limit: int = 20,
    offset: int = 0,
    status_filter: str | None = None,
    source_type_filter: str | None = None,
) -> list[dict]:
    jobs = await ai_gamification_repo.list_jobs_for_user(
        db,
        current_user_id=current_user.id,
        is_admin=current_user.role == "admin",
        status_filter=status_filter,
        source_type_filter=source_type_filter,
        limit=min(max(limit, 1), 100),
        offset=max(offset, 0),
    )
    return [ai_gamification_repo.to_job_read_payload(item) for item in jobs]


async def retry_ai_gamification_job(
    db: AsyncSession,
    *,
    job_id: int,
    current_user: User,
) -> dict:
    job = await get_job_for_user(db, job_id, current_user)
    if job.status != "failed":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only failed jobs can be retried",
        )

    await ai_gamification_repo.reset_job_for_retry(db, job)
    try:
        redis = get_redis_client()
        await redis.delete(f"{AI_GAMIFY_RETRY_KEY_PREFIX}:{job.id}")
        await enqueue_ai_job(job.id)
        await _bump_ai_metric("jobs_retried")
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Unable to enqueue retry: {exc}",
        )
    return {"job_id": job.id, "status": "pending"}


async def get_ai_ops_metrics() -> dict:
    redis = get_redis_client()
    metrics_raw = await redis.hgetall(AI_GAMIFY_METRICS_KEY)

    def _to_int(value) -> int:
        if value is None:
            return 0
        try:
            return int(value)
        except Exception:
            return 0

    queued_jobs = _to_int(await redis.llen(AI_GAMIFY_QUEUE))
    dead_letter_jobs = _to_int(await redis.llen(AI_GAMIFY_DLQ))
    return {
        "queued_jobs": queued_jobs,
        "dead_letter_jobs": dead_letter_jobs,
        "jobs_processed": _to_int(metrics_raw.get("jobs_processed")),
        "jobs_completed": _to_int(metrics_raw.get("jobs_completed")),
        "jobs_failed": _to_int(metrics_raw.get("jobs_failed")),
        "jobs_retried": _to_int(metrics_raw.get("jobs_retried")),
        "jobs_semantic_fallback_used": _to_int(metrics_raw.get("jobs_semantic_fallback_used")),
    }


def _parse_dlq_payload(raw_payload: str) -> dict:
    try:
        data = json.loads(raw_payload)
    except Exception:
        data = {}

    job_id = data.get("job_id")
    try:
        parsed_job_id = int(job_id) if job_id is not None else None
    except Exception:
        parsed_job_id = None

    error = data.get("error")
    if error is not None:
        error = str(error)

    return {
        "job_id": parsed_job_id,
        "error": error,
        "raw_payload": raw_payload,
    }


async def list_ai_dead_letter_jobs(*, limit: int = 20, offset: int = 0) -> dict:
    redis = get_redis_client()
    safe_limit = min(max(int(limit), 1), 200)
    safe_offset = max(int(offset), 0)

    total = int(await redis.llen(AI_GAMIFY_DLQ))
    if safe_offset >= total:
        return {"items": [], "limit": safe_limit, "offset": safe_offset, "total": total}

    raw_items = await redis.lrange(AI_GAMIFY_DLQ, safe_offset, safe_offset + safe_limit - 1)
    items = []
    for index, raw_payload in enumerate(raw_items, start=safe_offset):
        parsed = _parse_dlq_payload(raw_payload)
        items.append(
            {
                "queue_index": index,
                "job_id": parsed["job_id"],
                "error": parsed["error"],
                "raw_payload": parsed["raw_payload"],
            }
        )

    return {"items": items, "limit": safe_limit, "offset": safe_offset, "total": total}


async def _dlq_list_all(redis) -> list[str]:
    return list(await redis.lrange(AI_GAMIFY_DLQ, 0, -1))


async def _dlq_replace_all(redis, items: list[str]) -> None:
    await redis.delete(AI_GAMIFY_DLQ)
    for item in items:
        await redis.rpush(AI_GAMIFY_DLQ, item)


async def _dlq_remove_by_index(redis, queue_index: int) -> str:
    all_items = await _dlq_list_all(redis)
    if queue_index < 0 or queue_index >= len(all_items):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="DLQ item not found")

    removed_payload = all_items[queue_index]
    remaining = all_items[:queue_index] + all_items[queue_index + 1 :]

    await _dlq_replace_all(redis, remaining)

    return removed_payload


async def requeue_ai_dead_letter_job(
    db: AsyncSession,
    *,
    queue_index: int,
) -> dict:
    redis = get_redis_client()

    all_items = await _dlq_list_all(redis)
    if queue_index < 0 or queue_index >= len(all_items):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="DLQ item not found")
    raw_payload = all_items[queue_index]
    parsed = _parse_dlq_payload(raw_payload)
    job_id = parsed["job_id"]
    if job_id is None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="DLQ item has no valid job_id")

    job = await ai_gamification_repo.get_job(db, job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found for DLQ item")
    if job.status != "failed":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Only failed jobs can be requeued from DLQ")

    await ai_gamification_repo.reset_job_for_retry(db, job)

    removed_payload = await _dlq_remove_by_index(redis, queue_index)
    try:
        await redis.delete(f"{AI_GAMIFY_RETRY_KEY_PREFIX}:{job.id}")
        await enqueue_ai_job(job.id)
        await _bump_ai_metric("jobs_retried")
    except Exception as exc:
        # Restore payload into DLQ to avoid silent data loss on enqueue failure.
        try:
            await redis.rpush(AI_GAMIFY_DLQ, removed_payload)
        except Exception:
            logger.exception("Failed to restore DLQ payload after requeue error")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Unable to requeue DLQ job: {exc}",
        )

    return {"queue_index": queue_index, "job_id": job.id, "status": "pending"}


async def discard_ai_dead_letter_job(*, queue_index: int) -> dict:
    redis = get_redis_client()
    await _dlq_remove_by_index(redis, queue_index)
    return {"queue_index": queue_index, "removed": True}


async def requeue_ai_dead_letter_batch(
    db: AsyncSession,
    *,
    max_items: int = 20,
) -> dict:
    redis = get_redis_client()
    safe_max_items = min(max(int(max_items), 1), 500)

    all_items = await _dlq_list_all(redis)
    if not all_items:
        return {"scanned": 0, "requeued": 0, "discarded": 0, "skipped": 0, "failures": []}

    kept_items: list[str] = []
    failures: list[str] = []
    scanned = 0
    requeued = 0
    skipped = 0

    for index, raw_payload in enumerate(all_items):
        if index >= safe_max_items:
            kept_items.append(raw_payload)
            continue

        scanned += 1
        parsed = _parse_dlq_payload(raw_payload)
        job_id = parsed["job_id"]
        if job_id is None:
            skipped += 1
            kept_items.append(raw_payload)
            continue

        job = await ai_gamification_repo.get_job(db, job_id)
        if job is None:
            skipped += 1
            kept_items.append(raw_payload)
            continue
        if job.status != "failed":
            skipped += 1
            kept_items.append(raw_payload)
            continue

        await ai_gamification_repo.reset_job_for_retry(db, job)
        try:
            await redis.delete(f"{AI_GAMIFY_RETRY_KEY_PREFIX}:{job.id}")
            await enqueue_ai_job(job.id)
            await _bump_ai_metric("jobs_retried")
            requeued += 1
        except Exception as exc:
            await ai_gamification_repo.set_job_failed(db, job, error_text=f"DLQ batch requeue failed: {exc}")
            failures.append(f"job_id={job.id}: {exc}")
            kept_items.append(raw_payload)

    await _dlq_replace_all(redis, kept_items)
    return {
        "scanned": scanned,
        "requeued": requeued,
        "discarded": 0,
        "skipped": skipped,
        "failures": failures,
    }


async def discard_ai_dead_letter_batch(*, max_items: int = 20) -> dict:
    redis = get_redis_client()
    safe_max_items = min(max(int(max_items), 1), 500)

    all_items = await _dlq_list_all(redis)
    if not all_items:
        return {"scanned": 0, "requeued": 0, "discarded": 0, "skipped": 0, "failures": []}

    scanned = min(len(all_items), safe_max_items)
    discarded = scanned
    remaining = all_items[scanned:]
    await _dlq_replace_all(redis, remaining)
    return {"scanned": scanned, "requeued": 0, "discarded": discarded, "skipped": 0, "failures": []}


async def get_job_for_user(db: AsyncSession, job_id: int, current_user: User):
    job = await ai_gamification_repo.get_job(db, job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    if current_user.role != "admin" and job.created_by_user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
    return job


async def apply_job_draft(
    db: AsyncSession,
    *,
    job_id: int,
    payload: AIGamifyApplyRequest,
    current_user: User,
) -> dict:
    job = await get_job_for_user(db, job_id, current_user)
    payload = _resolve_apply_payload_for_job(job, payload)

    if job.status == "applied":
        same_target_type = job.applied_target_type == payload.target_type.value
        same_target_id = (
            job.applied_target_id == payload.target_id
            if payload.target_id is not None
            else True
        )
        if same_target_type and same_target_id and job.applied_target_id is not None:
            return {
                "job_id": job.id,
                "status": "applied",
                "updated_entity": {"type": job.applied_target_type, "id": job.applied_target_id},
            }
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Job already applied to another target")

    if job.status != "completed":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Job must be completed before apply")

    if not job.draft_json:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Completed job has no draft payload")

    try:
        draft = AIGamifyDraft.model_validate(job.draft_json)
    except Exception:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Stored draft payload is invalid")
    try:
        _validate_draft_quality(draft)
    except AIGamificationDraftValidationError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))

    source_text_for_preserve = _resolve_source_text_for_code_preservation(job)

    if payload.target_type == AIGamifyTargetType.MATERIAL:
        if payload.target_id is None:
            target_id = await _auto_create_material_target_from_draft(
                db,
                draft=draft,
                source_text=source_text_for_preserve,
                current_user=current_user,
            )
        else:
            target_id = await _apply_draft_to_material(
                db,
                target_id=payload.target_id,
                draft=draft,
                apply_mode=payload.apply_mode.value,
                current_user=current_user,
                preserve_source_text=source_text_for_preserve,
            )
        try:
            await bump_cache_namespace(NS_MATERIALS, NS_TESTS, NS_TEST_CONTENT)
        except Exception:
            logger.exception("Failed to bump cache namespace for material apply, target_id=%s", target_id)
    else:
        if payload.target_id is None:
            target_id = await _auto_create_question_target_from_draft(
                db,
                job=job,
                draft=draft,
                source_text=source_text_for_preserve,
                current_user=current_user,
            )
        else:
            target_id = await _apply_draft_to_question(
                db,
                target_id=payload.target_id,
                draft=draft,
                apply_mode=payload.apply_mode.value,
                current_user=current_user,
                preserve_source_text=source_text_for_preserve,
            )
        try:
            await bump_cache_namespace(NS_QUESTIONS, NS_TEST_CONTENT)
        except Exception:
            logger.exception("Failed to bump cache namespace for question apply, target_id=%s", target_id)

    await ai_gamification_repo.set_job_applied(
        db,
        job,
        target_type=payload.target_type.value,
        target_id=target_id,
    )

    return {
        "job_id": job.id,
        "status": "applied",
        "updated_entity": {"type": payload.target_type.value, "id": target_id},
    }


async def process_ai_gamification_job(job_id: int, session_factory=AsyncSessionLocal) -> None:
    # Step 1: mark running and take snapshot of payload fields.
    async with session_factory() as session:
        job = await ai_gamification_repo.get_job(session, job_id)
        if job is None:
            logger.warning("AI job not found: id=%s", job_id)
            return
        if job.status in {"completed", "failed", "applied"}:
            return
        await ai_gamification_repo.set_job_running(session, job)
        await session.commit()

        payload = _request_from_job(job)
        source_text = (job.raw_text or "") if payload.source_type.value == "raw_text" else (job.source_snapshot or "")

    # Step 2: call provider.
    try:
        result = await _generate_draft_with_semantic_fallback(payload=payload, source_text=source_text)
    except Exception as exc:
        retry_key = f"{AI_GAMIFY_RETRY_KEY_PREFIX}:{job_id}"
        max_retries = max(int(settings.ai_gamification_job_max_retries), 0)
        try:
            redis = get_redis_client()
            attempts = await redis.incr(retry_key)
            if attempts == 1:
                await redis.expire(retry_key, 7 * 24 * 3600)
            if attempts <= max_retries:
                await redis.rpush(AI_GAMIFY_QUEUE, json.dumps({"job_id": job_id}))
                await _bump_ai_metric("jobs_retried")
                logger.warning("AI job %s requeued after failure (attempt %s/%s): %s", job_id, attempts, max_retries, exc)
                return
        except Exception:
            logger.exception("AI retry bookkeeping failed for job_id=%s", job_id)

        async with session_factory() as session:
            job = await ai_gamification_repo.get_job(session, job_id)
            if job is None:
                return
            if job.status in {"completed", "applied"}:
                return
            await ai_gamification_repo.set_job_failed(session, job, error_text=str(exc))
            await session.commit()
        await _bump_ai_metric("jobs_failed")
        await _bump_ai_metric("jobs_processed")
        try:
            redis = get_redis_client()
            await redis.rpush(
                AI_GAMIFY_DLQ,
                json.dumps(
                    {
                        "job_id": job_id,
                        "error": str(exc)[:500],
                    }
                ),
            )
        except Exception:
            logger.exception("Failed to push AI job into DLQ job_id=%s", job_id)
        return

    # Step 3: persist completed state.
    async with session_factory() as session:
        job = await ai_gamification_repo.get_job(session, job_id)
        if job is None:
            return
        if job.status in {"applied"}:
            return
        await ai_gamification_repo.set_job_completed(
            session,
            job,
            draft=result.draft,
            model=result.model,
            provider=result.provider,
            usage=result.usage,
            latency_ms=result.latency_ms,
        )
        await session.commit()
    try:
        redis = get_redis_client()
        await redis.delete(f"{AI_GAMIFY_RETRY_KEY_PREFIX}:{job_id}")
    except Exception:
        logger.exception("Failed to cleanup AI retry key for job_id=%s", job_id)
    await _bump_ai_metric("jobs_completed")
    await _bump_ai_metric("jobs_processed")
