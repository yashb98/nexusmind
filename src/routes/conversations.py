"""Conversation routes — trigger debates, get transcripts."""

import json
import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from src.models.conversation import (
    BroadcastRequest,
    ConversationRequest,
    ConversationResponse,
    EntityOut,
    InsightOut,
    Message,
    RelationOut,
)
from src.services import conversation as conv_service
from src.services import graph as graph_service
from src.db import postgres
from src.utils.auth import get_current_user

router = APIRouter(prefix="/api/v1/conversations", tags=["conversations"])


def _state_to_response(state: dict) -> ConversationResponse:
    """Convert conversation state to API response."""
    return ConversationResponse(
        id=state["conversation_id"],
        agent_a_id=state["agent_a_id"],
        agent_b_id=state["agent_b_id"],
        topic=state["topic"],
        messages=[
            Message(
                speaker_agent_id=m["speaker_agent_id"],
                content=m["content"],
                turn_number=m["turn_number"],
                phase=m["phase"],
                timestamp=datetime.fromisoformat(m["timestamp"]),
            )
            for m in state["messages"]
        ],
        insights=[
            InsightOut(
                content=i.get("content", ""),
                importance=i.get("importance", 0.5),
                bloom_relevance=i.get("bloom_relevance", 1),
            )
            for i in state.get("extracted_insights", [])
        ],
        entities=[
            EntityOut(
                name=e.get("name", ""),
                entity_type=e.get("type", "concept"),
                description=e.get("description", ""),
            )
            for e in state.get("extracted_entities", [])
        ],
        relations=[
            RelationOut(
                source=r.get("source", ""),
                target=r.get("target", ""),
                relation_type=r.get("type", "RELATES_TO"),
                confidence=r.get("confidence", 0.5),
            )
            for r in state.get("extracted_relations", [])
        ],
        quality_score=state.get("quality_score", 0.0),
        phase_reached=state.get("phase", "OPEN"),
        turn_count=state.get("turn_count", 0),
    )


@router.post("", response_model=ConversationResponse, status_code=201)
async def trigger_debate(
    req: ConversationRequest,
    current_user: dict = Depends(get_current_user),
) -> ConversationResponse:
    """Trigger a Socratic debate between two agents."""
    state = await conv_service.run_socratic_debate(
        agent_a_id=req.agent_a_id,
        agent_b_id=req.agent_b_id,
        topic=req.topic,
        tenant_id=current_user["tenant_id"],
        background=req.background,
    )
    return _state_to_response(state)


@router.post("/stream")
async def stream_debate(
    req: ConversationRequest,
    current_user: dict = Depends(get_current_user),
) -> StreamingResponse:
    """Stream a Socratic debate turn-by-turn via SSE.

    Each turn is sent as a Server-Sent Event with the agent's display name,
    message content, phase, and turn number so the frontend can render them
    live as they arrive.
    """

    async def _generate():
        # Look up display names for both agents
        row_a = await postgres.fetchrow(
            "SELECT display_name, lora_archetype FROM agents WHERE id = $1",
            uuid.UUID(req.agent_a_id),
        )
        row_b = await postgres.fetchrow(
            "SELECT display_name, lora_archetype FROM agents WHERE id = $1",
            uuid.UUID(req.agent_b_id),
        )
        name_a = row_a["display_name"] if row_a else req.agent_a_id
        name_b = row_b["display_name"] if row_b else req.agent_b_id
        archetype_a = row_a["lora_archetype"] if row_a else ""
        archetype_b = row_b["lora_archetype"] if row_b else ""

        # Send metadata event first
        yield _sse({
            "type": "meta",
            "agent_a": {"id": req.agent_a_id, "name": name_a, "archetype": archetype_a},
            "agent_b": {"id": req.agent_b_id, "name": name_b, "archetype": archetype_b},
            "topic": req.topic,
        })

        # Run debate turn-by-turn, streaming each message
        state = await conv_service.init_debate_state(
            agent_a_id=req.agent_a_id,
            agent_b_id=req.agent_b_id,
            topic=req.topic,
            tenant_id=current_user["tenant_id"],
            background=req.background,
        )

        while state["should_continue"] and state["turn_count"] < state["max_turns"]:
            state = await conv_service._run_turn(state)
            msg = state["messages"][-1]
            speaker_id = msg["speaker_agent_id"]
            speaker_name = name_a if speaker_id == req.agent_a_id else name_b

            yield _sse({
                "type": "turn",
                "turn": msg["turn_number"],
                "phase": msg["phase"],
                "speaker_id": speaker_id,
                "speaker": speaker_name,
                "content": msg["content"],
                "side": "left" if speaker_id == req.agent_a_id else "right",
            })

        # Finalize and send completion
        state = await conv_service._extract_and_finalize(state)
        yield _sse({
            "type": "done",
            "quality_score": state["quality_score"],
            "turn_count": state["turn_count"],
            "insights": [
                {"content": i.get("content", ""), "importance": i.get("importance", 0.5)}
                for i in state.get("extracted_insights", [])
            ],
        })

    return StreamingResponse(
        _generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


def _sse(data: dict) -> str:
    """Format a dict as an SSE event."""
    return f"data: {json.dumps(data)}\n\n"


@router.post("/broadcast", response_model=list[ConversationResponse])
async def broadcast(
    req: BroadcastRequest,
    current_user: dict = Depends(get_current_user),
) -> list[ConversationResponse]:
    """Broadcast a topic to an agent's top 3 connections."""
    recommendations = await graph_service.find_similar_agents(
        req.agent_id, current_user["tenant_id"], limit=3
    )

    results = []
    for rec in recommendations:
        state = await conv_service.run_socratic_debate(
            agent_a_id=req.agent_id,
            agent_b_id=rec["id"],
            topic=req.topic,
            tenant_id=current_user["tenant_id"],
        )
        results.append(_state_to_response(state))

    return results
