"""
app/cache/redis_client.py
DESCRIPTION: simple redis async client wrapper using redis.asyncio.
"""
import redis.asyncio as aioredis
from app.core.config import settings

class RedisClient:
    def __init__(self):
        self._client: aioredis.Redis | None = None

    async def initialize(self):
        if self._client is None:
            self._client = aioredis.from_url(settings.redis_url, decode_responses=True)

    async def get(self) -> aioredis.Redis:
        if self._client is None:
            await self.initialize()
        return self._client

    async def close(self):
        if self._client is not None:
            await self._client.close()
            self._client = None

redis_client = RedisClient()
