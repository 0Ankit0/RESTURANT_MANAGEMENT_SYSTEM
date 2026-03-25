from typing import Optional
from redis.asyncio import Redis
from src.apps.core.cache import RedisCache
from src.apps.core.config import settings


async def get_redis_cache() -> Optional[Redis]:
    """
    Dependency to get Redis cache client.
    Returns None in development (DEBUG=True), Redis client in production.
    
    Usage:
        @router.get("/endpoint")
        async def endpoint(cache: Redis = Depends(get_redis_cache)):
            if cache:
                # Use cache in production
                cached_data = await cache.get("key")
            else:
                # Skip cache in development
                pass
    """
    return await RedisCache.get_client()


def use_cache() -> bool:
    """
    Simple dependency that returns whether caching should be used.
    Returns False in development, True in production.
    
    Usage:
        @router.get("/endpoint")
        async def endpoint(should_cache: bool = Depends(use_cache)):
            if should_cache:
                # Cache logic
                pass
    """
    return not settings.DEBUG
