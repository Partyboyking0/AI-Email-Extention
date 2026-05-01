import hashlib
import json
from collections.abc import Awaitable, Callable
from typing import TypeVar

from redis.asyncio import Redis
from redis.exceptions import RedisError

T = TypeVar("T")


def cache_key(namespace: str, text: str) -> str:
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return f"{namespace}:{digest}"


class MemoryCache:
    def __init__(self) -> None:
        self._items: dict[str, str] = {}

    async def get_or_set(self, key: str, factory: Callable[[], Awaitable[T]]) -> T:
        if key in self._items:
            return json.loads(self._items[key])
        value = await factory()
        self._items[key] = json.dumps(value)
        return value


class HybridCache:
    def __init__(self, redis_url: str | None = None, ttl_seconds: int = 600) -> None:
        self.ttl_seconds = ttl_seconds
        self.memory = MemoryCache()
        self.redis: Redis | None = Redis.from_url(redis_url, decode_responses=True) if redis_url else None

    async def get_or_set(self, key: str, factory: Callable[[], Awaitable[T]]) -> T:
        if self.redis is None:
            return await self.memory.get_or_set(key, factory)

        try:
            cached = await self.redis.get(key)
            if cached is not None:
                return json.loads(cached)

            value = await factory()
            await self.redis.set(key, json.dumps(value), ex=self.ttl_seconds)
            return value
        except RedisError:
            return await self.memory.get_or_set(key, factory)
