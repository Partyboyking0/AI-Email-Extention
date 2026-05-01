from backend.app.core.cache import HybridCache
import pytest


@pytest.mark.anyio
async def test_hybrid_cache_reuses_memory_value() -> None:
    cache = HybridCache(redis_url=None)
    calls = 0

    async def factory() -> dict[str, int]:
        nonlocal calls
        calls += 1
        return {"value": calls}

    first = await cache.get_or_set("test-key", factory)
    second = await cache.get_or_set("test-key", factory)

    assert first == {"value": 1}
    assert second == {"value": 1}
    assert calls == 1
