"""
Orchestration service for answers:
- persist answer
- try auto-grade (MCQ)
- update analytics
- invalidate cache
- queue open-answer jobs for manual grading
"""
import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import noload

from app.api.deps import add_post_commit_task
from app.repositories import answer_repo, analytics_repo, test_attempt_repo
from app.models.answer import Answer
from app.models.choice import Choice
from app.models.question import Question
from app.cache.redis_cache import NS_LEADERBOARD, NS_TEST_SUMMARY, bump_cache_namespace, get_redis_client
from app.services.challenge_service import ChallengeEventType, record_event
from app.tasks.task_queue import enqueue_open_answer_grading

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AnswerBatchSubmitResult:
    answers_count: int
    points_delta: float
    open_answers_count: int


async def submit_answer(
    session,
    user_id: int,
    test_id: int,
    question_id: int,
    payload: str,
    attempt_id: int | None = None,
    *,
    validate_attempt: bool = True,
):
    """
    High-level flow:
    1) persist answer
    2) load question to know if open/MCQ
    3) if MCQ -> grade immediately; update analytics
       if open -> push job to redis 'grading:open' and leave score NULL
    4) invalidate caches (leaderboard/test summary/user analytics)
    Returns the Answer object (possibly graded).
    """
    question: Optional[Question] = await session.get(Question, question_id)
    if question is None:
        raise LookupError("Question not found")
    if question.test_id != test_id:
        raise ValueError("Question does not belong to the specified test")
    normalized_payload = "" if payload is None else str(payload)
    trimmed_payload = normalized_payload.strip()

    if attempt_id is not None and validate_attempt:
        attempt = await test_attempt_repo.get_attempt(session, attempt_id)
        if attempt is None:
            raise LookupError("Attempt not found")
        if attempt.user_id != user_id or attempt.test_id != test_id:
            raise ValueError("Attempt does not belong to the specified user/test")
        if attempt.status == "completed":
            raise ValueError("Attempt is already completed")

    is_open = bool(question.is_open_answer)
    skipped_closed_answer = False
    skipped_open_answer = False
    should_enqueue_open_grading = False

    if not is_open:
        if trimmed_payload.lower() in {"", "null", "none"}:
            skipped_closed_answer = True
            normalized_payload = ""
        else:
            try:
                choice_id = int(trimmed_payload)
            except (TypeError, ValueError):
                raise ValueError("Closed question answer must be a valid choice id")
            choice: Optional[Choice] = await session.get(Choice, choice_id)
            if choice is None or choice.question_id != question_id:
                raise ValueError("Selected choice does not belong to the specified question")
    elif trimmed_payload == "":
        skipped_open_answer = True

    # 1) persist or replace an existing answer for the same question slot
    ans, previous_score = await answer_repo.upsert_answer(
        session,
        user_id=user_id,
        test_id=test_id,
        question_id=question_id,
        payload=normalized_payload,
        attempt_id=attempt_id,
    )

    # 3) auto-grade if not open-answer (MCQ)
    graded = None
    points_delta = -previous_score if is_open else 0.0
    if not is_open:
        graded = await answer_repo.grade_mcq_answer(session, ans.id)
        current_score = float(graded.score) if (graded and graded.score is not None) else 0.0
        points_delta = current_score - previous_score
        if skipped_closed_answer and graded is not None and graded.score is None:
            # Keep skipped MCQ explicitly zero-scored for stable attempt aggregation.
            graded.score = 0.0
            await session.flush()
            await session.refresh(graded)
    else:
        if skipped_open_answer:
            # Empty open answer is treated as an intentionally skipped question.
            ans.score = 0.0
            ans.graded_by = None
            ans.graded_at = None
            await session.flush()
            await session.refresh(ans)
        else:
            # Queueing is done post-commit to avoid worker races with uncommitted rows.
            should_enqueue_open_grading = True

    await analytics_repo.create_or_update_analytics(
        session,
        user_id=user_id,
        points_delta=points_delta,
        mark_active=True,
        reason_code="answer_auto_graded" if not is_open else "answer_open_submitted",
        source_type="answer",
        source_id=ans.id,
        metadata={
            "test_id": test_id,
            "question_id": question_id,
            "attempt_id": attempt_id,
            "is_open_answer": is_open,
        },
    )
    await record_event(
        session,
        user_id=user_id,
        event_type=ChallengeEventType.ANSWER_SUBMITTED,
        increment=1,
    )
    await record_event(
        session,
        user_id=user_id,
        event_type=ChallengeEventType.STREAK_DAY,
        increment=1,
    )
    if attempt_id is not None:
        attempt = await test_attempt_repo.get_attempt(session, attempt_id)
        if attempt is not None:
            await test_attempt_repo.refresh_attempt_scores(session, attempt)

    async def invalidate_after_commit() -> None:
        try:
            await bump_cache_namespace(NS_LEADERBOARD, NS_TEST_SUMMARY)
        except Exception:
            pass

    add_post_commit_task(session, invalidate_after_commit)

    if should_enqueue_open_grading:
        async def enqueue_open_grading_after_commit() -> None:
            try:
                await enqueue_open_answer_grading(answer_id=int(ans.id), user_id=int(user_id))
            except Exception:
                logger.exception("Failed to enqueue open-answer grading job", extra={"answer_id": ans.id})

        add_post_commit_task(session, enqueue_open_grading_after_commit)

    return graded if graded is not None else ans


async def submit_answers_batch_for_attempt(
    session,
    *,
    user_id: int,
    test_id: int,
    attempt_id: int,
    answers: list[tuple[int, str]],
) -> AnswerBatchSubmitResult:
    """
    Optimized batch submit for attempt payloads.
    Processes answers in-memory with one prefetch pass.
    Secondary analytics/challenge effects are scheduled by the caller after commit.
    """
    if not answers:
        return AnswerBatchSubmitResult(answers_count=0, points_delta=0.0, open_answers_count=0)

    question_ids = [int(question_id) for question_id, _ in answers]
    unique_question_ids = list(dict.fromkeys(question_ids))

    question_rows = (
        await session.execute(
            select(
                Question.id,
                Question.test_id,
                Question.points,
                Question.is_open_answer,
            ).where(Question.id.in_(unique_question_ids))
        )
    ).all()
    question_map = {
        int(question_id): {
            "id": int(question_id),
            "test_id": int(test_id),
            "points": float(points or 0.0),
            "is_open_answer": bool(is_open_answer),
        }
        for question_id, test_id, points, is_open_answer in question_rows
    }

    normalized_items: list[tuple[int, bool, float, str, str, int | None]] = []
    choice_ids: set[int] = set()

    for question_id, payload in answers:
        normalized_question_id = int(question_id)
        question = question_map.get(normalized_question_id)
        if question is None:
            raise LookupError("Question not found")
        if int(question["test_id"]) != int(test_id):
            raise ValueError("Question does not belong to the specified test")

        normalized_payload = "" if payload is None else str(payload)
        trimmed_payload = normalized_payload.strip()

        parsed_choice_id: int | None = None
        if not question["is_open_answer"] and trimmed_payload.lower() not in {"", "null", "none"}:
            try:
                parsed_choice_id = int(trimmed_payload)
            except (TypeError, ValueError):
                raise ValueError("Closed question answer must be a valid choice id")
            choice_ids.add(parsed_choice_id)

        normalized_items.append(
            (
                normalized_question_id,
                bool(question["is_open_answer"]),
                float(question["points"]),
                normalized_payload,
                trimmed_payload,
                parsed_choice_id,
            )
        )

    choice_map: dict[int, dict[str, int | bool]] = {}
    if choice_ids:
        choice_rows = (
            await session.execute(
                select(Choice.id, Choice.question_id, Choice.is_correct).where(Choice.id.in_(choice_ids))
            )
        ).all()
        choice_map = {
            int(choice_id): {
                "question_id": int(question_id),
                "is_correct": bool(is_correct),
            }
            for choice_id, question_id, is_correct in choice_rows
        }

    existing_rows = (
        await session.execute(
            select(Answer)
            .options(noload("*"))
            .where(
                Answer.user_id == user_id,
                Answer.test_id == test_id,
                Answer.attempt_id == attempt_id,
                Answer.question_id.in_(unique_question_ids),
            )
        )
    ).scalars().all()
    answers_by_question_id: dict[int, Answer] = {
        int(answer.question_id): answer for answer in existing_rows
    }

    open_answers_to_queue: list[Answer] = []
    total_points_delta = 0.0
    submitted_answers_count = 0

    for (
        question_id,
        is_open,
        question_points,
        normalized_payload,
        trimmed_payload,
        parsed_choice_id,
    ) in normalized_items:
        submitted_answers_count += 1
        score: float | None = None

        if not is_open:
            if trimmed_payload.lower() in {"", "null", "none"}:
                normalized_payload = ""
                score = 0.0
            else:
                if parsed_choice_id is None:
                    raise ValueError("Closed question answer must be a valid choice id")
                choice = choice_map.get(parsed_choice_id)
                if choice is None or int(choice["question_id"]) != question_id:
                    raise ValueError("Selected choice does not belong to the specified question")
                score = question_points if bool(choice["is_correct"]) else 0.0
        else:
            if trimmed_payload == "":
                score = 0.0
            else:
                score = None

        existing_answer = answers_by_question_id.get(question_id)
        previous_score = float(existing_answer.score or 0.0) if existing_answer is not None else 0.0

        if existing_answer is None:
            existing_answer = Answer(
                user_id=user_id,
                test_id=test_id,
                attempt_id=attempt_id,
                question_id=question_id,
                answer_payload=normalized_payload,
            )
            session.add(existing_answer)
            answers_by_question_id[question_id] = existing_answer
        else:
            existing_answer.answer_payload = normalized_payload

        existing_answer.score = score
        existing_answer.graded_by = None
        existing_answer.graded_at = None

        total_points_delta += float(score or 0.0) - previous_score

        if is_open and trimmed_payload != "":
            open_answers_to_queue.append(existing_answer)

    await session.flush()

    async def invalidate_after_commit() -> None:
        try:
            await bump_cache_namespace(NS_LEADERBOARD, NS_TEST_SUMMARY)
        except Exception:
            pass

    add_post_commit_task(session, invalidate_after_commit)

    if open_answers_to_queue:
        queued_answer_ids = [int(answer.id) for answer in open_answers_to_queue if answer.id is not None]

        async def enqueue_open_grading_after_commit() -> None:
            try:
                for answer_id in queued_answer_ids:
                    await enqueue_open_answer_grading(answer_id=int(answer_id), user_id=int(user_id))
            except Exception:
                logger.exception(
                    "Failed to enqueue open-answer grading jobs",
                    extra={"answer_ids": queued_answer_ids},
                )

        add_post_commit_task(session, enqueue_open_grading_after_commit)

    return AnswerBatchSubmitResult(
        answers_count=submitted_answers_count,
        points_delta=total_points_delta,
        open_answers_count=len(open_answers_to_queue),
    )


async def manual_grade_open_answer(session, answer_id: int, grader_id: int, score: float) -> Answer:
    answer: Optional[Answer] = await session.get(Answer, answer_id)
    if answer is None:
        raise LookupError("Answer not found")

    question: Optional[Question] = await session.get(Question, answer.question_id)
    if question is None:
        raise LookupError("Question not found")
    if not question.is_open_answer:
        raise ValueError("Manual grading is allowed only for open-answer questions")

    max_score = float(question.points)
    normalized_score = float(score)
    if normalized_score < 0 or normalized_score > max_score:
        raise ValueError(f"Score must be between 0 and {max_score}")

    previous_score = float(answer.score or 0.0)
    answer.score = normalized_score
    answer.graded_by = grader_id
    answer.graded_at = datetime.now(UTC).replace(tzinfo=None)
    await session.flush()
    await session.refresh(answer)

    delta = normalized_score - previous_score
    if delta != 0:
        await analytics_repo.apply_points_delta(
            session,
            answer.user_id,
            delta,
            reason_code="answer_manual_grade",
            source_type="answer",
            source_id=answer.id,
            idempotency_key=f"answer_manual_grade:{answer.id}:{normalized_score}",
            metadata={
                "question_id": answer.question_id,
                "attempt_id": answer.attempt_id,
                "grader_id": grader_id,
            },
        )
        if answer.attempt_id is not None:
            attempt = await test_attempt_repo.get_attempt(session, answer.attempt_id)
            if attempt is not None:
                await test_attempt_repo.refresh_attempt_scores(session, attempt)

        try:
            await bump_cache_namespace(NS_LEADERBOARD, NS_TEST_SUMMARY)
        except Exception:
            pass

    return answer
