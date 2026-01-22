"""
Redis cache helpers: get/set/delete, get_or_set decorator, and distributed lock util.
Uses redis.asyncio client.
"""
import json
import asyncio
from typing import Any, Callable, Coroutine
import redis.asyncio as aioredis
from contextlib import asynccontextmanager
from app.core.config import settings

_redis: aioredis.Redis | None = None

def get_redis_client() -> aioredis.Redis:
    global _redis
    if _redis is None:
        _redis = aioredis.from_url(settings.redis_url, decode_responses=True)
    return _redis

async def initialize():
    get_redis_client()
    # connection happens lazily

async def close():
    global _redis
    if _redis is not None:
        await _redis.close()
        _redis = None

async def get(key: str):
    r = get_redis_client()
    data = await r.get(key)
    if data is None:
        return None
    try:
        return json.loads(data)
    except Exception:
        return data

async def set(key: str, value: Any, ttl: int | None = None):
    r = get_redis_client()
    data = json.dumps(value)
    if ttl:
        await r.set(key, data, ex=ttl)
    else:
        await r.set(key, data)

async def delete(*keys: str):
    r = get_redis_client()
    if not keys:
        return
    await r.delete(*keys)

async def delete_pattern(pattern: str):
    r = get_redis_client()
    cur = "0"
    keys = []
    while True:
        cur, found = await r.scan(cur, match=pattern, count=100)
        if found:
            keys.extend(found)
        if cur == "0":
            break
    if keys:
        await r.delete(*keys)

def cache_key_leaderboard(prefix: str = "leaderboard:top", n: int = 100):
    return f"{prefix}:{n}"

def cache_key_test_summary(test_id: int):
    return f"test:{test_id}:summary"

@asynccontextmanager
async def redis_lock(name: str, timeout: int = 10):
    """
    Simple lock context using redis.SETNX via redis.lock
    """
    r = get_redis_client()
    lock = r.lock(name, timeout=timeout)
    locked = await lock.acquire(blocking=True, blocking_timeout=5)
    try:
        yield locked
    finally:
        if locked:
            await lock.release()

async def get_or_set(key: str, ttl: int, fn: Callable[[], Coroutine[Any, Any, Any]]):
    """
    Get cached value or compute via async fn and set it.
    """
    val = await get(key)
    if val is not None:
        return val
    # compute
    data = await fn()
    await set(key, data, ttl=ttl)
    return data
