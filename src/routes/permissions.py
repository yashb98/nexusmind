"""Permission routes — set, list, audit."""

from fastapi import APIRouter, Depends

from src.models.permission import AuditEntry, PermissionResponse, PermissionSet
from src.services import permission as permission_service
from src.utils.auth import get_current_user

router = APIRouter(prefix="/api/v1/agents", tags=["permissions"])


@router.post("/{agent_id}/permissions", status_code=201)
async def set_permission(
    agent_id: str,
    req: PermissionSet,
    current_user: dict = Depends(get_current_user),
) -> dict:
    """Set permission level for a target agent."""
    await permission_service.set_permission(
        agent_id, req.target_agent_id, req.level, current_user["tenant_id"]
    )
    return {"status": "ok"}


@router.get("/{agent_id}/permissions", response_model=list[PermissionResponse])
async def get_permissions(
    agent_id: str, current_user: dict = Depends(get_current_user)
) -> list[dict]:
    """Get all permission overrides for an agent."""
    return await permission_service.get_permissions(agent_id)


@router.get("/{agent_id}/audit", response_model=list[AuditEntry])
async def get_audit(agent_id: str, current_user: dict = Depends(get_current_user)) -> list[dict]:
    """Get audit log for an agent."""
    return await permission_service.get_audit_log(agent_id, current_user["tenant_id"])
