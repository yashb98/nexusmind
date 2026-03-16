"""Activity feed routes."""

from fastapi import APIRouter, Depends

from src.services import feed_service
from src.utils.auth import get_current_user

router = APIRouter(prefix="/api/v1/feed", tags=["feed"])


@router.get("")
async def get_feed(
    limit: int = 50,
    offset: int = 0,
    current_user: dict = Depends(get_current_user),
) -> list[dict]:
    """Get paginated activity feed."""
    return await feed_service.get_feed(
        current_user["user_id"], limit=limit, offset=offset
    )


@router.get("/unread")
async def get_unread_count(
    current_user: dict = Depends(get_current_user),
) -> dict:
    """Get unread feed item count."""
    count = await feed_service.get_unread_count(current_user["user_id"])
    return {"unread_count": count}


@router.patch("/{item_id}/read")
async def mark_read(
    item_id: str,
    current_user: dict = Depends(get_current_user),
) -> dict:
    """Mark a feed item as read."""
    await feed_service.mark_read(item_id)
    return {"status": "read"}
