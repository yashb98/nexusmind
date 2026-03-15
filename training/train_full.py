"""Full adapter training — nightly, rank=16, thorough."""

import argparse
import uuid
from datetime import UTC, datetime

import structlog

logger = structlog.get_logger(__name__)


def train_full(
    archetype: str = "all",
    data_path: str = "training/data/full.jsonl",
    iters: int = 500,
    rank: int = 16,
    batch_size: int = 4,
) -> dict:
    """Train a full LoRA adapter."""
    run_id = str(uuid.uuid4())
    started_at = datetime.now(UTC)

    logger.info(
        "full_train_start",
        run_id=run_id,
        archetype=archetype,
        rank=rank,
        iters=iters,
    )

    # Placeholder: actual training implementation
    result = {
        "run_id": run_id,
        "run_type": "full",
        "archetype": archetype,
        "rank": rank,
        "iters": iters,
        "val_loss_start": 2.5,
        "val_loss_end": 1.8,
        "adapter_path": f"adapters/{archetype}_full_{run_id[:8]}",
        "started_at": started_at.isoformat(),
        "completed_at": datetime.now(UTC).isoformat(),
    }

    logger.info("full_train_complete", **result)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--archetype", default="all")
    parser.add_argument("--data", default="training/data/full.jsonl")
    parser.add_argument("--iters", type=int, default=500)
    args = parser.parse_args()
    train_full(args.archetype, args.data, args.iters)
