"""Connection management routes (tenant-scoped)."""

from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.models.connection import ConnectionInfo, ConnectionRequest, ConnectionResponse
from src.services import connection_service
from src.utils.auth import get_current_user

router = APIRouter(prefix="/api/v1/connections", tags=["connections"])


@router.post("/invite", response_model=dict)
async def generate_invite_link(
    agent_id: str = Query(..., description="Agent ID generating the invite"),
    current_user: dict = Depends(get_current_user),
) -> dict:
    """Generate an invite link for an agent."""
    link = await connection_service.generate_invite_link(
        agent_id, current_user["tenant_id"]
    )
    return {"invite_link": link}


@router.post("/request", response_model=ConnectionResponse, status_code=201)
async def send_connection_request(
    req: ConnectionRequest,
    from_agent_id: str = Query(..., description="Agent sending the request"),
    current_user: dict = Depends(get_current_user),
) -> ConnectionResponse:
    """Send a connection request to another agent."""
    return await connection_service.send_request(
        from_agent_id, req.to_agent_id, req.message, current_user["tenant_id"]
    )


@router.get("/requests", response_model=list[ConnectionResponse])
async def list_pending_requests(
    agent_id: str = Query(..., description="Agent receiving requests"),
    current_user: dict = Depends(get_current_user),
) -> list[ConnectionResponse]:
    """List pending incoming connection requests."""
    return await connection_service.list_pending_requests(
        agent_id, current_user["tenant_id"]
    )


@router.patch("/requests/{request_id}", response_model=ConnectionResponse)
async def respond_to_request(
    request_id: str,
    accept: bool = Query(..., description="Accept or reject the request"),
    current_user: dict = Depends(get_current_user),
) -> ConnectionResponse:
    """Accept or reject a connection request."""
    try:
        return await connection_service.respond_to_request(
            request_id, accept, current_user["tenant_id"]
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        ) from e


@router.get("/{agent_id}/connections", response_model=list[ConnectionInfo])
async def list_connections(
    agent_id: str,
    current_user: dict = Depends(get_current_user),
) -> list[ConnectionInfo]:
    """List all connections with trust levels for an agent."""
    return await connection_service.list_connections(
        agent_id, current_user["tenant_id"]
    )
