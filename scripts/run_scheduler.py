"""Start the always-on background agent scheduler."""

import asyncio

from src.db import neo4j_client, postgres, qdrant_client, redis_client
from src.services.scheduler import scheduler
from src.utils.logging import setup_logging


async def main() -> None:
    setup_logging()

    await asyncio.gather(
        postgres.connect(),
        neo4j_client.connect(),
        qdrant_client.connect(),
        redis_client.connect(),
    )

    try:
        await scheduler.run_forever()
    finally:
        await asyncio.gather(
            postgres.disconnect(),
            neo4j_client.disconnect(),
            qdrant_client.disconnect(),
            redis_client.disconnect(),
        )


if __name__ == "__main__":
    asyncio.run(main())
