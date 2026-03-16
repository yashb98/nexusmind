"""Graph service — network queries, recommendations, relationship management."""

import structlog

from src.db import neo4j_client

logger = structlog.get_logger(__name__)


async def get_agent_network(agent_id: str, tenant_id: str, hops: int = 2) -> dict:
    """Get agent's network (nodes + edges) for D3.js visualization.

    Uses undirected KNOWS traversal and doesn't filter connected nodes by
    tenant_id so that mock agents (which live in a different tenant) are
    included in the graph.
    """
    records = await neo4j_client.execute_read(
        """MATCH (a:Agent {id: $id})
           OPTIONAL MATCH (a)-[r:KNOWS]-(b:Agent)
           WHERE b IS NOT NULL
           WITH a,
                COLLECT(DISTINCT {
                    id: b.id,
                    display_name: b.display_name,
                    interests: b.interests,
                    openness: b.openness,
                    extraversion: b.extraversion,
                    lora_archetype: b.lora_archetype,
                    communication_style: b.communication_style,
                    is_mock: COALESCE(b.is_mock, false)
                }) AS neighbors,
                [x IN COLLECT(DISTINCT
                    CASE WHEN r IS NOT NULL THEN {
                        source: startNode(r).id,
                        target: endNode(r).id,
                        strength: r.strength,
                        trust: r.trust,
                        conversation_count: r.conversation_count
                    } END
                ) WHERE x IS NOT NULL] AS edges
           RETURN [n IN neighbors WHERE n.id IS NOT NULL] + [{
               id: a.id,
               display_name: a.display_name,
               interests: a.interests,
               openness: a.openness,
               extraversion: a.extraversion,
               lora_archetype: a.lora_archetype,
               communication_style: a.communication_style,
               is_mock: COALESCE(a.is_mock, false)
           }] AS nodes, edges""",
        id=agent_id,
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


async def get_communities(tenant_id: str) -> list[dict]:
    """Get all communities."""
    records = await neo4j_client.execute_read(
        """MATCH (c:Community)
           OPTIONAL MATCH (a:Agent)-[:MEMBER_OF]->(c)
           RETURN c.id AS id, c.name AS name, c.summary AS summary,
                  COUNT(a) AS member_count
           ORDER BY member_count DESC""",
    )
    return records


async def get_trending_topics(days: int = 7, limit: int = 10) -> list[dict]:
    """Get trending topics based on recent mention growth."""
    records = await neo4j_client.execute_read(
        """MATCH (t:Topic)
           RETURN t.id AS id, t.name AS name,
                  t.mention_count AS mentions,
                  t.growth_rate AS growth_rate
           ORDER BY t.mention_count DESC
           LIMIT $limit""",
        limit=limit,
    )
    return records


async def run_community_detection(tenant_id: str) -> dict:
    """Run simple community detection based on shared topics."""
    # Group agents by their most common shared interests
    records = await neo4j_client.execute_read(
        """MATCH (a:Agent {tenant_id: $tid})-[r:KNOWS]->(b:Agent)
           WITH a, b, r.topics_shared AS topics
           WHERE topics IS NOT NULL AND size(topics) > 0
           UNWIND topics AS topic
           WITH topic, COLLECT(DISTINCT a.id) + COLLECT(DISTINCT b.id) AS members
           WHERE size(members) >= 2
           RETURN topic AS name, members, size(members) AS size
           ORDER BY size DESC
           LIMIT 10""",
        tid=tenant_id,
    )

    communities_created = 0
    for rec in records:
        import uuid

        comm_id = str(uuid.uuid4())
        await neo4j_client.execute_write(
            """MERGE (c:Community {name: $name})
               ON CREATE SET c.id = $id, c.summary = $summary,
                             c.member_count = $size, c.formed_at = datetime()
               ON MATCH SET c.member_count = $size""",
            id=comm_id,
            name=rec["name"],
            summary=f"Community around {rec['name']}",
            size=rec["size"],
        )

        for member_id in rec.get("members", []):
            await neo4j_client.execute_write(
                """MATCH (a:Agent {id: $aid}), (c:Community {name: $cname})
                   MERGE (a)-[:MEMBER_OF]->(c)""",
                aid=member_id,
                cname=rec["name"],
            )
        communities_created += 1

    logger.info("community_detection_complete", communities=communities_created)
    return {"communities_created": communities_created}


async def update_trust(agent_a_id: str, agent_b_id: str, trust_delta: float) -> None:
    """Update trust on KNOWS edge. Clamp to 0-1. Append to trust_history."""
    await neo4j_client.execute_write(
        """MATCH (a:Agent {id: $aid})-[r:KNOWS]-(b:Agent {id: $bid})
        SET r.trust = CASE
            WHEN r.trust + $delta > 1.0 THEN 1.0
            WHEN r.trust + $delta < 0.0 THEN 0.0
            ELSE r.trust + $delta
        END,
        r.trust_history = r.trust_history[-9..] + [r.trust + $delta]""",
        aid=agent_a_id,
        bid=agent_b_id,
        delta=trust_delta,
    )


async def multi_hop_query(start_entity: str, max_hops: int = 3) -> list[dict]:
    """Traverse typed relations from an entity."""
    records = await neo4j_client.execute_read(
        """MATCH path = (e:Entity {name: $name})-[*1.."""
        + str(min(max_hops, 5))
        + """]->(target:Entity)
           RETURN [n IN nodes(path) | n.name] AS path_names,
                  [r IN relationships(path) | type(r)] AS rel_types,
                  length(path) AS hops
           LIMIT 20""",
        name=start_entity,
    )
    return records
