"""Prepare training data — conversations → JSONL with fact/pattern separation."""

import json
import re
from pathlib import Path

import structlog

logger = structlog.get_logger(__name__)

# Patterns to strip (facts that belong in memory, not weights)
FACT_PATTERNS = [
    r"\b\d{4}-\d{2}-\d{2}\b",  # dates
    r"\bhttps?://\S+",  # URLs
    r"\b\d+\.?\d*%",  # percentages
    r"\$\d+[\d,]*\.?\d*",  # dollar amounts
]


def strip_facts(text: str) -> str:
    """Remove factual content that should stay in memory, not weights."""
    result = text
    for pattern in FACT_PATTERNS:
        result = re.sub(pattern, "[FACT]", result)
    return result


def prepare_conversation_jsonl(
    conversations: list[dict],
    output_path: str,
    archetype: str | None = None,
    min_quality: float = 3.5,
) -> int:
    """Convert verified conversations to training JSONL."""
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    count = 0
    with open(output, "w") as f:
        for conv in conversations:
            if conv.get("quality_score", 0) < min_quality:
                continue

            messages = conv.get("messages", [])
            if len(messages) < 4:
                continue

            # Build training example
            system_prompt = conv.get("system_prompt", "You are an AI agent.")
            train_messages = []
            for msg in messages:
                content = strip_facts(msg["content"])
                role = "assistant" if msg.get("is_speaker") else "user"
                train_messages.append({"role": role, "content": content})

            example = {
                "messages": [
                    {"role": "system", "content": system_prompt},
                    *train_messages,
                ]
            }
            f.write(json.dumps(example) + "\n")
            count += 1

    logger.info("training_data_prepared", examples=count, path=output_path)
    return count
