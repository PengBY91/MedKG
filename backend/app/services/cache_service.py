import json
import logging
import functools
from typing import Any, Optional, Union
import redis.asyncio as redis
from app.core.config import settings

logger = logging.getLogger(__name__)

class CacheService:
    """
    Redis-based caching service using redis-py (formerly aioredis).
    """
    def __init__(self, host: str = "localhost", port: int = 6379, db: int = 0):
        self.redis_url = f"redis://{host}:{port}/{db}"
        self._redis: Optional[redis.Redis] = None

    async def _get_redis(self) -> redis.Redis:
        if self._redis is None:
            try:
                self._redis = redis.from_url(self.redis_url, encoding="utf-8", decode_responses=True)
                # Test connection
                await self._redis.ping()
                logger.info("Connected to Redis for caching.")
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {str(e)}")
                self._redis = None
                raise e
        return self._redis

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        try:
            r = await self._get_redis()
            value = await r.get(key)
            return json.loads(value) if value else None
        except Exception as e:
            logger.warning(f"Cache get failed for key {key}: {str(e)}")
            return None

    async def set(self, key: str, value: Any, expire: int = 3600):
        """Set value in cache with expiration (default 1h)."""
        try:
            r = await self._get_redis()
            await r.set(key, json.dumps(value), ex=expire)
        except Exception as e:
            logger.warning(f"Cache set failed for key {key}: {str(e)}")

    async def delete(self, key: str):
        """Delete from cache."""
        try:
            r = await self._get_redis()
            await r.delete(key)
        except Exception as e:
            logger.warning(f"Cache delete failed for key {key}: {str(e)}")

    async def clear_pattern(self, pattern: str):
        """Clear cache keys by pattern."""
        try:
            r = await self._get_redis()
            keys = await r.keys(pattern)
            if keys:
                await r.delete(*keys)
        except Exception as e:
            logger.warning(f"Cache clear_pattern failed for {pattern}: {str(e)}")

def cached(prefix: str, expire: int = 3600):
    """
    Decorator for caching function results.
    Usage: @cached("stats", expire=300)
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Formulate cache key
            key_parts = [prefix]
            if args:
                # Skip 'self' or 'cls' usually the first arg in services
                key_parts.extend([str(a) for a in args[1:]])
            if kwargs:
                sorted_items = sorted(kwargs.items())
                key_parts.extend([f"{k}:{v}" for k, v in sorted_items])
            
            cache_key = ":".join(key_parts)
            
            # Try to get from cache
            cached_value = await cache_service.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Save to cache
            await cache_service.set(cache_key, result, expire=expire)
            
            return result
        return wrapper
    return decorator

# Singleton instance
cache_service = CacheService()
