"""Self-evolution — research scout + code improvement proposals."""

import uuid

import structlog

from src.db import postgres
from src.llm import llm_service
from src.services import search as search_service

logger = structlog.get_logger(__name__)

RESEARCH_TOPICS = [
    "personality LLM fine-tuning",
    "Socratic teaching AI",
    "knowledge graph RAG",
    "LoRA adapter merging",
    "community detection algorithms",
    "emergent behavior multi-agent",
    "self-improving AI systems",
    "Bloom taxonomy assessment",
    "conversation quality evaluation",
    "hallucination detection LLM",
]


async def run_research_scout() -> dict:
    """Weekly research scout — search for relevant papers."""
    proposals_created = 0

    for topic in RESEARCH_TOPICS:
        results = await search_service.web_search(f"arxiv {topic} 2026", max_results=3)
        if not results:
            continue

        for result in results:
            relevance = await _score_relevance(result, topic)
            if relevance < 0.7:
                continue

            proposal_id = str(uuid.uuid4())
            await postgres.execute(
                """INSERT INTO evolution_proposals
                   (id, proposal_type, title, source_url,
                    relevance_score, difficulty_score, improvement_score,
                    description, status)
                   VALUES ($1, $2, $3, $4, $5, $6, $7, $8, 'pending')""",
                uuid.UUID(proposal_id),
                "research",
                result.get("title", "Untitled"),
                result.get("url", ""),
                relevance,
                0.5,  # default difficulty
                0.5,  # default improvement
                result.get("content", ""),
            )
            proposals_created += 1

    logger.info("research_scout_complete", proposals=proposals_created)
    return {"proposals_created": proposals_created}


async def run_code_improvement() -> dict:
    """Weekly code improvement — analyze metrics and propose changes."""
    # Collect system metrics
    metrics = await _collect_system_metrics()

    # Identify areas for improvement
    issues = _identify_issues(metrics)

    proposals_created = 0
    for issue in issues:
        proposal_id = str(uuid.uuid4())
        await postgres.execute(
            """INSERT INTO evolution_proposals
               (id, proposal_type, title, description,
                improvement_score, status)
               VALUES ($1, $2, $3, $4, $5, 'pending')""",
            uuid.UUID(proposal_id),
            "code",
            issue["title"],
            issue["description"],
            issue.get("improvement_score", 0.5),
        )
        proposals_created += 1

    logger.info("code_improvement_complete", proposals=proposals_created)
    return {"proposals_created": proposals_created}


async def get_proposals(
    proposal_type: str | None = None,
    status: str | None = None,
    limit: int = 20,
) -> list[dict]:
    """Get evolution proposals with optional filtering."""
    query = "SELECT * FROM evolution_proposals WHERE 1=1"
    params: list = []
    idx = 1

    if proposal_type:
        query += f" AND proposal_type = ${idx}"
        params.append(proposal_type)
        idx += 1

    if status:
        query += f" AND status = ${idx}"
        params.append(status)
        idx += 1

    query += f" ORDER BY created_at DESC LIMIT ${idx}"
    params.append(limit)

    rows = await postgres.fetch(query, *params)
    return [
        {
            "id": str(r["id"]),
            "type": r["proposal_type"],
            "title": r["title"],
            "source_url": r.get("source_url"),
            "relevance_score": r.get("relevance_score"),
            "status": r["status"],
            "created_at": r["created_at"].isoformat(),
        }
        for r in rows
    ]


async def update_proposal_status(proposal_id: str, status: str) -> bool:
    """Update proposal status (approved/rejected)."""
    result = await postgres.execute(
        "UPDATE evolution_proposals SET status = $1 WHERE id = $2",
        status,
        uuid.UUID(proposal_id),
    )
    return result == "UPDATE 1"


async def get_finetune_history(limit: int = 20) -> list[dict]:
    """Get fine-tune run history."""
    rows = await postgres.fetch(
        """SELECT * FROM finetune_runs
           ORDER BY completed_at DESC NULLS LAST
           LIMIT $1""",
        limit,
    )
    return [
        {
            "id": str(r["id"]),
            "run_type": r["run_type"],
            "archetype": r["archetype"],
            "training_examples": r["training_examples"],
            "val_loss_start": r["val_loss_start"],
            "val_loss_end": r["val_loss_end"],
            "personality_variance": r["personality_variance"],
            "deployed": r["deployed"],
            "started_at": r["started_at"].isoformat() if r["started_at"] else None,
            "completed_at": r["completed_at"].isoformat() if r["completed_at"] else None,
        }
        for r in rows
    ]


async def _score_relevance(result: dict, topic: str) -> float:
    """Score how relevant a search result is to our system."""
    try:
        response = await llm_service.generate(
            system_prompt="Score relevance 0-1. Return only a number.",
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"Topic: {topic}\n"
                        f"Title: {result.get('title', '')}\n"
                        f"Content: {result.get('content', '')[:500]}\n"
                        "Relevance to NexusMind (AI agent platform)?"
                    ),
                }
            ],
            trace_id=f"relevance-{uuid.uuid4()}",
            temperature=0.2,
            max_tokens=10,
        )
        return min(1.0, max(0.0, float(response.strip())))
    except (ValueError, Exception):
        return 0.3


async def _collect_system_metrics() -> dict:
    """Collect system performance metrics."""
    try:
        avg_quality = await postgres.fetchval(
            """SELECT AVG(quality_score) FROM scheduler_metrics
               WHERE created_at > NOW() - INTERVAL '7 days'""",
        )
        total_convos = await postgres.fetchval(
            """SELECT COUNT(*) FROM scheduler_metrics
               WHERE created_at > NOW() - INTERVAL '7 days'""",
        )
        acceptance_rate = await postgres.fetchval(
            """SELECT AVG(CASE WHEN judge_decision = 'accepted' THEN 1.0 ELSE 0.0 END)
               FROM verification_decisions
               WHERE created_at > NOW() - INTERVAL '7 days'""",
        )
        return {
            "avg_quality": float(avg_quality or 0),
            "total_conversations": int(total_convos or 0),
            "acceptance_rate": float(acceptance_rate or 0),
        }
    except Exception:
        return {"avg_quality": 0, "total_conversations": 0, "acceptance_rate": 0}


def _identify_issues(metrics: dict) -> list[dict]:
    """Identify areas for improvement based on metrics."""
    issues = []

    if metrics.get("avg_quality", 0) < 5.0:
        issues.append(
            {
                "title": "Low average conversation quality",
                "description": (
                    f"Average quality score is {metrics['avg_quality']:.1f}. "
                    "Consider tuning prompt templates or phase timing."
                ),
                "improvement_score": 0.7,
            }
        )

    if metrics.get("acceptance_rate", 0) < 0.5:
        issues.append(
            {
                "title": "Low verification acceptance rate",
                "description": (
                    f"Only {metrics['acceptance_rate']:.0%} of insights accepted. "
                    "Review conversation depth or extraction prompts."
                ),
                "improvement_score": 0.6,
            }
        )

    return issues
