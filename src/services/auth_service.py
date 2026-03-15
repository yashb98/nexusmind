"""Auth service — register, login, verify."""

import uuid

import structlog
from fastapi import HTTPException, status

from src.db import postgres
from src.models.auth import LoginRequest, RegisterRequest, TokenResponse, UserResponse
from src.utils.auth import create_access_token, hash_password, verify_password

logger = structlog.get_logger(__name__)


async def register(req: RegisterRequest) -> TokenResponse:
    """Register a new user with auto-created tenant."""
    existing = await postgres.fetchrow("SELECT id FROM users WHERE email = $1", req.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Email already registered"
        )

    tenant_id = str(uuid.uuid4())
    await postgres.execute(
        "INSERT INTO tenants (id, name) VALUES ($1, $2)",
        uuid.UUID(tenant_id),
        f"{req.display_name}'s Workspace",
    )

    user_id = str(uuid.uuid4())
    hashed = hash_password(req.password)
    await postgres.execute(
        "INSERT INTO users (id, tenant_id, email, display_name, hashed_password)"
        " VALUES ($1, $2, $3, $4, $5)",
        uuid.UUID(user_id),
        uuid.UUID(tenant_id),
        req.email,
        req.display_name,
        hashed,
    )

    logger.info("user_registered", user_id=user_id, email=req.email)
    token = create_access_token(user_id, tenant_id)
    return TokenResponse(access_token=token)


async def login(req: LoginRequest) -> TokenResponse:
    """Authenticate a user and return a JWT."""
    row = await postgres.fetchrow(
        "SELECT id, tenant_id, hashed_password FROM users WHERE email = $1", req.email
    )
    if not row or not verify_password(req.password, row["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password"
        )

    user_id = str(row["id"])
    tenant_id = str(row["tenant_id"])
    logger.info("user_login", user_id=user_id)
    token = create_access_token(user_id, tenant_id)
    return TokenResponse(access_token=token)


async def get_user(user_id: str) -> UserResponse:
    """Get user info by ID."""
    row = await postgres.fetchrow("SELECT * FROM users WHERE id = $1", uuid.UUID(user_id))
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return UserResponse(
        id=str(row["id"]),
        tenant_id=str(row["tenant_id"]),
        email=row["email"],
        display_name=row["display_name"],
        role=row["role"],
    )
