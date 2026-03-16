"""Group service — CRUD, membership, group conversations."""

import uuid

import structlog

from src.db import postgres

logger = structlog.get_logger(__name__)


async def create_group(data: dict, user_id: str, tenant_id: str) -> dict:
    """Create a new group in the tenant."""
    row = await postgres.fetchrow(
        """INSERT INTO groups (tenant_id, name, description, group_type,
                               created_by, max_members, is_public)
           VALUES ($1, $2, $3, $4, $5, $6, $7)
           RETURNING *""",
        uuid.UUID(tenant_id),
        data["name"],
        data.get("description"),
        data.get("group_type", "interest"),
        uuid.UUID(user_id),
        data.get("max_members", 20),
        data.get("is_public", True),
    )
    return _row_to_dict(row)


async def list_groups(user_id: str, tenant_id: str) -> list[dict]:
    """List all groups in the tenant with member counts."""
    rows = await postgres.fetch(
        """SELECT g.*, COUNT(gm.id) AS member_count
           FROM groups g
           LEFT JOIN group_members gm ON g.id = gm.group_id
           WHERE g.tenant_id = $1
           GROUP BY g.id
           ORDER BY g.created_at DESC""",
        uuid.UUID(tenant_id),
    )
    return [_row_to_dict(r) for r in rows]


async def get_group(group_id: str) -> dict | None:
    """Get a single group by ID with member count."""
    row = await postgres.fetchrow(
        """SELECT g.*, COUNT(gm.id) AS member_count
           FROM groups g
           LEFT JOIN group_members gm ON g.id = gm.group_id
           WHERE g.id = $1
           GROUP BY g.id""",
        uuid.UUID(group_id),
    )
    return _row_to_dict(row) if row else None


async def update_group(group_id: str, data: dict) -> dict | None:
    """Update mutable group fields."""
    updates = {k: v for k, v in data.items() if v is not None}
    if not updates:
        return await get_group(group_id)

    set_clauses = []
    params: list[object] = [uuid.UUID(group_id)]
    idx = 2

    for field, value in updates.items():
        set_clauses.append(f"{field} = ${idx}")
        params.append(value)
        idx += 1

    set_clauses.append("updated_at = NOW()")
    query = f"UPDATE groups SET {', '.join(set_clauses)} WHERE id = $1 RETURNING *"

    row = await postgres.fetchrow(query, *params)
    if not row:
        return None

    logger.info("group_updated", group_id=group_id)
    return _row_to_dict(row)


async def delete_group(group_id: str) -> bool:
    """Delete a group and its memberships."""
    result = await postgres.execute(
        "DELETE FROM groups WHERE id = $1",
        uuid.UUID(group_id),
    )
    if result == "DELETE 1":
        logger.info("group_deleted", group_id=group_id)
        return True
    return False


async def join_group(group_id: str, agent_id: str) -> None:
    """Add an agent as a member of a group."""
    await postgres.execute(
        """INSERT INTO group_members (group_id, agent_id, role)
           VALUES ($1, $2, 'member')
           ON CONFLICT (group_id, agent_id) DO NOTHING""",
        uuid.UUID(group_id),
        uuid.UUID(agent_id),
    )
    logger.info("group_joined", group_id=group_id, agent_id=agent_id)


async def leave_group(group_id: str, agent_id: str) -> None:
    """Remove an agent from a group."""
    await postgres.execute(
        "DELETE FROM group_members WHERE group_id = $1 AND agent_id = $2",
        uuid.UUID(group_id),
        uuid.UUID(agent_id),
    )
    logger.info("group_left", group_id=group_id, agent_id=agent_id)


async def get_members(group_id: str) -> list[dict]:
    """Get all members of a group with agent details."""
    rows = await postgres.fetch(
        """SELECT a.id, a.display_name, a.lora_archetype, a.interests,
                  gm.role, gm.joined_at
           FROM group_members gm
           JOIN agents a ON a.id = gm.agent_id
           WHERE gm.group_id = $1
           ORDER BY gm.joined_at""",
        uuid.UUID(group_id),
    )
    return [
        {
            "id": str(r["id"]),
            "display_name": r["display_name"],
            "archetype": r["lora_archetype"],
            "interests": r["interests"],
            "role": r["role"],
            "joined_at": r["joined_at"].isoformat(),
        }
        for r in rows
    ]


async def discover_groups(tenant_id: str, limit: int = 10) -> list[dict]:
    """Discover public groups ordered by popularity."""
    rows = await postgres.fetch(
        """SELECT g.*, COUNT(gm.id) AS member_count
           FROM groups g
           LEFT JOIN group_members gm ON g.id = gm.group_id
           WHERE g.tenant_id = $1 AND g.is_public = true
           GROUP BY g.id
           ORDER BY member_count DESC
           LIMIT $2""",
        uuid.UUID(tenant_id),
        limit,
    )
    return [_row_to_dict(r) for r in rows]


def _row_to_dict(row) -> dict:
    """Convert a database row to a serializable dict."""
    return {
        "id": str(row["id"]),
        "name": row["name"],
        "description": row.get("description"),
        "group_type": row.get("group_type", "interest"),
        "created_by": str(row["created_by"]),
        "max_members": row.get("max_members", 20),
        "is_public": row.get("is_public", True),
        "member_count": row.get("member_count", 0),
        "created_at": row["created_at"].isoformat(),
    }
