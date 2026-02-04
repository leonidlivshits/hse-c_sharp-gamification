import asyncio
import json
import logging
from typing import Optional

from app.cache.redis_cache import get_redis_client
from app.db.session import AsyncSessionLocal
from app.models.answer import Answer

logger = logging.getLogger("worker")


async def process_job(job_payload: str) -> None:
    try:
        data = json.loads(job_payload)
    except Exception:
        logger.exception("Invalid job payload (not json): %s", job_payload)
        return

    answer_id = data.get("answer_id")
    user_id = data.get("user_id")
    logger.info("Open answer queued for manual grading: answer_id=%s user_id=%s", answer_id, user_id)

    if answer_id is None:
        logger.warning("Job missing answer_id: %s", data)
        return

    # ensure record exists (do not modify schema here)
    async with AsyncSessionLocal() as session:
        ans: Optional[Answer] = await session.get(Answer, answer_id)
        if ans:
            logger.info("Found answer %s for manual grading (user_id=%s)", answer_id, ans.user_id)
        else:
            logger.warning("Answer %s not found in DB", answer_id)


async def run_worker() -> None:
    r = get_redis_client()
    logger.info("Worker started: polling grading:open")
    while True:
        try:
            # BLPOP returns tuple (key, value) or None
            item = await r.blpop("grading:open", timeout=5)
            if not item:
                # timeout - loop again (allows graceful shutdown)
                await asyncio.sleep(0.1)
                continue
            _, payload = item
            await process_job(payload)
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
