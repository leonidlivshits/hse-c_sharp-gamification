from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.access import (
    get_manageable_test,
    get_user_level_context,
    get_visible_test,
    is_unlocked_test,
)
from app.api.deps import get_db
from app.cache.redis_cache import (
    ANSWERS_BY_TEST_TTL,
    NS_MATERIALS,
    NS_QUESTIONS,
    NS_TESTS,
    NS_TEST_CONTENT,
    NS_TEST_SUMMARY,
    TEST_CONTENT_TTL,
    TESTS_CATALOG_TTL,
    TESTS_LIST_TTL,
    TEST_DETAIL_TTL,
    TEST_SUMMARY_TTL,
    bump_cache_namespace,
    bump_user_attempts_state_version,
    cache_key_answers_for_test,
    cache_key_test_content_for_user,
    cache_key_test_content,
    cache_key_test_detail,
    cache_key_test_list,
    cache_key_tests_catalog_me,
    cache_key_test_summary,
    get_cache_namespace_version,
    get_user_attempts_state_version,
    get,
    set,
)
from app.core.security import get_current_user, require_roles
from app.models.user import User
from app.schemas.grading import AttemptScoreUpdate
from app.schemas.answer import AnswerRead, AttemptSubmitRequest
from app.schemas.question import QuestionRead
from app.schemas.test_ import TestCardRead, TestCreate, TestRead, TestUpdate
from app.schemas.analytics import TestSummary
from app.schemas.test_attempt import TestAttemptQuotaRead, TestAttemptRead, TestAttemptStartRead, TestAttemptStateRead
from app.schemas.test_content import TestContentRead, TestContentWrite
from app.repositories import analytics_repo, answer_repo, test_repo, test_attempt_repo
from app.repositories import question_repo
from app.services import test_service
from app.services.answer_service import submit_answers_batch_for_attempt
from app.services.test_attempt_api_service import (
    build_attempt_quota_payload,
    build_attempt_state_payload,
    resolve_block_reason_from_policy_error,
    schedule_attempt_completion_postprocess,
)
from app.services.test_runtime import AttemptPolicyError, finalize_attempt_if_expired, resolve_attempt_for_user

router = APIRouter()


async def _prewarm_answers_cache_for_tests(
    db: AsyncSession,
    *,
    user_id: int,
    tests: list,
) -> None:
    """
    Best-effort cache prewarm for /answers/test/{id} calls that typically follow /tests
    on the frontend (home/personal/analytics pages).
    """
    if not tests:
        return

    test_ids = [int(test.id) for test in tests]
    answers_by_test = await answer_repo.get_answers_for_tests_for_user(
        db,
        user_id=user_id,
        test_ids=test_ids,
    )
    summary_version = await get_cache_namespace_version(NS_TEST_SUMMARY)

    for test_id in test_ids:
        answers = answers_by_test.get(test_id, [])
        payload = [AnswerRead.model_validate(item).model_dump(mode="json") for item in answers]
        cache_key = cache_key_answers_for_test(
            test_id=test_id,
            user_id=user_id,
            limit=100,
            offset=0,
            version=summary_version,
        )
        await set(cache_key, payload, ttl=ANSWERS_BY_TEST_TTL)


@router.get("/", response_model=List[TestRead], status_code=status.HTTP_200_OK)
async def list_tests(
    published_only: bool = True,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not published_only and current_user.role not in {"teacher", "admin"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")

    total_points, level_id = await get_user_level_context(db, current_user)
    if published_only:
        version = await get_cache_namespace_version(NS_TESTS)
        cache_key = cache_key_test_list(
            published_only=published_only,
            limit=limit,
            level_id=level_id,
            version=version,
        )
        cached = await get(cache_key)
        if cached is not None:
            return cached

    author_id = current_user.id if (not published_only and current_user.role == "teacher") else None
    items = await test_repo.list_tests(db, published_only=published_only, limit=limit, author_id=author_id)
    if published_only and current_user.role not in {"teacher", "admin"}:
        items = [
            item
            for item in items
            if await is_unlocked_test(db, current_user, item, total_points=total_points)
        ]
        try:
            # Prewarm answer caches for common frontend flow:
            # /tests -> /answers/test/{id} for each visible test.
            await _prewarm_answers_cache_for_tests(
                db,
                user_id=current_user.id,
                tests=items,
            )
        except Exception:
            # Cache prewarm is best-effort and must not affect API response.
            pass
    if published_only:
        payload = [TestRead.model_validate(item).model_dump(mode="json") for item in items]
        await set(cache_key, payload, ttl=TESTS_LIST_TTL)
    return items


@router.get("/catalog/me", response_model=List[TestCardRead], status_code=status.HTTP_200_OK)
async def list_tests_with_my_state(
    published_only: bool = True,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not published_only and current_user.role not in {"teacher", "admin"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")

    cache_key = None
    should_cache = current_user.role != "admin"
    if should_cache:
        tests_version = await get_cache_namespace_version(NS_TESTS)
        summary_version = await get_cache_namespace_version(NS_TEST_SUMMARY)
        attempts_version = await get_user_attempts_state_version(current_user.id)
        cache_key = cache_key_tests_catalog_me(
            user_id=current_user.id,
            published_only=published_only,
            limit=limit,
            tests_version=tests_version,
            summary_version=summary_version,
            attempts_version=attempts_version,
        )
        cached = await get(cache_key)
        if cached is not None:
            return cached

    total_points: float | None = None
    if published_only and current_user.role not in {"teacher", "admin"}:
        total_points, _ = await get_user_level_context(db, current_user)

    author_id = current_user.id if (not published_only and current_user.role == "teacher") else None
    items = await test_repo.list_tests(db, published_only=published_only, limit=limit, author_id=author_id)

    if published_only and current_user.role not in {"teacher", "admin"}:
        items = [
            item
            for item in items
            if await is_unlocked_test(db, current_user, item, total_points=total_points)
        ]

    state_map = await test_repo.get_user_test_state_map(
        db,
        user_id=current_user.id,
        tests=items,
    )

    payload: list[TestCardRead] = []
    for item in items:
        base = TestRead.model_validate(item).model_dump(mode="python")
        state = state_map.get(item.id, {})
        payload.append(
            TestCardRead.model_validate(
                {
                    **base,
                    "total_questions": int(state.get("total_questions", 0)),
                    "user_status": state.get("user_status", "not_started"),
                    "ui_status": state.get("ui_status", state.get("user_status", "not_started")),
                    "progress_state": state.get("progress_state", state.get("user_status", "not_started")),
                    "attempt_state": state.get("attempt_state", "can_start"),
                    "can_start": bool(state.get("can_start", True)),
                    "can_resume": bool(state.get("can_resume", False)),
                    "block_reason": state.get("block_reason"),
                    "has_active_attempt": bool(state.get("has_active_attempt", False)),
                    "active_attempt_id": state.get("active_attempt_id"),
                    "completed_attempts": int(state.get("completed_attempts", 0)),
                    "remaining_attempts": int(state.get("remaining_attempts", max(int(item.max_attempts or 1), 1))),
                    "user_score": state.get("user_score"),
                    "user_max_score": state.get("user_max_score"),
                    "latest_completed_at": state.get("latest_completed_at"),
                }
            )
        )

    if should_cache and cache_key is not None:
        await set(
            cache_key,
            [item.model_dump(mode="json") for item in payload],
            ttl=TESTS_CATALOG_TTL,
        )
    return payload


@router.get("/page/me", response_model=List[TestCardRead], status_code=status.HTTP_200_OK)
async def list_tests_page_cards(
    published_only: bool = True,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Screen-oriented alias for tests page cards.
    Returns the same payload as /tests/catalog/me.
    """
    return await list_tests_with_my_state(
        published_only=published_only,
        limit=limit,
        db=db,
        current_user=current_user,
    )


@router.get("/{test_id}", response_model=TestRead, status_code=status.HTTP_200_OK)
async def get_test(
    test_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    total_points: float | None = None
    level_id = 0
    if current_user.role not in {"teacher", "admin"}:
        total_points, level_id = await get_user_level_context(db, current_user)
        version = await get_cache_namespace_version(NS_TESTS)
        cache_key = cache_key_test_detail(test_id, level_id=level_id, version=version)
        cached = await get(cache_key)
        if cached is not None:
            return cached

    t = await get_visible_test(db, test_id, current_user, total_points=total_points)
    if t.published:
        payload = TestRead.model_validate(t).model_dump(mode="json")
        version = await get_cache_namespace_version(NS_TESTS)
        await set(cache_key_test_detail(test_id, level_id=level_id, version=version), payload, ttl=TEST_DETAIL_TTL)
    return t


@router.post("/", response_model=TestRead, status_code=status.HTTP_201_CREATED)
async def create_test(
    payload: TestCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("teacher", "admin")),
):
    test = await test_service.create_test(db, payload, current_user)
    await bump_cache_namespace(NS_TESTS, NS_TEST_CONTENT, NS_TEST_SUMMARY, NS_MATERIALS)
    return test


@router.patch("/{test_id}", response_model=TestRead, status_code=status.HTTP_200_OK)
async def update_test(
    test_id: int,
    payload: TestUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("teacher", "admin")),
):
    test = await test_service.update_test(db, test_id, payload, current_user)
    await bump_cache_namespace(NS_TESTS, NS_TEST_CONTENT, NS_TEST_SUMMARY, NS_MATERIALS)
    return test


@router.post("/{test_id}/publish", response_model=TestRead, status_code=status.HTTP_200_OK)
async def publish_test(
    test_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("teacher", "admin")),
):
    await get_manageable_test(db, test_id, current_user)
    test = await test_repo.update_test(db, test_id, published=True)
    if test is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Test not found")
    await bump_cache_namespace(NS_TESTS, NS_TEST_CONTENT, NS_TEST_SUMMARY)
    return test


@router.post("/{test_id}/hide", response_model=TestRead, status_code=status.HTTP_200_OK)
async def hide_test(
    test_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("teacher", "admin")),
):
    await get_manageable_test(db, test_id, current_user)
    test = await test_repo.update_test(db, test_id, published=False)
    if test is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Test not found")
    await bump_cache_namespace(NS_TESTS, NS_TEST_CONTENT, NS_TEST_SUMMARY)
    return test


@router.delete("/{test_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_test(
    test_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("teacher", "admin")),
):
    await get_manageable_test(db, test_id, current_user)
    deleted = await test_repo.delete_test(db, test_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Test not found")
    await bump_cache_namespace(NS_TESTS, NS_TEST_CONTENT, NS_TEST_SUMMARY, NS_MATERIALS)
    return {}


@router.get("/{test_id}/summary", response_model=TestSummary, status_code=status.HTTP_200_OK)
async def test_summary(
    test_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    is_teacher = current_user.role in {"teacher", "admin"}
    summary_version = await get_cache_namespace_version(NS_TEST_SUMMARY)
    cache_key = cache_key_test_summary(test_id, version=summary_version)
    test = await test_service.get_test_or_summary_access(db, test_id, current_user)
    if not is_teacher:
        cached = await get(cache_key)
        if cached is not None:
            return cached

    summary = await test_repo.get_test_summary(db, test_id)
    if test.published:
        await set(cache_key, summary, ttl=TEST_SUMMARY_TTL)
    return summary


@router.get("/{test_id}/content", response_model=TestContentRead, status_code=status.HTTP_200_OK)
async def get_test_content(
    test_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    is_teacher = current_user.role in {"teacher", "admin"}
    total_points: float | None = None
    content_version = await get_cache_namespace_version(NS_TEST_CONTENT)
    cache_key = cache_key_test_content(test_id, level_id=-1, version=content_version)
    if not is_teacher:
        cache_key = cache_key_test_content_for_user(
            test_id=test_id,
            user_id=current_user.id,
            version=content_version,
        )
        cached = await get(cache_key)
        if cached is not None:
            return cached
        total_points, _ = await get_user_level_context(db, current_user)

    test = await get_visible_test(db, test_id, current_user, total_points=total_points)

    questions = await question_repo.list_questions_for_test(db, test_id=test_id, limit=500, offset=0)
    payload = {
        "test": TestRead.model_validate(test).model_dump(mode="json"),
        "questions": [QuestionRead.model_validate(question).model_dump(mode="json") for question in questions],
    }
    if test.published:
        await set(cache_key, payload, ttl=TEST_CONTENT_TTL)
    return payload


@router.put("/{test_id}/content", response_model=TestContentRead, status_code=status.HTTP_200_OK)
async def replace_test_content(
    test_id: int,
    payload: TestContentWrite,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("teacher", "admin")),
):
    test, questions = await test_service.replace_test_content(
        db,
        test_id=test_id,
        payload=payload,
        current_user=current_user,
    )
    await bump_cache_namespace(NS_QUESTIONS, NS_TEST_CONTENT, NS_TEST_SUMMARY)
    return {
        "test": TestRead.model_validate(test).model_dump(mode="json"),
        "questions": [QuestionRead.model_validate(question).model_dump(mode="json") for question in questions],
    }


@router.post("/{test_id}/attempts/start", response_model=TestAttemptStartRead, status_code=status.HTTP_201_CREATED)
async def start_test_attempt(
    test_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    test = await get_visible_test(db, test_id, current_user)
    quota_test_id = int(test.id)
    quota_max_attempts = int(test.max_attempts or 1)
    quota_deadline = test.deadline
    active_attempt_before = await test_attempt_repo.get_active_attempt(db, current_user.id, test_id)
    try:
        attempt = await resolve_attempt_for_user(db, test, current_user.id)
        await bump_user_attempts_state_version(current_user.id)
        action = "resumed" if active_attempt_before is not None and active_attempt_before.id == attempt.id else "started"
        quota = await build_attempt_quota_payload(
            db,
            test_id=quota_test_id,
            max_attempts=quota_max_attempts,
            deadline=quota_deadline,
            user_id=current_user.id,
        )
        payload = {
            **TestAttemptRead.model_validate(attempt).model_dump(mode="python"),
            "action": action,
            "max_attempts": quota.max_attempts,
            "completed_attempts": quota.completed_attempts,
            "remaining_attempts": quota.remaining_attempts,
            "has_active_attempt": quota.has_active_attempt,
            "ui_status": quota.ui_status,
            "progress_state": quota.progress_state,
            "attempt_state": quota.attempt_state,
            "can_start": quota.can_start,
            "can_resume": quota.can_resume,
            "block_reason": quota.block_reason,
        }
        return TestAttemptStartRead.model_validate(payload)
    except AttemptPolicyError as exc:
        if getattr(exc, "code", "") in {"deadline_passed", "time_limit_exceeded"}:
            await bump_user_attempts_state_version(current_user.id)
        block_reason = resolve_block_reason_from_policy_error(exc)
        quota = await build_attempt_quota_payload(
            db,
            test_id=quota_test_id,
            max_attempts=quota_max_attempts,
            deadline=quota_deadline,
            user_id=current_user.id,
            forced_block_reason=block_reason,
        )
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "detail": str(exc),
                "block_reason": block_reason,
                "attempt_state": quota.attempt_state,
                "can_start": quota.can_start,
                "can_resume": quota.can_resume,
                "ui_status": quota.ui_status,
                "progress_state": quota.progress_state,
                "max_attempts": quota.max_attempts,
                "completed_attempts": quota.completed_attempts,
                "remaining_attempts": quota.remaining_attempts,
                "has_active_attempt": quota.has_active_attempt,
            },
        )
    except IntegrityError:
        # Defensive fallback for rare concurrent starts when db-level unique
        # conflict races with read-after-rollback recovery.
        quota = await build_attempt_quota_payload(
            db,
            test_id=quota_test_id,
            max_attempts=quota_max_attempts,
            deadline=quota_deadline,
            user_id=current_user.id,
        )
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "detail": "Concurrent attempt start conflict, please retry",
                "block_reason": quota.block_reason,
                "attempt_state": quota.attempt_state,
                "can_start": quota.can_start,
                "can_resume": quota.can_resume,
                "ui_status": quota.ui_status,
                "progress_state": quota.progress_state,
                "max_attempts": quota.max_attempts,
                "completed_attempts": quota.completed_attempts,
                "remaining_attempts": quota.remaining_attempts,
                "has_active_attempt": quota.has_active_attempt,
            },
        )


@router.get("/{test_id}/attempts/me", response_model=List[TestAttemptRead], status_code=status.HTTP_200_OK)
async def list_my_test_attempts(
    test_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await get_visible_test(db, test_id, current_user)
    return await test_attempt_repo.list_attempts_for_user(db, current_user.id, test_id=test_id)


@router.get("/{test_id}/attempts/quota", response_model=TestAttemptQuotaRead, status_code=status.HTTP_200_OK)
async def get_my_test_attempt_quota(
    test_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    test = await get_visible_test(db, test_id, current_user)
    return await build_attempt_quota_payload(
        db,
        test_id=int(test.id),
        max_attempts=int(test.max_attempts or 1),
        deadline=test.deadline,
        user_id=current_user.id,
    )


@router.get("/attempts/{attempt_id}/state", response_model=TestAttemptStateRead, status_code=status.HTTP_200_OK)
async def get_attempt_state(
    attempt_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    attempt = await test_attempt_repo.get_attempt(db, attempt_id)
    if attempt is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attempt not found")
    if attempt.user_id != current_user.id and current_user.role not in {"teacher", "admin"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")

    test = await test_service.get_test_or_summary_access(db, attempt.test_id, current_user)
    if current_user.role == "teacher":
        await get_manageable_test(db, attempt.test_id, current_user)

    attempt, reason = await finalize_attempt_if_expired(db, test, attempt)
    if reason is not None:
        await bump_user_attempts_state_version(attempt.user_id)
    return build_attempt_state_payload(test=test, attempt=attempt, expired_reason=reason)


@router.post("/attempts/{attempt_id}/submit", response_model=TestAttemptRead, status_code=status.HTTP_200_OK)
async def submit_test_attempt(
    attempt_id: int,
    payload: AttemptSubmitRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Submit all attempt answers in one request and complete the attempt.
    Useful for reducing frontend N-request submit flows.
    """
    attempt = await test_attempt_repo.get_attempt(db, attempt_id)
    if attempt is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attempt not found")
    if attempt.user_id != current_user.id and current_user.role not in {"teacher", "admin"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")

    test = await test_service.get_test_or_summary_access(db, attempt.test_id, current_user)
    if current_user.role == "teacher":
        await get_manageable_test(db, attempt.test_id, current_user)

    if attempt.status == "completed":
        return attempt

    attempt, reason = await finalize_attempt_if_expired(db, test, attempt)
    if attempt.status == "completed":
        if reason is not None:
            await bump_user_attempts_state_version(attempt.user_id)
        return attempt

    try:
        await submit_answers_batch_for_attempt(
            db,
            user_id=attempt.user_id,
            test_id=attempt.test_id,
            attempt_id=attempt.id,
            answers=[(item.question_id, item.answer_payload) for item in payload.answers],
        )
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except IntegrityError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Concurrent answer update conflict; please retry",
        ) from exc

    completed_attempt = await test_attempt_repo.complete_attempt(db, attempt)
    await bump_user_attempts_state_version(completed_attempt.user_id)
    await analytics_repo.register_completed_attempt(
        db,
        completed_attempt.user_id,
        attempt_id=completed_attempt.id,
        sync_rewards=False,
    )
    schedule_attempt_completion_postprocess(
        db,
        user_id=completed_attempt.user_id,
        test_id=completed_attempt.test_id,
        attempt_id=completed_attempt.id,
    )
    return completed_attempt


@router.post("/attempts/{attempt_id}/complete", response_model=TestAttemptRead, status_code=status.HTTP_200_OK)
async def complete_test_attempt(
    attempt_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    attempt = await test_attempt_repo.get_attempt(db, attempt_id)
    if attempt is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attempt not found")
    if attempt.user_id != current_user.id and current_user.role not in {"teacher", "admin"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
    test = await test_service.get_test_or_summary_access(db, attempt.test_id, current_user)
    if current_user.role == "teacher":
        await get_manageable_test(db, attempt.test_id, current_user)
    if attempt.status == "completed":
        return attempt
    _, reason = await finalize_attempt_if_expired(db, test, attempt)
    if attempt.status == "completed":
        if reason is not None:
            await bump_user_attempts_state_version(attempt.user_id)
        return attempt
    completed_attempt = await test_attempt_repo.complete_attempt(db, attempt)
    await bump_user_attempts_state_version(completed_attempt.user_id)
    await analytics_repo.register_completed_attempt(
        db,
        completed_attempt.user_id,
        attempt_id=completed_attempt.id,
        sync_rewards=False,
    )
    schedule_attempt_completion_postprocess(
        db,
        user_id=completed_attempt.user_id,
        test_id=completed_attempt.test_id,
        attempt_id=completed_attempt.id,
    )
    return completed_attempt


@router.patch("/attempts/{attempt_id}/score", response_model=TestAttemptRead, status_code=status.HTTP_200_OK)
async def override_attempt_score(
    attempt_id: int,
    payload: AttemptScoreUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("teacher", "admin")),
):
    attempt = await test_attempt_repo.get_attempt(db, attempt_id)
    if attempt is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attempt not found")
    if current_user.role == "teacher":
        await get_manageable_test(db, attempt.test_id, current_user)
    if attempt.status != "completed":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Attempt must be completed before final grading")

    if attempt.max_score is None:
        attempt = await test_attempt_repo.refresh_attempt_scores(db, attempt)
    max_score = float(attempt.max_score or 0.0)
    if payload.score < 0 or payload.score > max_score:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Score must be between 0 and {max_score}",
        )

    updated_attempt = await test_attempt_repo.set_manual_score(db, attempt, payload.score)
    await bump_user_attempts_state_version(updated_attempt.user_id)
    try:
        await bump_cache_namespace(NS_TEST_SUMMARY)
    except Exception:
        pass
    return updated_attempt
