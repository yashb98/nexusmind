"""Redis async client for session state and caching."""

import structlog
from redis.asyncio import Redis, from_url

from src.config import settings

logger = structlog.get_logger(__name__)

_client: Redis | None = None


async def get_client() -> Redis:
    """Get the Redis client."""
    global _client
    if _client is None:
        raise RuntimeError("Redis client not initialized. Call connect() first.")
    return _client


async def connect() -> None:
    """Initialize the Redis connection."""
    global _client
    _client = from_url(settings.redis.redis_url, decode_responses=True)
    await _client.ping()
    logger.info("redis_connected", url=settings.redis.redis_url)


async def disconnect() -> None:
    """Close the Redis connection."""
    global _client
    if _client:
        await _client.close()
        _client = None
        logger.info("redis_disconnected")
