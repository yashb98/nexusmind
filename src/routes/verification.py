"""Verification routes — recent decisions and detail."""

from fastapi import APIRouter, Depends

from src.db import postgres
from src.utils.auth import get_current_user

router = APIRouter(prefix="/api/v1/verification", tags=["verification"])


@router.get("/recent")
async def get_recent(
    limit: int = 20,
    current_user: dict = Depends(get_current_user),
) -> list[dict]:
    """Get recent verification council decisions."""
    rows = await postgres.fetch(
        """SELECT id, insight_content, skeptic_score, connector_score,
                  judge_decision, judge_reasoning, created_at
           FROM verification_decisions
           ORDER BY created_at DESC LIMIT $1""",
        limit,
    )
    return [
        {
            "id": str(r["id"]),
            "insight_content": r["insight_content"],
            "skeptic_score": r["skeptic_score"],
            "connector_score": r["connector_score"],
            "decision": r["judge_decision"],
            "reasoning": r["judge_reasoning"],
            "created_at": r["created_at"].isoformat(),
        }
        for r in rows
    ]


@router.get("/{insight_id}")
async def get_decision(
    insight_id: str,
    current_user: dict = Depends(get_current_user),
) -> dict:
    """Get verification decision detail for an insight."""
    import uuid

    row = await postgres.fetchrow(
        "SELECT * FROM verification_decisions WHERE id = $1",
        uuid.UUID(insight_id),
    )
    if not row:
        return {"error": "Not found"}
    return {
        "id": str(row["id"]),
        "insight_content": row["insight_content"],
        "skeptic_score": row["skeptic_score"],
        "skeptic_reasoning": row["skeptic_reasoning"],
        "connector_score": row["connector_score"],
        "connector_relations": row["connector_relations"],
        "decision": row["judge_decision"],
        "reasoning": row["judge_reasoning"],
        "created_at": row["created_at"].isoformat(),
    }
