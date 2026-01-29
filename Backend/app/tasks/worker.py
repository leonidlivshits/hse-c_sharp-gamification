"""
Simple background worker that polls Redis list 'grading:open' for open answers.
When an open-answer job arrives, it currently logs it and leaves the answer for manual grading.
Extend to send notifications / assign to teachers.
Run via docker-compose worker service (already configured).
"""
import asyncio
import json
import logging
from app.cache.redis_cache import get_redis_client
from app.db.session import AsyncSessionLocal
from sqlalchemy import select
from app.models.answer import Answer

logger = logging.getLogger("worker")

async def process_job(job_payload: str):
    data = json.loads(job_payload)
    answer_id = data.get("answer_id")
    user_id = data.get("user_id")
    logger.info("Open answer queued for manual grading: answer_id=%s user_id=%s", answer_id, user_id)

    # Example: mark DB record as 'needs_review' by setting score = NULL and maybe a flag (if present).
    # We don't change schema here; instead, we can insert a placeholder in another table or send notification.
    # For demo: just ensure record exists.
    async with AsyncSessionLocal() as session:
        ans = await session.get(Answer, answer_id)
        if ans:
            logger.info("Found answer %s, leaving for manual grading", answer_id)
        else:
            logger.warning("Answer %s not found", answer_id)

async def run_worker():
    r = get_redis_client()
    logger.info("Worker started: polling grading:open")
    while True:
        try:
            item = await r.blpop("grading:open", timeout=5)
            if not item:
                await asyncio.sleep(0.2)
                continue
            # item is (key, value)
            _, payload = item
            await process_job(payload)
        except Exception as e:
            logger.exception("Worker error: %s", e)
            await asyncio.sleep(1)  # backoff

if __name__ == "__main__":
    # Simple bootstrap when run as module (docker-compose runs python -m app.tasks.worker)
    import logging, sys
    logging.basicConfig(stream=sys.stdout, level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    asyncio.run(run_worker())
