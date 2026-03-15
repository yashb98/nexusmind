"""Agent CRUD service with Postgres + Neo4j sync."""

import uuid

import structlog

from src.db import neo4j_client, postgres
from src.models.agent import AgentCreate, AgentResponse, AgentUpdate

logger = structlog.get_logger(__name__)


def _row_to_response(row: dict) -> AgentResponse:
    """Convert a database row to AgentResponse."""
    return AgentResponse(
        id=str(row["id"]),
        user_id=str(row["user_id"]),
        tenant_id=str(row["tenant_id"]),
        display_name=row["display_name"],
        openness=row["openness"],
        conscientiousness=row["conscientiousness"],
        extraversion=row["extraversion"],
        agreeableness=row["agreeableness"],
        neuroticism=row["neuroticism"],
        interests=row["interests"] or [],
        communication_style=row["communication_style"],
        lora_archetype=row.get("lora_archetype"),
        default_privacy_level=row["default_privacy_level"],
        avatar_image_url=row.get("avatar_image_url"),
        status=row["status"],
    )


async def create_agent(req: AgentCreate, user_id: str, tenant_id: str) -> AgentResponse:
    """Create an agent in Postgres and sync to Neo4j."""
    agent_id = uuid.uuid4()

    row = await postgres.fetchrow(
        """INSERT INTO agents
           (id, user_id, tenant_id, display_name,
            openness, conscientiousness, extraversion, agreeableness, neuroticism,
            interests, communication_style, lora_archetype,
            default_privacy_level, avatar_image_url)
           VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14)
           RETURNING *""",
        agent_id,
        uuid.UUID(user_id),
        uuid.UUID(tenant_id),
        req.display_name,
        req.openness,
        req.conscientiousness,
        req.extraversion,
        req.agreeableness,
        req.neuroticism,
        req.interests,
        req.communication_style,
        req.lora_archetype,
        req.default_privacy_level,
        req.avatar_image_url,
    )

    await _sync_agent_to_neo4j(row)
    logger.info("agent_created", agent_id=str(agent_id))
    return _row_to_response(row)


async def get_agent(agent_id: str, tenant_id: str) -> AgentResponse | None:
    """Get a single agent by ID (tenant-scoped)."""
    row = await postgres.fetchrow(
        "SELECT * FROM agents WHERE id = $1 AND tenant_id = $2",
        uuid.UUID(agent_id),
        uuid.UUID(tenant_id),
    )
    if not row:
        return None
    return _row_to_response(row)


async def list_agents(tenant_id: str) -> list[AgentResponse]:
    """List all agents in a tenant."""
    rows = await postgres.fetch(
        "SELECT * FROM agents WHERE tenant_id = $1 ORDER BY created_at",
        uuid.UUID(tenant_id),
    )
    return [_row_to_response(r) for r in rows]


async def update_agent(agent_id: str, tenant_id: str, req: AgentUpdate) -> AgentResponse | None:
    """Update an agent's mutable fields."""
    updates = req.model_dump(exclude_none=True)
    if not updates:
        return await get_agent(agent_id, tenant_id)

    set_clauses = []
    params: list[object] = []
    idx = 3  # $1=agent_id, $2=tenant_id

    for field, value in updates.items():
        set_clauses.append(f"{field} = ${idx}")
        params.append(value)
        idx += 1

    set_clauses.append("updated_at = NOW()")
    query = (
        f"UPDATE agents SET {', '.join(set_clauses)} WHERE id = $1 AND tenant_id = $2 RETURNING *"
    )

    row = await postgres.fetchrow(query, uuid.UUID(agent_id), uuid.UUID(tenant_id), *params)
    if not row:
        return None

    await _sync_agent_to_neo4j(row)
    logger.info("agent_updated", agent_id=agent_id)
    return _row_to_response(row)


async def delete_agent(agent_id: str, tenant_id: str) -> bool:
    """Delete an agent."""
    result = await postgres.execute(
        "DELETE FROM agents WHERE id = $1 AND tenant_id = $2",
        uuid.UUID(agent_id),
        uuid.UUID(tenant_id),
    )
    if result == "DELETE 1":
        await neo4j_client.execute_write("MATCH (a:Agent {id: $id}) DETACH DELETE a", id=agent_id)
        logger.info("agent_deleted", agent_id=agent_id)
        return True
    return False


async def _sync_agent_to_neo4j(row: dict) -> None:
    """Create or update Agent node in Neo4j."""
    await neo4j_client.execute_write(
        """MERGE (a:Agent {id: $id})
           SET a.tenant_id = $tenant_id,
               a.display_name = $display_name,
               a.interests = $interests,
               a.openness = $openness,
               a.extraversion = $extraversion""",
        id=str(row["id"]),
        tenant_id=str(row["tenant_id"]),
        display_name=row["display_name"],
        interests=row["interests"] or [],
        openness=row["openness"],
        extraversion=row["extraversion"],
    )
