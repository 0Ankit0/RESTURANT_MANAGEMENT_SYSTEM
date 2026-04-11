import logging
from unittest.mock import AsyncMock

import pytest

from src.apps.core.cache import RedisCache


@pytest.mark.asyncio
async def test_redis_get_logs_warning_on_failure(monkeypatch, caplog):
    failing_client = AsyncMock()
    failing_client.get.side_effect = RuntimeError("redis unavailable")
    monkeypatch.setattr(RedisCache, "get_client", AsyncMock(return_value=failing_client))

    with caplog.at_level(logging.WARNING):
        result = await RedisCache.get("tokens:active:1")

    assert result is None
    assert "core.cache.get_failed" in caplog.text
    assert any(getattr(record, "cache_key", None) == "tokens:active:1" for record in caplog.records)
