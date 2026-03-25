"""
Test Redis cache functionality
Run with: pytest tests/test_redis_cache.py -v
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from src.apps.core.cache import RedisCache
from src.apps.core.dependencies import get_redis_cache, use_cache


class TestRedisCacheProduction:
    """Test Redis cache in production mode (DEBUG=False)"""
    
    @pytest.mark.asyncio
    async def test_cache_disabled_in_debug_mode(self, monkeypatch):
        """Cache should return None in development mode"""
        monkeypatch.setattr("src.apps.core.config.settings.DEBUG", True)
        
        client = await RedisCache.get_client()
        assert client is None
    
    @pytest.mark.asyncio
    async def test_use_cache_dependency_debug_mode(self, monkeypatch):
        """use_cache should return False in debug mode"""
        monkeypatch.setattr("src.apps.core.config.settings.DEBUG", True)
        
        should_cache = use_cache()
        assert should_cache is False
    
    @pytest.mark.asyncio
    async def test_use_cache_dependency_production_mode(self, monkeypatch):
        """use_cache should return True in production mode"""
        monkeypatch.setattr("src.apps.core.config.settings.DEBUG", False)
        
        should_cache = use_cache()
        assert should_cache is True
    
    @pytest.mark.asyncio
    async def test_get_redis_cache_dependency_debug(self, monkeypatch):
        """get_redis_cache should return None in debug mode"""
        monkeypatch.setattr("src.apps.core.config.settings.DEBUG", True)
        
        cache = await get_redis_cache()
        assert cache is None
    
    @pytest.mark.asyncio
    async def test_cache_operations_in_debug_mode(self, monkeypatch):
        """All cache operations should handle None gracefully in debug mode"""
        monkeypatch.setattr("src.apps.core.config.settings.DEBUG", True)
        
        # These should all return None/False without errors
        result = await RedisCache.get("test_key")
        assert result is None
        
        success = await RedisCache.set("test_key", {"data": "value"})
        assert success is False
        
        exists = await RedisCache.exists("test_key")
        assert exists is False
        
        deleted = await RedisCache.delete("test_key")
        assert deleted is False
        
        cleared = await RedisCache.clear_pattern("test:*")
        assert cleared == 0


class TestRedisCacheMocked:
    """Test Redis cache with mocked Redis client"""
    
    @pytest.mark.asyncio
    async def test_cache_get_success(self, monkeypatch):
        """Test successful cache get operation"""
        monkeypatch.setattr("src.apps.core.config.settings.DEBUG", False)
        
        mock_redis = AsyncMock()
        mock_redis.get.return_value = '{"user": "test"}'
        
        with patch.object(RedisCache, 'get_client', return_value=mock_redis):
            result = await RedisCache.get("test_key")
            assert result == {"user": "test"}
            mock_redis.get.assert_called_once_with("test_key")
    
    @pytest.mark.asyncio
    async def test_cache_set_success(self, monkeypatch):
        """Test successful cache set operation"""
        monkeypatch.setattr("src.apps.core.config.settings.DEBUG", False)
        
        mock_redis = AsyncMock()
        mock_redis.setex.return_value = True
        
        with patch.object(RedisCache, 'get_client', return_value=mock_redis):
            result = await RedisCache.set("test_key", {"user": "test"}, ttl=300)
            assert result is True
            mock_redis.setex.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_cache_delete_success(self, monkeypatch):
        """Test successful cache delete operation"""
        monkeypatch.setattr("src.apps.core.config.settings.DEBUG", False)
        
        mock_redis = AsyncMock()
        mock_redis.delete.return_value = 1
        
        with patch.object(RedisCache, 'get_client', return_value=mock_redis):
            result = await RedisCache.delete("test_key")
            assert result is True
            mock_redis.delete.assert_called_once_with("test_key")
    
    @pytest.mark.asyncio
    async def test_cache_exists_success(self, monkeypatch):
        """Test successful cache exists operation"""
        monkeypatch.setattr("src.apps.core.config.settings.DEBUG", False)
        
        mock_redis = AsyncMock()
        mock_redis.exists.return_value = 1
        
        with patch.object(RedisCache, 'get_client', return_value=mock_redis):
            result = await RedisCache.exists("test_key")
            assert result is True
            mock_redis.exists.assert_called_once_with("test_key")
    
    @pytest.mark.asyncio
    async def test_cache_clear_pattern(self, monkeypatch):
        """Test clearing cache by pattern"""
        monkeypatch.setattr("src.apps.core.config.settings.DEBUG", False)
        
        mock_redis = AsyncMock()
        
        # Mock scan_iter to return keys
        async def mock_scan_iter(match):
            for key in ["user:1", "user:2", "user:3"]:
                yield key
        
        mock_redis.scan_iter = mock_scan_iter
        mock_redis.delete.return_value = 3
        
        with patch.object(RedisCache, 'get_client', return_value=mock_redis):
            result = await RedisCache.clear_pattern("user:*")
            assert result == 3
    
    @pytest.mark.asyncio
    async def test_cache_handles_json_serialization_error(self, monkeypatch):
        """Test cache handles non-serializable objects gracefully"""
        monkeypatch.setattr("src.apps.core.config.settings.DEBUG", False)
        
        mock_redis = AsyncMock()
        
        with patch.object(RedisCache, 'get_client', return_value=mock_redis):
            # Try to cache a non-serializable object
            class NonSerializable:
                pass
            
            result = await RedisCache.set("test_key", NonSerializable())
            assert result is False
    
    @pytest.mark.asyncio
    async def test_cache_handles_redis_exception(self, monkeypatch):
        """Test cache handles Redis connection errors gracefully"""
        monkeypatch.setattr("src.apps.core.config.settings.DEBUG", False)
        
        mock_redis = AsyncMock()
        mock_redis.get.side_effect = Exception("Connection error")
        
        with patch.object(RedisCache, 'get_client', return_value=mock_redis):
            result = await RedisCache.get("test_key")
            assert result is None
    
    @pytest.mark.asyncio
    async def test_cache_close(self):
        """Test cache connection cleanup"""
        mock_redis = AsyncMock()
        mock_pool = MagicMock()
        mock_pool.disconnect = AsyncMock()
        
        RedisCache._client = mock_redis
        RedisCache._pool = mock_pool
        
        await RedisCache.close()
        
        mock_redis.close.assert_called_once()
        mock_pool.disconnect.assert_called_once()
        assert RedisCache._client is None
        assert RedisCache._pool is None
