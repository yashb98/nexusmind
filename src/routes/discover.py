"""Discovery routes — recommended agents, groups, and events."""

from fastapi import APIRouter, Depends

from src.services import event_service, group_service
from src.services.graph import get_recommendations
from src.utils.auth import get_current_user

router = APIRouter(prefix="/api/v1/discover", tags=["discover"])


@router.get("/agents")
async def discover_agents(
    agent_id: str,
    limit: int = 5,
    current_user: dict = Depends(get_current_user),
) -> list[dict]:
    """Get recommended agents based on graph proximity."""
    return await get_recommendations(
        agent_id, current_user["tenant_id"], limit=limit
    )


@router.get("/groups")
async def discover_groups(
    limit: int = 10,
    current_user: dict = Depends(get_current_user),
) -> list[dict]:
    """Discover popular public groups."""
    return await group_service.discover_groups(
        current_user["tenant_id"], limit=limit
    )


@router.get("/events")
async def discover_events(
    limit: int = 10,
    current_user: dict = Depends(get_current_user),
) -> list[dict]:
    """Get upcoming events."""
    return await event_service.list_events(
        current_user["tenant_id"], status="scheduled", limit=limit
    )
