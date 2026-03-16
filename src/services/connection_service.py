"""Connection management service with Postgres + Neo4j + Redis."""

import uuid

import structlog

from src.db import neo4j_client, postgres, redis_client
from src.models.connection import ConnectionInfo, ConnectionResponse

logger = structlog.get_logger(__name__)

_INVITE_TTL_SECONDS = 7 * 24 * 60 * 60  # 7 days


def _row_to_response(row: dict) -> ConnectionResponse:
    """Convert a database row to ConnectionResponse."""
    return ConnectionResponse(
        id=str(row["id"]),
        from_agent_id=str(row["from_agent_id"]),
        to_agent_id=str(row["to_agent_id"]),
        message=row.get("message"),
        status=row["status"],
        created_at=str(row["created_at"]),
        responded_at=str(row["responded_at"]) if row.get("responded_at") else None,
    )


async def generate_invite_link(agent_id: str, tenant_id: str) -> str:
    """Generate a UUID-based invite token, store in Redis with 7-day TTL.

    Args:
        agent_id: The agent generating the invite.
        tenant_id: Tenant scope.

    Returns:
        The invite link containing the token.
    """
    token = str(uuid.uuid4())
    redis = await redis_client.get_client()
    await redis.set(
        f"invite:{token}",
        f"{agent_id}:{tenant_id}",
        ex=_INVITE_TTL_SECONDS,
    )
    logger.info("invite_link_generated", agent_id=agent_id, token=token)
    return f"/api/v1/connections/invite/{token}"


async def send_request(
    from_agent_id: str, to_agent_id: str, message: str | None, tenant_id: str
) -> ConnectionResponse:
    """Insert a connection request into the connection_requests table.

    Args:
        from_agent_id: Sender agent ID.
        to_agent_id: Recipient agent ID.
        message: Optional message.
        tenant_id: Tenant scope.

    Returns:
        The created connection request.
    """
    request_id = uuid.uuid4()
    row = await postgres.fetchrow(
        """INSERT INTO connection_requests
           (id, from_agent_id, to_agent_id, message, status)
           VALUES ($1, $2, $3, $4, 'pending')
           RETURNING *""",
        request_id,
        uuid.UUID(from_agent_id),
        uuid.UUID(to_agent_id),
        message,
    )
    logger.info(
        "connection_request_sent",
        request_id=str(request_id),
        from_agent_id=from_agent_id,
        to_agent_id=to_agent_id,
    )
    return _row_to_response(row)


async def list_pending_requests(agent_id: str, tenant_id: str) -> list[ConnectionResponse]:
    """Fetch pending incoming connection requests for an agent.

    Args:
        agent_id: The agent receiving requests.
        tenant_id: Tenant scope.

    Returns:
        List of pending connection requests.
    """
    rows = await postgres.fetch(
        """SELECT * FROM connection_requests
           WHERE to_agent_id = $1 AND tenant_id = $2 AND status = 'pending'
           ORDER BY created_at DESC""",
        uuid.UUID(agent_id),
        uuid.UUID(tenant_id),
    )
    return [_row_to_response(r) for r in rows]


async def respond_to_request(
    request_id: str, accept: bool, tenant_id: str
) -> ConnectionResponse:
    """Accept or reject a connection request.

    If accepted, creates a KNOWS edge in Neo4j with trust=0.2.

    Args:
        request_id: The connection request ID.
        accept: Whether to accept or reject.
        tenant_id: Tenant scope.

    Returns:
        The updated connection request.
    """
    new_status = "accepted" if accept else "rejected"
    row = await postgres.fetchrow(
        """UPDATE connection_requests
           SET status = $1, responded_at = NOW()
           WHERE id = $2 AND tenant_id = $3
           RETURNING *""",
        new_status,
        uuid.UUID(request_id),
        uuid.UUID(tenant_id),
    )
    if not row:
        raise ValueError(f"Connection request {request_id} not found")

    if accept:
        await neo4j_client.execute_write(
            """MATCH (a:Agent {id: $from_id}), (b:Agent {id: $to_id})
               MERGE (a)-[r:KNOWS]->(b)
               SET r.trust = 0.2, r.since = datetime()
               MERGE (b)-[r2:KNOWS]->(a)
               SET r2.trust = 0.2, r2.since = datetime()""",
            from_id=str(row["from_agent_id"]),
            to_id=str(row["to_agent_id"]),
        )
        logger.info(
            "connection_accepted",
            request_id=request_id,
            from_agent_id=str(row["from_agent_id"]),
            to_agent_id=str(row["to_agent_id"]),
        )
    else:
        logger.info("connection_rejected", request_id=request_id)

    return _row_to_response(row)


async def list_connections(agent_id: str, tenant_id: str) -> list[ConnectionInfo]:
    """Query Neo4j for all KNOWS edges of an agent.

    Args:
        agent_id: The agent to list connections for.
        tenant_id: Tenant scope.

    Returns:
        List of connections with trust info.
    """
    records = await neo4j_client.execute_read(
        """MATCH (a:Agent {id: $agent_id, tenant_id: $tenant_id})-[r:KNOWS]->(b:Agent)
           RETURN b.id AS agent_id,
                  b.display_name AS display_name,
                  r.trust AS trust,
                  COALESCE(r.conversation_count, 0) AS conversation_count,
                  COALESCE(r.topics_shared, []) AS topics_shared,
                  COALESCE(b.is_mock, false) AS is_mock""",
        agent_id=agent_id,
        tenant_id=tenant_id,
    )
    return [
        ConnectionInfo(
            agent_id=rec["agent_id"],
            display_name=rec["display_name"],
            trust=rec["trust"],
            conversation_count=rec["conversation_count"],
            topics_shared=rec["topics_shared"],
            is_mock=rec["is_mock"],
        )
        for rec in records
    ]
