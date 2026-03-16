"""Auth request/response models."""

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    """User registration request."""

    email: EmailStr
    display_name: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    """User login request."""

    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """JWT token response."""

    access_token: str
    token_type: str = "bearer"


class UserUpdate(BaseModel):
    """User update request."""

    display_name: str | None = Field(default=None, min_length=1, max_length=255)


class UserResponse(BaseModel):
    """User info response."""

    id: str
    tenant_id: str
    email: str
    display_name: str
    role: str
