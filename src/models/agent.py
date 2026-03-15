"""Agent request/response models."""

from pydantic import BaseModel, Field


class AgentCreate(BaseModel):
    """Create agent request."""

    display_name: str = Field(min_length=1, max_length=255)
    openness: float = Field(ge=0, le=1)
    conscientiousness: float = Field(ge=0, le=1)
    extraversion: float = Field(ge=0, le=1)
    agreeableness: float = Field(ge=0, le=1)
    neuroticism: float = Field(ge=0, le=1)
    interests: list[str] = Field(min_length=1, max_length=10)
    communication_style: str = Field(default="analytical")
    lora_archetype: str | None = None
    default_privacy_level: int = Field(default=2, ge=0, le=5)
    avatar_image_url: str | None = None
    default_trust_for_strangers: float = Field(default=0.2, ge=0, le=1)
    is_mock: bool = False


class AgentUpdate(BaseModel):
    """Update agent request (all fields optional)."""

    display_name: str | None = None
    interests: list[str] | None = None
    communication_style: str | None = None
    default_privacy_level: int | None = Field(default=None, ge=0, le=5)
    avatar_image_url: str | None = None


class AgentResponse(BaseModel):
    """Agent response."""

    id: str
    user_id: str
    tenant_id: str
    display_name: str
    openness: float
    conscientiousness: float
    extraversion: float
    agreeableness: float
    neuroticism: float
    interests: list[str]
    communication_style: str
    lora_archetype: str | None
    default_privacy_level: int
    avatar_image_url: str | None
    default_trust_for_strangers: float
    is_mock: bool
    status: str
