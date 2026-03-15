"""Conversation routes — trigger debates, get transcripts."""

from datetime import datetime

from fastapi import APIRouter, Depends

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
