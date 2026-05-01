from collections import defaultdict, deque
from time import monotonic

from fastapi import HTTPException, status
from redis.asyncio import Redis
from redis.exceptions import RedisError


class SlidingWindowRateLimiter:
    def __init__(self, max_requests: int = 100, window_seconds: int = 3600, redis_url: str | None = None) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._events: dict[str, deque[float]] = defaultdict(deque)
        self.redis: Redis | None = Redis.from_url(redis_url, decode_responses=True) if redis_url else None

    async def check(self, user_id: str) -> None:
        if self.redis is not None:
            try:
                await self._check_redis(user_id)
                return
            except RedisError:
                pass

        self._check_memory(user_id)

    def _check_memory(self, user_id: str) -> None:
        now = monotonic()
        events = self._events[user_id]

        while events and now - events[0] > self.window_seconds:
            events.popleft()

        if len(events) >= self.max_requests:
            retry_after = max(1, int(self.window_seconds - (now - events[0])))
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded",
                headers={"Retry-After": str(retry_after)},
            )

        events.append(now)

    async def _check_redis(self, user_id: str) -> None:
        now_ms = int(monotonic() * 1000)
        window_ms = self.window_seconds * 1000
        key = f"rate-limit:{user_id}"
        cutoff = now_ms - window_ms

        pipe = self.redis.pipeline()
        pipe.zremrangebyscore(key, 0, cutoff)
        pipe.zadd(key, {str(now_ms): now_ms})
        pipe.zcard(key)
        pipe.expire(key, self.window_seconds)
        results = await pipe.execute()
        request_count = int(results[2])

        if request_count > self.max_requests:
            oldest = await self.redis.zrange(key, 0, 0, withscores=True)
            retry_after = 1
            if oldest:
                retry_after = max(1, int((window_ms - (now_ms - int(oldest[0][1]))) / 1000))
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded",
                headers={"Retry-After": str(retry_after)},
            )
