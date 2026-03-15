"""Avatar routes — generate, presets."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from src.services import avatar as avatar_service
from src.utils.auth import get_current_user

router = APIRouter(prefix="/api/v1/avatar", tags=["avatar"])


class GenerateRequest(BaseModel):
    text: str
    avatar_image_url: str | None = None
    voice: str | None = None


@router.post("/generate")
async def generate(
    req: GenerateRequest,
    current_user: dict = Depends(get_current_user),
) -> dict:
    """Generate avatar video from text."""
    return await avatar_service.generate_avatar_video(
        text=req.text,
        avatar_image_url=req.avatar_image_url,
        voice=req.voice,
    )


@router.get("/presets")
async def presets() -> list[dict]:
    """Get available preset avatars."""
    return avatar_service.get_presets()
