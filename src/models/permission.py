"""Permission request/response models."""

from pydantic import BaseModel, Field


class PermissionSet(BaseModel):
    """Set permission level for a target agent."""

    target_agent_id: str
    level: int = Field(ge=0, le=5)


class PermissionResponse(BaseModel):
    """Permission entry response."""

    id: str
    agent_id: str
    target_agent_id: str | None
    level: int


class AuditEntry(BaseModel):
    """Audit log entry."""

    id: str
    tenant_id: str
    agent_id: str
    action: str
    target_agent_id: str | None
    permission_level_used: int | None
    data_category: str | None
    created_at: str
