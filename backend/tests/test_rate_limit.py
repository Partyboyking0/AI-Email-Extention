import pytest
from fastapi import HTTPException

from backend.app.core.rate_limit import SlidingWindowRateLimiter


@pytest.mark.anyio
async def test_memory_rate_limiter_blocks_after_limit() -> None:
    limiter = SlidingWindowRateLimiter(max_requests=2, window_seconds=60, redis_url=None)

    await limiter.check("user-1")
    await limiter.check("user-1")

    with pytest.raises(HTTPException) as exc:
        await limiter.check("user-1")

    assert exc.value.status_code == 429
    assert exc.value.headers["Retry-After"]
