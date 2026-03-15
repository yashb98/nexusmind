"""Teach-back routes — Socratic tutoring sessions."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from src.db import postgres
from src.services import teachback as teachback_service
from src.utils.auth import get_current_user

router = APIRouter(prefix="/api/v1/teachback", tags=["teachback"])


class StartRequest(BaseModel):
    insight_id: str
    insight_content: str
    topic: str


class RespondRequest(BaseModel):
    message: str


@router.post("/start")
async def start_session(
    req: StartRequest,
    current_user: dict = Depends(get_current_user),
) -> dict:
    """Start a teach-back session for an insight."""
    return await teachback_service.start_session(
        user_id=current_user["user_id"],
        insight_id=req.insight_id,
        insight_content=req.insight_content,
        topic=req.topic,
    )


@router.post("/{session_id}/respond")
async def respond(
    session_id: str,
    req: RespondRequest,
    current_user: dict = Depends(get_current_user),
) -> dict:
    """Send a learner response and get tutor's next message."""
    return await teachback_service.process_response(session_id, req.message)


@router.post("/{session_id}/complete")
async def complete(
    session_id: str,
    current_user: dict = Depends(get_current_user),
) -> dict:
    """Complete session and assess Bloom level change."""
    return await teachback_service.complete_session(session_id)


@router.get("/{session_id}")
async def get_session(
    session_id: str,
    current_user: dict = Depends(get_current_user),
) -> dict:
    """Get session details."""
    import uuid

    row = await postgres.fetchrow(
        "SELECT * FROM teachback_sessions WHERE id = $1",
        uuid.UUID(session_id),
    )
    if not row:
        return {"error": "Not found"}
    return {
        "id": str(row["id"]),
        "topic": row["topic"],
        "bloom_level_start": row["bloom_level_start"],
        "bloom_level_end": row["bloom_level_end"],
        "turns": row["turns"],
        "status": row["status"],
    }
