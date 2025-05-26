import redis.asyncio as aioredis # Import the asyncio version of the redis library
from redis.asyncio.connection import ConnectionPool # Correct import for ConnectionPool
import json
from typing import Optional, Any
from app.config import settings

class RedisCache:
    def __init__(self):
        self.redis_url = f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}"
        if settings.REDIS_PASSWORD:
            self.redis_url = f"redis://:{settings.REDIS_PASSWORD}@{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}"
        
        # Create a connection pool. This is more efficient than creating connections on the fly.
        # Note: aioredis.from_url automatically manages a connection pool.
        self.pool = ConnectionPool.from_url(self.redis_url, decode_responses=True) # decode_responses for auto-decoding from bytes to str

    async def get_client(self):
        # Get a client from the pool
        return aioredis.Redis(connection_pool=self.pool)

    async def get(self, key: str) -> Optional[Any]:
        try:
            client = await self.get_client()
            cached_value = await client.get(key)
            if cached_value:
                return json.loads(cached_value) # Assuming JSON serializable data
            return None
        except Exception as e:
            print(f"Redis get error: {e}") # Basic logging, consider more robust logging
            return None

    async def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None):
        try:
            client = await self.get_client()
            serialized_value = json.dumps(value) # Assuming JSON serializable data
            if ttl_seconds is None:
                ttl_seconds = settings.REDIS_CACHE_TTL_SECONDS
            await client.set(key, serialized_value, ex=ttl_seconds)
        except Exception as e:
            print(f"Redis set error: {e}") # Basic logging

    async def delete(self, key: str):
        try:
            client = await self.get_client()
            await client.delete(key)
        except Exception as e:
            print(f"Redis delete error: {e}")

    async def clear_cache_by_prefix(self, prefix: str):
        try:
            client = await self.get_client()
            keys = []
            async for key in client.scan_iter(match=f"{prefix}:*"):
                keys.append(key)
            if keys:
                await client.delete(*keys)
            print(f"Cleared {len(keys)} keys with prefix '{prefix}'")
        except Exception as e:
            print(f"Redis clear_cache_by_prefix error: {e}")

# Global instance of the cache client
redis_cache_client = RedisCache()

# Optional: function to be called on app startup/shutdown to explicitly manage pool (if needed)
# async def connect_redis_pool():
#    # aioredis.from_url manages the pool implicitly, explicit connect/disconnect often not needed for basic use.
#    # If more control is needed, this is where you'd initialize and close the pool.
#    pass

# async def close_redis_pool():
#    if redis_cache_client.pool:
#        await redis_cache_client.pool.disconnect() # Or appropriate close method for the pool
#    pass
