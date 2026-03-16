"""Event CRUD and lifecycle routes (tenant-scoped)."""

from fastapi import APIRouter, Depends, HTTPException, status

from src.services import event_service
from src.utils.auth import get_current_user

router = APIRouter(prefix="/api/v1/events", tags=["events"])


@router.post("", status_code=201)
async def create_event(
    data: dict,
    current_user: dict = Depends(get_current_user),
) -> dict:
    """Create a new event."""
    if "title" not in data:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Field 'title' is required",
        )
    return await event_service.create_event(
        data, current_user["user_id"], current_user["tenant_id"]
    )


@router.get("")
async def list_events(
    event_status: str | None = None,
    limit: int = 20,
    current_user: dict = Depends(get_current_user),
) -> list[dict]:
    """List events with optional status filter."""
    return await event_service.list_events(
        current_user["tenant_id"], status=event_status, limit=limit
    )


@router.get("/{event_id}")
async def get_event(
    event_id: str,
    current_user: dict = Depends(get_current_user),
) -> dict:
    """Get event detail."""
    event = await event_service.get_event(event_id)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Event not found"
        )
    return event


@router.post("/{event_id}/join")
async def join_event(
    event_id: str,
    data: dict,
    current_user: dict = Depends(get_current_user),
) -> dict:
    """Join an event with an agent."""
    if "agent_id" not in data:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Field 'agent_id' is required",
        )
    await event_service.join_event(event_id, data["agent_id"])
    return {"status": "joined"}


@router.post("/{event_id}/start")
async def start_event(
    event_id: str,
    current_user: dict = Depends(get_current_user),
) -> dict:
    """Start a scheduled event (admin only)."""
    event = await event_service.start_event(event_id)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found or not in scheduled status",
        )
    return event


@router.get("/{event_id}/results")
async def get_results(
    event_id: str,
    current_user: dict = Depends(get_current_user),
) -> dict:
    """Get event results."""
    results = await event_service.get_results(event_id)
    if not results:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Event not found"
        )
    return results
