"""Verification Council — Skeptic + Connector + Judge for knowledge quality."""

import asyncio
import uuid

import structlog

from src.config import settings
from src.db import neo4j_client, postgres
from src.llm import llm_service

logger = structlog.get_logger(__name__)

SKEPTIC_PROMPT = """You are the Skeptic. Challenge this claim:
"{content}"
Source: {source}

Counter-evidence (if any): {counter_evidence}
Existing contradictions: {contradictions}

Score source reliability 0-1. Provide reasoning.
Return JSON: {{"score": 0.0-1.0, "reasoning": "..."}}"""

CONNECTOR_PROMPT = """You are the Connector. How does this relate to existing knowledge?
"{content}"
Related entities: {related}
Similar memories: {similar}

Score novelty 0-1 and list connections.
Return JSON: {{"score": 0.0-1.0, "connections": ["..."]}}"""

JUDGE_PROMPT = """You are the Judge. Based on:
Skeptic score: {skeptic_score} — {skeptic_reasoning}
Connector score: {connector_score} — {connections}

Decide: ACCEPT / PROVISIONAL / INVESTIGATE / REJECT
Return JSON: {{"decision": "accepted|provisional|investigate|rejected", "reasoning": "..."}}"""


async def verify(
    insight_content: str,
    source_description: str,
    conversation_id: str | None,
    tenant_id: str,
) -> dict:
    """Run the full Verification Council on an insight."""
    if not settings.verification.enabled:
        return {
            "decision": "accepted",
            "skeptic_score": 1.0,
            "connector_score": 1.0,
            "reasoning": "Verification disabled",
        }

    # Skeptic and Connector run in PARALLEL
    skeptic_result, connector_result = await asyncio.gather(
        run_skeptic(insight_content, source_description, tenant_id),
        run_connector(insight_content, tenant_id),
    )

    # Judge uses both results
    decision = await run_judge(insight_content, skeptic_result, connector_result)

    # Store decision in Postgres
    await _store_decision(
        tenant_id=tenant_id,
        insight_content=insight_content,
        source_conversation_id=conversation_id,
        skeptic_result=skeptic_result,
        connector_result=connector_result,
        decision=decision,
    )

    logger.info(
        "verification_complete",
        decision=decision["decision"],
        skeptic=skeptic_result["score"],
        connector=connector_result["score"],
    )

    return {
        "decision": decision["decision"],
        "skeptic_score": skeptic_result["score"],
        "connector_score": connector_result["score"],
        "reasoning": decision.get("reasoning", ""),
    }


async def run_skeptic(content: str, source: str, tenant_id: str) -> dict:
    """Challenge source reliability and search for contradictions."""
    # Check for contradictions in existing graph
    contradictions = await _find_contradictions(content)

    prompt = SKEPTIC_PROMPT.format(
        content=content,
        source=source,
        counter_evidence="No web search available in this context",
        contradictions=contradictions or "None found",
    )

    try:
        response = await llm_service.generate(
            system_prompt="You are a critical evaluator. Return only valid JSON.",
            messages=[{"role": "user", "content": prompt}],
            trace_id=f"skeptic-{uuid.uuid4()}",
            temperature=0.3,
        )
        return _parse_score_response(response, default_score=0.5)
    except Exception as e:
        logger.warning("skeptic_failed", error=str(e))
        return {"score": 0.5, "reasoning": "Skeptic evaluation failed"}


async def run_connector(content: str, tenant_id: str) -> dict:
    """Find how new knowledge relates to existing graph."""
    related = await _find_related_entities(content)

    prompt = CONNECTOR_PROMPT.format(
        content=content,
        related=related or "No related entities found",
        similar="No similar memories in this context",
    )

    try:
        response = await llm_service.generate(
            system_prompt="You are a knowledge connector. Return only valid JSON.",
            messages=[{"role": "user", "content": prompt}],
            trace_id=f"connector-{uuid.uuid4()}",
            temperature=0.3,
        )
        result = _parse_score_response(response, default_score=0.5)
        result.setdefault("connections", [])
        return result
    except Exception as e:
        logger.warning("connector_failed", error=str(e))
        return {"score": 0.5, "connections": []}


async def run_judge(content: str, skeptic: dict, connector: dict) -> dict:
    """Final decision based on Skeptic and Connector scores."""
    skeptic_score = skeptic.get("score", 0.5)

    # Fast path: use thresholds without LLM if clear-cut
    accept_threshold = settings.verification.skeptic_accept_threshold
    reject_threshold = settings.verification.skeptic_reject_threshold

    if skeptic_score >= accept_threshold:
        return {"decision": "accepted", "reasoning": "High confidence from Skeptic"}
    if skeptic_score < reject_threshold:
        return {"decision": "rejected", "reasoning": "Low reliability from Skeptic"}

    # Ambiguous: use LLM judge
    prompt = JUDGE_PROMPT.format(
        skeptic_score=skeptic_score,
        skeptic_reasoning=skeptic.get("reasoning", "N/A"),
        connector_score=connector.get("score", 0.5),
        connections=connector.get("connections", []),
    )

    try:
        response = await llm_service.generate(
            system_prompt="You are an impartial judge. Return only valid JSON.",
            messages=[{"role": "user", "content": prompt}],
            trace_id=f"judge-{uuid.uuid4()}",
            temperature=0.2,
        )
        result = _parse_judge_response(response)
        return result
    except Exception as e:
        logger.warning("judge_failed", error=str(e))
        # Default to provisional when uncertain
        return {"decision": "provisional", "reasoning": "Judge evaluation failed"}


def _parse_score_response(response: str, default_score: float = 0.5) -> dict:
    """Parse a score JSON response from LLM."""
    import json

    try:
        text = response.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            text = "\n".join(lines[1:-1])
        start = text.find("{")
        end = text.rfind("}") + 1
        if start >= 0 and end > start:
            data = json.loads(text[start:end])
            score = float(data.get("score", default_score))
            return {
                "score": max(0.0, min(1.0, score)),
                "reasoning": data.get("reasoning", ""),
                "connections": data.get("connections", []),
            }
    except (json.JSONDecodeError, ValueError):
        pass
    return {"score": default_score, "reasoning": "Parse failed"}


def _parse_judge_response(response: str) -> dict:
    """Parse the judge's decision response."""
    import json

    valid_decisions = {"accepted", "provisional", "investigate", "rejected"}
    try:
        text = response.strip()
        start = text.find("{")
        end = text.rfind("}") + 1
        if start >= 0 and end > start:
            data = json.loads(text[start:end])
            decision = data.get("decision", "provisional").lower()
            if decision not in valid_decisions:
                decision = "provisional"
            return {
                "decision": decision,
                "reasoning": data.get("reasoning", ""),
            }
    except (json.JSONDecodeError, ValueError):
        pass
    return {"decision": "provisional", "reasoning": "Parse failed"}


async def _find_contradictions(content: str) -> str | None:
    """Search Neo4j for entities that might contradict the claim."""
    try:
        records = await neo4j_client.execute_read(
            """MATCH (e1:Entity)-[:CONTRADICTS]->(e2:Entity)
               WHERE e1.name CONTAINS $keyword OR e2.name CONTAINS $keyword
               RETURN e1.name + ' contradicts ' + e2.name AS contradiction
               LIMIT 3""",
            keyword=content.split()[0] if content else "",
        )
        if records:
            return "; ".join(r["contradiction"] for r in records)
    except Exception:
        pass
    return None


async def _find_related_entities(content: str) -> str | None:
    """Find related entities in the graph."""
    try:
        records = await neo4j_client.execute_read(
            """MATCH (e:Entity)
               WHERE e.name CONTAINS $keyword
               RETURN e.name + ' (' + e.type + ')' AS entity
               LIMIT 5""",
            keyword=content.split()[0] if content else "",
        )
        if records:
            return ", ".join(r["entity"] for r in records)
    except Exception:
        pass
    return None


async def _store_decision(
    tenant_id: str,
    insight_content: str,
    source_conversation_id: str | None,
    skeptic_result: dict,
    connector_result: dict,
    decision: dict,
) -> None:
    """Store verification decision in Postgres."""
    import json

    await postgres.execute(
        """INSERT INTO verification_decisions
           (tenant_id, insight_content, source_conversation_id,
            skeptic_score, skeptic_reasoning,
            connector_score, connector_relations,
            judge_decision, judge_reasoning)
           VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)""",
        uuid.UUID(tenant_id),
        insight_content,
        uuid.UUID(source_conversation_id) if source_conversation_id else None,
        skeptic_result.get("score", 0.5),
        skeptic_result.get("reasoning", ""),
        connector_result.get("score", 0.5),
        json.dumps(connector_result.get("connections", [])),
        decision.get("decision", "provisional"),
        decision.get("reasoning", ""),
    )
