"""Avatar pipeline — Edge TTS + SadTalker for talking-head videos."""

import uuid

import httpx
import structlog

from src.config import settings

logger = structlog.get_logger(__name__)

PRESET_AVATARS = [
    {"id": "avatar-1", "name": "Professional", "url": "/static/avatars/professional.png"},
    {"id": "avatar-2", "name": "Friendly", "url": "/static/avatars/friendly.png"},
    {"id": "avatar-3", "name": "Scholar", "url": "/static/avatars/scholar.png"},
    {"id": "avatar-4", "name": "Creative", "url": "/static/avatars/creative.png"},
    {"id": "avatar-5", "name": "Mentor", "url": "/static/avatars/mentor.png"},
    {"id": "avatar-6", "name": "Explorer", "url": "/static/avatars/explorer.png"},
]


async def generate_tts_audio(text: str, voice: str | None = None) -> bytes | None:
    """Generate TTS audio via Edge TTS."""
    try:
        import edge_tts

        voice = voice or settings.avatar.edge_tts_voice
        communicate = edge_tts.Communicate(text, voice)
        audio_data = b""
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_data += chunk["data"]
        return audio_data
    except ImportError:
        logger.warning("edge_tts_not_installed")
        return None
    except Exception as e:
        logger.warning("tts_generation_failed", error=str(e))
        return None


async def generate_avatar_video(
    text: str,
    avatar_image_url: str | None = None,
    voice: str | None = None,
) -> dict:
    """Full avatar pipeline: text → TTS → SadTalker → video URL."""
    video_id = str(uuid.uuid4())

    # Step 1: TTS
    audio = await generate_tts_audio(text, voice)
    if not audio:
        return {"video_id": video_id, "status": "tts_failed", "url": None}

    # Step 2: SadTalker via RunPod (if configured)
    if settings.avatar.runpod_avatar_endpoint:
        try:
            video_url = await _run_sadtalker(audio, avatar_image_url or PRESET_AVATARS[0]["url"])
            return {"video_id": video_id, "status": "complete", "url": video_url}
        except Exception as e:
            logger.warning("sadtalker_failed", error=str(e))

    # Fallback: audio only
    return {"video_id": video_id, "status": "audio_only", "url": None}


async def _run_sadtalker(audio: bytes, image_url: str) -> str | None:
    """Send audio + image to SadTalker on RunPod serverless."""
    import base64

    endpoint = settings.avatar.runpod_avatar_endpoint
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            f"https://api.runpod.ai/v2/{endpoint}/runsync",
            headers={"Authorization": f"Bearer {settings.llm.runpod_api_key}"},
            json={
                "input": {
                    "audio": base64.b64encode(audio).decode(),
                    "image_url": image_url,
                }
            },
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("output", {}).get("video_url")


def get_presets() -> list[dict]:
    """Return available preset avatar images."""
    return PRESET_AVATARS
