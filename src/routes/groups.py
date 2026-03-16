"""Group CRUD and membership routes (tenant-scoped)."""

from fastapi import APIRouter, Depends, HTTPException, status

from src.services import group_service
from src.utils.auth import get_current_user

router = APIRouter(prefix="/api/v1/groups", tags=["groups"])


@router.post("", status_code=201)
async def create_group(
    data: dict,
    current_user: dict = Depends(get_current_user),
) -> dict:
    """Create a new group."""
    if "name" not in data:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Field 'name' is required",
        )
    return await group_service.create_group(
        data, current_user["user_id"], current_user["tenant_id"]
    )


@router.get("")
async def list_groups(
    current_user: dict = Depends(get_current_user),
) -> list[dict]:
    """List all groups in the tenant."""
    return await group_service.list_groups(
        current_user["user_id"], current_user["tenant_id"]
    )


@router.get("/discover")
async def discover_groups(
    limit: int = 10,
    current_user: dict = Depends(get_current_user),
) -> list[dict]:
    """Discover popular public groups."""
    return await group_service.discover_groups(
        current_user["tenant_id"], limit=limit
    )


@router.get("/{group_id}")
async def get_group(
    group_id: str,
    current_user: dict = Depends(get_current_user),
) -> dict:
    """Get group detail with members."""
    group = await group_service.get_group(group_id)
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Group not found"
        )
    group["members"] = await group_service.get_members(group_id)
    return group


@router.patch("/{group_id}")
async def update_group(
    group_id: str,
    data: dict,
    current_user: dict = Depends(get_current_user),
) -> dict:
    """Update group fields."""
    group = await group_service.update_group(group_id, data)
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Group not found"
        )
    return group


@router.delete("/{group_id}", status_code=204)
async def delete_group(
    group_id: str,
    current_user: dict = Depends(get_current_user),
) -> None:
    """Delete a group."""
    deleted = await group_service.delete_group(group_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Group not found"
        )


@router.post("/{group_id}/join")
async def join_group(
    group_id: str,
    data: dict,
    current_user: dict = Depends(get_current_user),
) -> dict:
    """Join a group with an agent."""
    if "agent_id" not in data:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Field 'agent_id' is required",
        )
    await group_service.join_group(group_id, data["agent_id"])
    return {"status": "joined"}


@router.post("/{group_id}/leave")
async def leave_group(
    group_id: str,
    data: dict,
    current_user: dict = Depends(get_current_user),
) -> dict:
    """Leave a group with an agent."""
    if "agent_id" not in data:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Field 'agent_id' is required",
        )
    await group_service.leave_group(group_id, data["agent_id"])
    return {"status": "left"}
