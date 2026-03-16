"""Auth routes — register, login, me."""

import uuid

from fastapi import APIRouter, Depends

from src.db import neo4j_client, postgres
from src.models.auth import LoginRequest, RegisterRequest, TokenResponse, UserResponse, UserUpdate
from src.services import auth_service
from src.utils.auth import get_current_user

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(req: RegisterRequest) -> TokenResponse:
    """Register a new user."""
    return await auth_service.register(req)


@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest) -> TokenResponse:
    """Login and get JWT token."""
    return await auth_service.login(req)


@router.get("/me", response_model=UserResponse)
async def me(current_user: dict = Depends(get_current_user)) -> UserResponse:
    """Get current user info (protected route)."""
    return await auth_service.get_user(current_user["user_id"])


@router.patch("/me", response_model=UserResponse)
async def update_me(
    req: UserUpdate, current_user: dict = Depends(get_current_user)
) -> UserResponse:
    """Update current user info."""
    return await auth_service.update_user(current_user["user_id"], req)


@router.delete("/me")
async def delete_account(current_user: dict = Depends(get_current_user)):
    """Hard delete user account and all associated data."""
    user_id = current_user["user_id"]

    # Delete agents first
    agents = await postgres.fetch(
        "SELECT id FROM agents WHERE user_id = $1", uuid.UUID(user_id)
    )
    for agent in agents:
        try:
            await neo4j_client.execute_write(
                "MATCH (a:Agent {id: $id}) DETACH DELETE a",
                id=str(agent["id"]),
            )
        except Exception:
            pass

    await postgres.execute("DELETE FROM agents WHERE user_id = $1", uuid.UUID(user_id))
    await postgres.execute("DELETE FROM notification_preferences WHERE user_id = $1", uuid.UUID(user_id))
    await postgres.execute("DELETE FROM users WHERE id = $1", uuid.UUID(user_id))

    return {"status": "deleted"}
