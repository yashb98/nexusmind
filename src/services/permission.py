"""Permission service — set, check, audit."""

import uuid

import structlog

from src.db import neo4j_client, postgres
from src.services.personality import trust_derived_permission

logger = structlog.get_logger(__name__)


async def set_permission(agent_id: str, target_agent_id: str, level: int, tenant_id: str) -> None:
    """Set or update permission level for a specific agent pair."""
    await postgres.execute(
        """INSERT INTO permissions (agent_id, target_agent_id, level)
           VALUES ($1, $2, $3)
           ON CONFLICT (agent_id, target_agent_id)
           DO UPDATE SET level = $3""",
        uuid.UUID(agent_id),
        uuid.UUID(target_agent_id),
        level,
    )
    logger.info(
        "permission_set",
        agent_id=agent_id,
        target=target_agent_id,
        level=level,
    )


async def get_permissions(agent_id: str) -> list[dict]:
    """Get all permission overrides for an agent."""
    rows = await postgres.fetch(
        "SELECT * FROM permissions WHERE agent_id = $1",
        uuid.UUID(agent_id),
    )
    return [
        {
            "id": str(r["id"]),
            "agent_id": str(r["agent_id"]),
            "target_agent_id": str(r["target_agent_id"]) if r["target_agent_id"] else None,
            "level": r["level"],
        }
        for r in rows
    ]


async def get_effective_level(source_agent_id: str, target_agent_id: str) -> int:
    """Get effective permission level: manual override > trust-derived > default.

    Priority:
    1. Per-agent manual override in permissions table (highest)
    2. Trust-derived level from KNOWS edge trust value
    3. Target agent's default privacy level (lowest)
    """
    # 1. Check manual override
    override = await postgres.fetchval(
        "SELECT level FROM permissions WHERE agent_id = $1 AND target_agent_id = $2",
        uuid.UUID(target_agent_id),
        uuid.UUID(source_agent_id),
    )
    if override is not None:
        return override

    # 2. Check trust-derived level from KNOWS edge
    try:
        records = await neo4j_client.execute_read(
            """MATCH (a:Agent {id: $aid})-[r:KNOWS]-(b:Agent {id: $bid})
               RETURN r.trust AS trust""",
            aid=source_agent_id,
            bid=target_agent_id,
        )
        if records and records[0].get("trust") is not None:
            return trust_derived_permission(records[0]["trust"])
    except Exception as e:
        logger.warning("trust_permission_lookup_failed", error=str(e))

    # 3. Fallback to target's default
    default = await postgres.fetchval(
        "SELECT default_privacy_level FROM agents WHERE id = $1",
        uuid.UUID(target_agent_id),
    )
    return default if default is not None else 0


async def check_access(
    source_agent_id: str,
    target_agent_id: str,
    required_level: int,
    category: str,
    tenant_id: str,
) -> bool:
    """Check if source can access target's data at required_level. Always logs."""
    effective = await get_effective_level(source_agent_id, target_agent_id)
    allowed = effective >= required_level

    await _log_audit(
        tenant_id=tenant_id,
        agent_id=source_agent_id,
        action="access_check",
        target_agent_id=target_agent_id,
        permission_level_used=required_level,
        data_category=category,
    )

    return allowed


async def get_audit_log(agent_id: str, tenant_id: str, limit: int = 50) -> list[dict]:
    """Get recent audit entries for an agent."""
    rows = await postgres.fetch(
        """SELECT * FROM audit_log
           WHERE agent_id = $1 AND tenant_id = $2
           ORDER BY created_at DESC LIMIT $3""",
        uuid.UUID(agent_id),
        uuid.UUID(tenant_id),
        limit,
    )
    return [
        {
            "id": str(r["id"]),
            "tenant_id": str(r["tenant_id"]),
            "agent_id": str(r["agent_id"]),
            "action": r["action"],
            "target_agent_id": str(r["target_agent_id"]) if r["target_agent_id"] else None,
            "permission_level_used": r["permission_level_used"],
            "data_category": r["data_category"],
            "created_at": r["created_at"].isoformat(),
        }
        for r in rows
    ]


async def _log_audit(
    tenant_id: str,
    agent_id: str,
    action: str,
    target_agent_id: str | None = None,
    permission_level_used: int | None = None,
    data_category: str | None = None,
    langfuse_trace_id: str | None = None,
) -> None:
    """Append to audit log."""
    await postgres.execute(
        """INSERT INTO audit_log
           (tenant_id, agent_id, action, target_agent_id,
            permission_level_used, data_category, langfuse_trace_id)
           VALUES ($1, $2, $3, $4, $5, $6, $7)""",
        uuid.UUID(tenant_id),
        uuid.UUID(agent_id),
        action,
        uuid.UUID(target_agent_id) if target_agent_id else None,
        permission_level_used,
        data_category,
        langfuse_trace_id,
    )
