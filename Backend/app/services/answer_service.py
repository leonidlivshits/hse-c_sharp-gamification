"""
submit_answer orchestrates:
- persist answer via answer_repo.record_answer
- if MCQ: grade immediately via answer_repo.grade_mcq_answer
- update analytics (points)
- invalidate caches: leaderboard and test summary
- if open answer: push to redis queue for manual grading (worker)
"""
import json
from app.repositories import answer_repo, analytics_repo
from app.cache.redis_cache import get_redis_client, delete_pattern, cache_key_test_summary, cache_key_leaderboard
from app.db.session import AsyncSessionLocal

async def submit_answer(session, user_id: int, test_id: int, question_id: int, payload: str):
    # persist
    ans = await answer_repo.record_answer(session, user_id, test_id, question_id, payload)

    # try to auto-grade (MCQ)
    graded = await answer_repo.grade_mcq_answer(session, ans.id)
    points_awarded = graded.score if graded and graded.score is not None else 0.0

    # update analytics
    await analytics_repo.create_or_update_analytics(session, user_id, points_delta=points_awarded, mark_active=True)

    # cache invalidation: leaderboard + test summary for this test
    # leaderboards keyed by leaderboard:top:<N> => delete patterns
    await delete_pattern("leaderboard:top:*")
    await delete_pattern(f"test:{test_id}:summary*")

    # if not graded (open answer), enqueue for manual grading
    if graded and graded.score is None:
        # open answer: push job for worker (stores minimal info)
        r = get_redis_client()
        job = {"answer_id": graded.id, "user_id": user_id}
        await r.rpush("grading:open", json.dumps(job))

    return graded
