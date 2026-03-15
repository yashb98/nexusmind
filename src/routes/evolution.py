"""Evolution dashboard routes — proposals, fine-tune history, metrics."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from src.services import evolution as evolution_service
from src.utils.auth import get_current_user

router = APIRouter(prefix="/api/v1/evolution", tags=["evolution"])


class StatusUpdate(BaseModel):
    status: str  # approved, rejected


@router.get("/proposals")
async def list_proposals(
    proposal_type: str | None = None,
    status: str | None = None,
    limit: int = 20,
    current_user: dict = Depends(get_current_user),
) -> list[dict]:
    """List evolution proposals."""
    return await evolution_service.get_proposals(proposal_type, status, limit)


@router.patch("/proposals/{proposal_id}")
async def update_proposal(
    proposal_id: str,
    req: StatusUpdate,
    current_user: dict = Depends(get_current_user),
) -> dict:
    """Update proposal status."""
    updated = await evolution_service.update_proposal_status(proposal_id, req.status)
    return {"updated": updated}


@router.get("/finetune/history")
async def finetune_history(
    limit: int = 20,
    current_user: dict = Depends(get_current_user),
) -> list[dict]:
    """Get fine-tune run history."""
    return await evolution_service.get_finetune_history(limit)


@router.post("/finetune/trigger")
async def trigger_finetune(
    current_user: dict = Depends(get_current_user),
) -> dict:
    """Manually trigger a fine-tune run (placeholder)."""
    return {"status": "queued", "message": "Fine-tune run queued"}


@router.get("/metrics")
async def get_metrics(
    current_user: dict = Depends(get_current_user),
) -> dict:
    """Get system evolution metrics."""
    from src.services.evolution import _collect_system_metrics

    return await _collect_system_metrics()
