"""Merge multiple micro-adapters into a single adapter."""

import structlog

logger = structlog.get_logger(__name__)


def merge_adapters(
    adapter_paths: list[str],
    quality_scores: list[float],
    output_path: str,
) -> str:
    """Weighted merge of micro-adapters based on quality scores."""
    if not adapter_paths:
        raise ValueError("No adapters to merge")

    # Placeholder: actual merge would use MLX or PEFT
    # Weight each adapter proportional to its quality score
    total_quality = sum(quality_scores)
    weights = [q / total_quality for q in quality_scores] if total_quality > 0 else []

    logger.info(
        "adapters_merged",
        count=len(adapter_paths),
        weights=weights,
        output=output_path,
    )

    return output_path


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--adapters", nargs="+", required=True)
    parser.add_argument("--scores", nargs="+", type=float, required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    merge_adapters(args.adapters, args.scores, args.output)
