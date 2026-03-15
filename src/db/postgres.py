"""Async PostgreSQL client using asyncpg."""

import asyncpg
import structlog

from src.config import settings

logger = structlog.get_logger(__name__)

_pool: asyncpg.Pool | None = None


async def get_pool() -> asyncpg.Pool:
    """Get the connection pool, creating it if needed."""
    global _pool
    if _pool is None:
        raise RuntimeError("PostgreSQL pool not initialized. Call connect() first.")
    return _pool


async def connect() -> None:
    """Initialize the connection pool."""
    global _pool
    _pool = await asyncpg.create_pool(
        dsn=settings.database.database_url,
        min_size=2,
        max_size=10,
    )
    logger.info("postgres_connected", dsn=settings.database.database_url.split("@")[-1])


async def disconnect() -> None:
    """Close the connection pool."""
    global _pool
    if _pool:
        await _pool.close()
        _pool = None
        logger.info("postgres_disconnected")


async def execute(query: str, *args: object) -> str:
    """Execute a query and return status."""
    pool = await get_pool()
    return await pool.execute(query, *args)


async def fetch(query: str, *args: object) -> list[asyncpg.Record]:
    """Execute a query and return all rows."""
    pool = await get_pool()
    return await pool.fetch(query, *args)


async def fetchrow(query: str, *args: object) -> asyncpg.Record | None:
    """Execute a query and return one row."""
    pool = await get_pool()
    return await pool.fetchrow(query, *args)


async def fetchval(query: str, *args: object) -> object:
    """Execute a query and return a single value."""
    pool = await get_pool()
    return await pool.fetchval(query, *args)
