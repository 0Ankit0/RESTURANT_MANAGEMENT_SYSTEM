from typing import Optional, Any
import json
from redis.asyncio import Redis, ConnectionPool
from src.apps.core.config import settings


class RedisCache:
    """Redis cache client for production environment"""
    
    _pool: Optional[ConnectionPool] = None
    _client: Optional[Redis] = None
    
    @classmethod
    async def get_client(cls) -> Optional[Redis]:
        """Get Redis client instance, only in production"""
        if settings.DEBUG:
            return None
        assert settings.REDIS_URL, "REDIS_URL must be set in production"
        
        if cls._client is None:
            cls._pool = ConnectionPool.from_url(
                settings.REDIS_URL,
                max_connections=settings.REDIS_MAX_CONNECTIONS,
                decode_responses=True
            )
            cls._client = Redis(connection_pool=cls._pool)
        
        return cls._client
    
    @classmethod
    async def close(cls):
        """Close Redis connection"""
        if cls._client:
            await cls._client.close()
            cls._client = None
        if cls._pool:
            await cls._pool.disconnect()
            cls._pool = None
    
    @classmethod
    async def get(cls, key: str) -> Optional[Any]:
        """Get value from cache"""
        client = await cls.get_client()
        if not client:
            return None
        
        try:
            value = await client.get(key)
            if value:
                return json.loads(value)
        except Exception:
            pass
        return None
    
    @classmethod
    async def set(cls, key: str, value: Any, ttl: int = 3600) -> bool:
        """Set value in cache with TTL (default 1 hour)"""
        client = await cls.get_client()
        if not client:
            return False
        
        try:
            serialized = json.dumps(value)
            await client.setex(key, ttl, serialized)
            return True
        except Exception:
            return False
    
    @classmethod
    async def delete(cls, key: str) -> bool:
        """Delete value from cache"""
        client = await cls.get_client()
        if not client:
            return False
        
        try:
            await client.delete(key)
            return True
        except Exception:
            return False
    
    @classmethod
    async def exists(cls, key: str) -> bool:
        """Check if key exists in cache"""
        client = await cls.get_client()
        if not client:
            return False
        
        try:
            return bool(await client.exists(key))
        except Exception:
            return False
    
    @classmethod
    async def clear_pattern(cls, pattern: str) -> int:
        """Clear all keys matching pattern"""
        client = await cls.get_client()
        if not client:
            return 0
        
        try:
            keys = []
            async for key in client.scan_iter(match=pattern):
                keys.append(key)
            
            if keys:
                return await client.delete(*keys)
            return 0
        except Exception:
            return 0
