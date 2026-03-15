"""Neo4j async driver and constraint management."""

import structlog
from neo4j import AsyncDriver, AsyncGraphDatabase

from src.config import settings

logger = structlog.get_logger(__name__)

_driver: AsyncDriver | None = None

CONSTRAINTS = [
    "CREATE CONSTRAINT agent_unique IF NOT EXISTS FOR (a:Agent) REQUIRE a.id IS UNIQUE",
    "CREATE CONSTRAINT topic_unique IF NOT EXISTS FOR (t:Topic) REQUIRE t.id IS UNIQUE",
    "CREATE CONSTRAINT community_unique IF NOT EXISTS FOR (c:Community) REQUIRE c.id IS UNIQUE",
    "CREATE CONSTRAINT insight_unique IF NOT EXISTS FOR (i:Insight) REQUIRE i.id IS UNIQUE",
    "CREATE CONSTRAINT entity_unique IF NOT EXISTS FOR (e:Entity) REQUIRE e.id IS UNIQUE",
]


async def get_driver() -> AsyncDriver:
    """Get the Neo4j driver."""
    global _driver
    if _driver is None:
        raise RuntimeError("Neo4j driver not initialized. Call connect() first.")
    return _driver


async def connect() -> None:
    """Initialize the Neo4j driver and create constraints."""
    global _driver
    _driver = AsyncGraphDatabase.driver(
        settings.neo4j.uri,
        auth=(settings.neo4j.user, settings.neo4j.password),
    )
    await _driver.verify_connectivity()
    logger.info("neo4j_connected", uri=settings.neo4j.uri)

    async with _driver.session() as session:
        for constraint in CONSTRAINTS:
            await session.run(constraint)
    logger.info("neo4j_constraints_created", count=len(CONSTRAINTS))


async def disconnect() -> None:
    """Close the Neo4j driver."""
    global _driver
    if _driver:
        await _driver.close()
        _driver = None
        logger.info("neo4j_disconnected")


async def execute_read(query: str, **params: object) -> list[dict]:
    """Run a read transaction."""
    driver = await get_driver()
    async with driver.session() as session:
        result = await session.run(query, params)
        return [record.data() async for record in result]


async def execute_write(query: str, **params: object) -> list[dict]:
    """Run a write transaction."""
    driver = await get_driver()
    async with driver.session() as session:
        result = await session.run(query, params)
        return [record.data() async for record in result]
