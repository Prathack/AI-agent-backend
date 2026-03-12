"""
Redis Cache Manager
Falls back to in-memory cache when Redis is unavailable.
"""

import json
import logging
import time
from typing import Any, Dict, Optional

logger = logging.getLogger("rental_agent.cache")


class InMemoryCache:
    """Simple TTL-based in-memory cache (Redis fallback)."""

    def __init__(self):
        self._store: Dict[str, Dict] = {}

    def get(self, key: str) -> Optional[Any]:
        if key not in self._store:
            return None
        entry = self._store[key]
        if time.time() > entry["expires_at"]:
            del self._store[key]
            return None
        return entry["value"]

    def set(self, key: str, value: Any, ttl: int = 3600):
        self._store[key] = {
            "value": value,
            "expires_at": time.time() + ttl,
        }

    def delete(self, key: str):
        self._store.pop(key, None)

    def flush(self):
        self._store.clear()


class CacheManager:
    """
    Wraps Redis (preferred) or in-memory fallback.
    Async interface for FastAPI compatibility.
    """

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self._redis = None
        self._memory = InMemoryCache()
        self._using_redis = False
        self._try_connect(redis_url)

    def _try_connect(self, redis_url: str):
        try:
            import redis
            r = redis.from_url(redis_url, socket_connect_timeout=2)
            r.ping()
            self._redis = r
            self._using_redis = True
            logger.info("Redis cache connected")
        except Exception:
            logger.warning("Redis unavailable — using in-memory cache")

    @staticmethod
    def build_key(provider: str, pickup: str, dropoff: str, date: str) -> str:
        raw = f"{provider}:{pickup}:{dropoff}:{date}"
        return raw.lower().replace(" ", "_").replace(",", "")

    async def get(self, key: str) -> Optional[Dict]:
        try:
            if self._using_redis:
                val = self._redis.get(key)
                if val:
                    logger.debug(f"Cache HIT (Redis): {key}")
                    return json.loads(val)
            else:
                val = self._memory.get(key)
                if val:
                    logger.debug(f"Cache HIT (memory): {key}")
                    return val
        except Exception as e:
            logger.error(f"Cache get error: {e}")
        return None

    async def set(self, key: str, value: Dict, ttl: int = 3600):
        try:
            if self._using_redis:
                self._redis.setex(key, ttl, json.dumps(value))
            else:
                self._memory.set(key, value, ttl)
            logger.debug(f"Cache SET: {key} (TTL={ttl}s)")
        except Exception as e:
            logger.error(f"Cache set error: {e}")

    async def delete(self, key: str):
        try:
            if self._using_redis:
                self._redis.delete(key)
            else:
                self._memory.delete(key)
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
