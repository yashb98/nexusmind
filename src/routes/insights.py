"""Insights routes — agent discoveries and knowledge feed."""

from fastapi import APIRouter, Depends

from src.db import neo4j_client
from src.utils.auth import get_current_user

router = APIRouter(prefix="/api/v1/agents", tags=["insights"])


@router.get("/{agent_id}/insights")
async def get_insights(
    agent_id: str,
    limit: int = 20,
    current_user: dict = Depends(get_current_user),
) -> list[dict]:
    """Get insight feed for an agent (sorted by recency)."""
    records = await neo4j_client.execute_read(
        """MATCH (a:Agent {id: $aid})-[:PARTICIPATED_IN]->(c:Conversation)-[:PRODUCED]->(i:Insight)
           RETURN i.id AS id, i.content AS content,
                  i.importance AS importance,
                  i.verification_status AS status,
                  i.discovered_at AS discovered_at
           ORDER BY i.discovered_at DESC
           LIMIT $limit""",
        aid=agent_id,
        limit=limit,
    )
    return records


@router.get("/{agent_id}/discoveries")
async def get_discoveries(
    agent_id: str,
    limit: int = 20,
    current_user: dict = Depends(get_current_user),
) -> list[dict]:
    """Get knowledge discovered by an agent's conversations."""
    records = await neo4j_client.execute_read(
        """MATCH (a:Agent {id: $aid})-[:PARTICIPATED_IN]->(c:Conversation)
           OPTIONAL MATCH (c)-[:PRODUCED]->(i:Insight)
           RETURN c.id AS conversation_id,
                  c.summary AS summary,
                  c.quality_score AS quality_score,
                  c.turn_count AS turn_count,
                  COLLECT(i.content) AS insights
           ORDER BY c.started_at DESC
           LIMIT $limit""",
        aid=agent_id,
        limit=limit,
    )
    return records
