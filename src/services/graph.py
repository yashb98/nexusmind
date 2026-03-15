"""Graph service — network queries, recommendations, relationship management."""

import structlog

from src.db import neo4j_client

logger = structlog.get_logger(__name__)


async def get_agent_network(agent_id: str, tenant_id: str, hops: int = 2) -> dict:
    """Get agent's network (nodes + edges) for D3.js visualization."""
    records = await neo4j_client.execute_read(
        """MATCH path = (a:Agent {id: $id, tenant_id: $tid})-[:KNOWS*1.."""
        + str(min(hops, 3))
        + """]->(b:Agent {tenant_id: $tid})
           UNWIND nodes(path) AS n
           UNWIND relationships(path) AS r
           WITH COLLECT(DISTINCT {
               id: n.id,
               display_name: n.display_name,
               interests: n.interests,
               openness: n.openness,
               extraversion: n.extraversion
           }) AS nodes,
           COLLECT(DISTINCT {
               source: startNode(r).id,
               target: endNode(r).id,
               strength: r.strength,
               conversation_count: r.conversation_count
           }) AS edges
           RETURN nodes, edges""",
        id=agent_id,
        tid=tenant_id,
    )

    if not records:
        return {"nodes": [], "edges": []}
    return {"nodes": records[0].get("nodes", []), "edges": records[0].get("edges", [])}


async def find_similar_agents(agent_id: str, tenant_id: str, limit: int = 5) -> list[dict]:
    """Find agents with similar interests (Jaccard overlap)."""
    records = await neo4j_client.execute_read(
        """MATCH (a:Agent {id: $id, tenant_id: $tid})
           MATCH (b:Agent {tenant_id: $tid})
           WHERE a <> b
           WITH a, b,
                [x IN a.interests WHERE x IN b.interests] AS shared,
                a.interests + [x IN b.interests WHERE NOT x IN a.interests] AS combined
           WHERE size(shared) > 0
           RETURN b.id AS id, b.display_name AS display_name,
                  b.interests AS interests,
                  toFloat(size(shared)) / size(combined) AS similarity
           ORDER BY similarity DESC
           LIMIT $limit""",
        id=agent_id,
        tid=tenant_id,
        limit=limit,
    )
    return records


async def get_recommendations(agent_id: str, tenant_id: str, limit: int = 5) -> list[dict]:
    """Get agents who share interests but haven't connected yet."""
    records = await neo4j_client.execute_read(
        """MATCH (a:Agent {id: $id, tenant_id: $tid})
           MATCH (b:Agent {tenant_id: $tid})
           WHERE a <> b
             AND NOT (a)-[:KNOWS]->(b)
           WITH a, b,
                [x IN a.interests WHERE x IN b.interests] AS shared
           WHERE size(shared) > 0
           RETURN b.id AS id, b.display_name AS display_name,
                  b.interests AS interests, shared,
                  size(shared) AS shared_count
           ORDER BY shared_count DESC
           LIMIT $limit""",
        id=agent_id,
        tid=tenant_id,
        limit=limit,
    )
    return records


async def upsert_relationship(
    agent_a_id: str,
    agent_b_id: str,
    strength_delta: float = 0.1,
    topics: list[str] | None = None,
) -> None:
    """Create or update KNOWS relationship between two agents."""
    await neo4j_client.execute_write(
        """MATCH (a:Agent {id: $a_id}), (b:Agent {id: $b_id})
           MERGE (a)-[r:KNOWS]->(b)
           ON CREATE SET r.strength = $delta,
                         r.trust = 0.5,
                         r.conversation_count = 1,
                         r.topics_shared = $topics,
                         r.last_interaction = datetime()
           ON MATCH SET r.strength = CASE
                            WHEN r.strength + $delta > 1.0 THEN 1.0
                            ELSE r.strength + $delta END,
                        r.conversation_count = r.conversation_count + 1,
                        r.topics_shared = CASE
                            WHEN $topics IS NOT NULL
                            THEN r.topics_shared + $topics
                            ELSE r.topics_shared END,
                        r.last_interaction = datetime()""",
        a_id=agent_a_id,
        b_id=agent_b_id,
        delta=strength_delta,
        topics=topics or [],
    )
    logger.info("relationship_upserted", a=agent_a_id, b=agent_b_id)


async def get_relationship(agent_a_id: str, agent_b_id: str) -> dict | None:
    """Get the KNOWS relationship between two agents."""
    records = await neo4j_client.execute_read(
        """MATCH (a:Agent {id: $a_id})-[r:KNOWS]->(b:Agent {id: $b_id})
           RETURN r.strength AS strength, r.trust AS trust,
                  r.conversation_count AS conversation_count,
                  r.topics_shared AS topics_shared""",
        a_id=agent_a_id,
        b_id=agent_b_id,
    )
    return records[0] if records else None
