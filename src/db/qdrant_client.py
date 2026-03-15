"""Qdrant vector database client with 3-tier memory collections."""

import structlog
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import Distance, PayloadSchemaType, VectorParams

from src.config import settings

logger = structlog.get_logger(__name__)

_client: AsyncQdrantClient | None = None

COLLECTIONS = {
    "agent_memories_hot": {
        "vector_size": 768,
        "payload_schema": {
            "agent_id": PayloadSchemaType.KEYWORD,
            "tenant_id": PayloadSchemaType.KEYWORD,
            "memory_type": PayloadSchemaType.KEYWORD,
            "privacy_level_required": PayloadSchemaType.INTEGER,
            "importance": PayloadSchemaType.FLOAT,
            "verification_status": PayloadSchemaType.KEYWORD,
        },
    },
    "knowledge_base": {
        "vector_size": 768,
        "payload_schema": {
            "tenant_id": PayloadSchemaType.KEYWORD,
            "source": PayloadSchemaType.KEYWORD,
            "topic": PayloadSchemaType.KEYWORD,
            "bloom_level": PayloadSchemaType.INTEGER,
        },
    },
    "agent_memories_cold": {
        "vector_size": 768,
        "payload_schema": {
            "agent_id": PayloadSchemaType.KEYWORD,
            "tenant_id": PayloadSchemaType.KEYWORD,
            "importance": PayloadSchemaType.FLOAT,
        },
    },
}


async def get_client() -> AsyncQdrantClient:
    """Get the Qdrant client."""
    global _client
    if _client is None:
        raise RuntimeError("Qdrant client not initialized. Call connect() first.")
    return _client


async def connect() -> None:
    """Initialize client and create collections."""
    global _client
    _client = AsyncQdrantClient(
        url=settings.qdrant.url,
        api_key=settings.qdrant.api_key or None,
    )

    for name, config in COLLECTIONS.items():
        exists = await _client.collection_exists(name)
        if not exists:
            await _client.create_collection(
                collection_name=name,
                vectors_config=VectorParams(
                    size=config["vector_size"],
                    distance=Distance.COSINE,
                ),
            )
            for field_name, field_type in config["payload_schema"].items():
                await _client.create_payload_index(
                    collection_name=name,
                    field_name=field_name,
                    field_schema=field_type,
                )
            logger.info("qdrant_collection_created", name=name)
        else:
            logger.info("qdrant_collection_exists", name=name)

    logger.info("qdrant_connected", url=settings.qdrant.url)


async def disconnect() -> None:
    """Close the Qdrant client."""
    global _client
    if _client:
        await _client.close()
        _client = None
        logger.info("qdrant_disconnected")
