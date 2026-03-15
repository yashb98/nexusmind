"""Connection request models."""

from pydantic import BaseModel, Field


class ConnectionRequest(BaseModel):
    """Send a connection request."""

    to_agent_id: str
    message: str | None = Field(default=None, max_length=500)


class ConnectionResponse(BaseModel):
    """Connection request response."""

    id: str
    from_agent_id: str
    to_agent_id: str
    message: str | None
    status: str
    created_at: str
    responded_at: str | None


class ConnectionInfo(BaseModel):
    """Connection with trust info."""

    agent_id: str
    display_name: str
    trust: float
    conversation_count: int
    topics_shared: list[str]
    is_mock: bool
