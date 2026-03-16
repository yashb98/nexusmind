"""Event service — CRUD, participation, lifecycle management."""

import uuid

import structlog

from src.db import postgres

logger = structlog.get_logger(__name__)


async def create_event(data: dict, user_id: str, tenant_id: str) -> dict:
    """Create a new event in the tenant."""
    row = await postgres.fetchrow(
        """INSERT INTO events (tenant_id, title, description, event_type,
                               created_by, group_id, scheduled_at, max_participants)
           VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
           RETURNING *""",
        uuid.UUID(tenant_id),
        data["title"],
        data.get("description"),
        data.get("event_type", "debate"),
        uuid.UUID(user_id),
        uuid.UUID(data["group_id"]) if data.get("group_id") else None,
        data.get("scheduled_at"),
        data.get("max_participants", 10),
    )
    return _row_to_dict(row)


async def list_events(
    tenant_id: str, status: str | None = None, limit: int = 20
) -> list[dict]:
    """List events with optional status filter and participant counts."""
    if status:
        rows = await postgres.fetch(
            """SELECT e.*, COUNT(ep.id) AS participant_count
               FROM events e
               LEFT JOIN event_participants ep ON e.id = ep.event_id
               WHERE e.tenant_id = $1 AND e.status = $2
               GROUP BY e.id
               ORDER BY e.scheduled_at DESC NULLS LAST
               LIMIT $3""",
            uuid.UUID(tenant_id),
            status,
            limit,
        )
    else:
        rows = await postgres.fetch(
            """SELECT e.*, COUNT(ep.id) AS participant_count
               FROM events e
               LEFT JOIN event_participants ep ON e.id = ep.event_id
               WHERE e.tenant_id = $1
               GROUP BY e.id
               ORDER BY e.scheduled_at DESC NULLS LAST
               LIMIT $2""",
            uuid.UUID(tenant_id),
            limit,
        )
    return [_row_to_dict(r) for r in rows]


async def get_event(event_id: str) -> dict | None:
    """Get a single event by ID with participant count."""
    row = await postgres.fetchrow(
        """SELECT e.*, COUNT(ep.id) AS participant_count
           FROM events e
           LEFT JOIN event_participants ep ON e.id = ep.event_id
           WHERE e.id = $1
           GROUP BY e.id""",
        uuid.UUID(event_id),
    )
    return _row_to_dict(row) if row else None


async def join_event(event_id: str, agent_id: str) -> None:
    """Register an agent as a participant in an event."""
    await postgres.execute(
        """INSERT INTO event_participants (event_id, agent_id)
           VALUES ($1, $2)
           ON CONFLICT (event_id, agent_id) DO NOTHING""",
        uuid.UUID(event_id),
        uuid.UUID(agent_id),
    )
    logger.info("event_joined", event_id=event_id, agent_id=agent_id)


async def start_event(event_id: str) -> dict | None:
    """Transition event status to live."""
    row = await postgres.fetchrow(
        """UPDATE events SET status = 'live', started_at = NOW(), updated_at = NOW()
           WHERE id = $1 AND status = 'scheduled'
           RETURNING *""",
        uuid.UUID(event_id),
    )
    if not row:
        return None
    logger.info("event_started", event_id=event_id)
    return _row_to_dict(row)


async def complete_event(event_id: str, results: dict | None = None) -> dict | None:
    """Transition event status to completed and store results."""
    row = await postgres.fetchrow(
        """UPDATE events SET status = 'completed', results = $2,
                             completed_at = NOW(), updated_at = NOW()
           WHERE id = $1 AND status = 'live'
           RETURNING *""",
        uuid.UUID(event_id),
        results,
    )
    if not row:
        return None
    logger.info("event_completed", event_id=event_id)
    return _row_to_dict(row)


async def get_results(event_id: str) -> dict | None:
    """Get event results."""
    row = await postgres.fetchrow(
        "SELECT id, results, status FROM events WHERE id = $1",
        uuid.UUID(event_id),
    )
    if not row:
        return None
    return {
        "id": str(row["id"]),
        "status": row["status"],
        "results": row.get("results"),
    }


def _row_to_dict(row) -> dict:
    """Convert a database row to a serializable dict."""
    return {
        "id": str(row["id"]),
        "title": row["title"],
        "description": row.get("description"),
        "event_type": row.get("event_type", "debate"),
        "status": row.get("status", "scheduled"),
        "created_by": str(row["created_by"]),
        "group_id": str(row["group_id"]) if row.get("group_id") else None,
        "scheduled_at": row["scheduled_at"].isoformat() if row.get("scheduled_at") else None,
        "max_participants": row.get("max_participants", 10),
        "participant_count": row.get("participant_count", 0),
        "results": row.get("results"),
        "created_at": row["created_at"].isoformat(),
    }
