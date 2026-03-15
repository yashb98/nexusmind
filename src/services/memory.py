"""Memory service — hot tier Qdrant storage and retrieval."""

import uuid
from datetime import UTC, datetime, timedelta

import structlog
from qdrant_client.models import FieldCondition, Filter, MatchValue, PointStruct

from src.db import qdrant_client as qdrant
from src.services import permission as permission_service

logger = structlog.get_logger(__name__)

COLLECTION = "agent_memories_hot"


async def store_memory(
    agent_id: str,
    tenant_id: str,
    content: str,
    embedding: list[float],
    memory_type: str = "conversation_insight",
    privacy_level: int = 1,
    importance: float = 0.5,
    source_conversation_id: str | None = None,
    verification_status: str = "unverified",
) -> str:
    """Store a memory vector in the hot tier."""
    client = await qdrant.get_client()
    point_id = str(uuid.uuid4())

    await client.upsert(
        collection_name=COLLECTION,
        points=[
            PointStruct(
                id=point_id,
                vector=embedding,
                payload={
                    "agent_id": agent_id,
                    "tenant_id": tenant_id,
                    "memory_type": memory_type,
                    "source_conversation_id": source_conversation_id or "",
                    "content": content,
                    "privacy_level_required": privacy_level,
                    "importance": importance,
                    "verification_status": verification_status,
                    "created_at": datetime.now(UTC).isoformat(),
                    "expires_at": (datetime.now(UTC) + timedelta(days=30)).isoformat(),
                },
            )
        ],
    )

    logger.info("memory_stored", agent_id=agent_id, type=memory_type, point_id=point_id)
    return point_id


async def retrieve_memories(
    agent_id: str,
    tenant_id: str,
    query_embedding: list[float],
    accessor_agent_id: str | None = None,
    limit: int = 5,
) -> list[dict]:
    """Retrieve permission-filtered memories via semantic search."""
    # Determine max accessible privacy level
    if accessor_agent_id and accessor_agent_id != agent_id:
        effective_level = await permission_service.get_effective_level(accessor_agent_id, agent_id)
    else:
        effective_level = 5  # Self-access = full access

    client = await qdrant.get_client()

    results = await client.query_points(
        collection_name=COLLECTION,
        query=query_embedding,
        query_filter=Filter(
            must=[
                FieldCondition(key="agent_id", match=MatchValue(value=agent_id)),
                FieldCondition(key="tenant_id", match=MatchValue(value=tenant_id)),
            ]
        ),
        limit=limit * 2,  # Over-fetch then filter by permission
    )

    memories = []
    for point in results.points:
        payload = point.payload or {}
        required = payload.get("privacy_level_required", 0)
        if required <= effective_level:
            memories.append(
                {
                    "id": str(point.id),
                    "content": payload.get("content", ""),
                    "memory_type": payload.get("memory_type", ""),
                    "importance": payload.get("importance", 0),
                    "score": point.score,
                }
            )
            if len(memories) >= limit:
                break

    return memories
