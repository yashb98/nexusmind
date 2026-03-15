"""Graph routes — network, recommendations."""

from fastapi import APIRouter, Depends

from src.services import graph as graph_service
from src.utils.auth import get_current_user

router = APIRouter(prefix="/api/v1/graph", tags=["graph"])


@router.get("/agents/{agent_id}/network")
async def get_network(
    agent_id: str,
    hops: int = 2,
    current_user: dict = Depends(get_current_user),
) -> dict:
    """Get agent's network graph (nodes + edges)."""
    return await graph_service.get_agent_network(agent_id, current_user["tenant_id"], hops)


@router.get("/agents/{agent_id}/recommendations")
async def get_recommendations(
    agent_id: str, current_user: dict = Depends(get_current_user)
) -> list[dict]:
    """Get recommended agents to connect with."""
    return await graph_service.get_recommendations(agent_id, current_user["tenant_id"])
