import json
import asyncio
from typing import Any, Callable, Coroutine, Optional
import redis.asyncio as aioredis
from contextlib import asynccontextmanager
from app.core.config import settings

_redis: Optional[aioredis.Redis] = None

def get_redis_client() -> aioredis.Redis:
    global _redis
    if _redis is None:
        _redis = aioredis.from_url(settings.redis_url, decode_responses=True)
    return _redis

async def initialize():
    r = get_redis_client()
    try:
        await r.ping()
    except Exception:
        # connection lazy; just ignore here
        pass

async def close():
    global _redis
    if _redis is not None:
        try:
            await _redis.close()
        finally:
            _redis = None

async def get(key: str) -> Any:
    r = get_redis_client()
    data = await r.get(key)
    if data is None:
        return None
    try:
        return json.loads(data)
    except Exception:
        return data

async def set(key: str, value: Any, ttl: Optional[int] = None) -> None:
    r = get_redis_client()
    data = json.dumps(value)
    if ttl:
        await r.set(key, data, ex=ttl)
    else:
        await r.set(key, data)

async def delete(*keys: str) -> None:
    if not keys:
        return
    r = get_redis_client()
    await r.delete(*keys)

async def delete_pattern(pattern: str) -> None:
    """
    Delete keys matching pattern. Uses SCAN to avoid blocking.
    """
    r = get_redis_client()
    cur = 0
    keys = []
    while True:
        cur, found = await r.scan(cur, match=pattern, count=500)
        if found:
            keys.extend(found)
        if cur == 0 or cur == "0":
            break
    if keys:
        # chunk deletes by 500 to be safe
        chunk_size = 500
        for i in range(0, len(keys), chunk_size):
            await r.delete(*keys[i:i+chunk_size])

def cache_key_leaderboard(prefix: str = "leaderboard:top", n: int = 100) -> str:
    return f"{prefix}:{n}"

def cache_key_test_summary(test_id: int) -> str:
    return f"test:{test_id}:summary"

@asynccontextmanager
async def redis_lock(name: str, timeout: int = 10):
    r = get_redis_client()
    lock = r.lock(name, timeout=timeout)
    locked = await lock.acquire(blocking=True, blocking_timeout=5)
    try:
        yield locked
    finally:
        if locked:
            try:
                await lock.release()
            except Exception:
                pass

async def get_or_set(key: str, ttl: int, fn: Callable[[], Coroutine[Any, Any, Any]]):
    val = await get(key)
    if val is not None:
        return val
    data = await fn()
    # set even if data is None (optional choice)
    await set(key, data, ttl=ttl)
    return data
