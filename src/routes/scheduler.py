"""Scheduler routes — status, pause, resume."""

from fastapi import APIRouter, Depends

from src.services.scheduler import scheduler
from src.utils.auth import get_current_user

router = APIRouter(prefix="/api/v1/scheduler", tags=["scheduler"])


@router.get("/status")
async def get_status(current_user: dict = Depends(get_current_user)) -> dict:
    """Get background scheduler status."""
    return scheduler.get_status()


@router.post("/pause")
async def pause(current_user: dict = Depends(get_current_user)) -> dict:
    """Pause the background scheduler."""
    scheduler.pause()
    return {"status": "paused"}


@router.post("/resume")
async def resume(current_user: dict = Depends(get_current_user)) -> dict:
    """Resume the background scheduler."""
    scheduler.resume()
    return {"status": "resumed"}
