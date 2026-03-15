"""Auth routes — register, login, me."""

from fastapi import APIRouter, Depends

from src.models.auth import LoginRequest, RegisterRequest, TokenResponse, UserResponse
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
