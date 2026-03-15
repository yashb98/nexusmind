"""Conversation models — request/response, state, messages."""

from datetime import datetime
from typing import TypedDict

from pydantic import BaseModel, Field


class ConversationRequest(BaseModel):
    """Request to trigger a Socratic debate."""

    agent_a_id: str
    agent_b_id: str
    topic: str = Field(min_length=1, max_length=500)
    background: bool = False


class BroadcastRequest(BaseModel):
    """Broadcast a topic to an agent's connections."""

    agent_id: str
    topic: str = Field(min_length=1, max_length=500)


class Message(BaseModel):
    """A single conversation message."""

    speaker_agent_id: str
    content: str
    turn_number: int
    phase: str
    timestamp: datetime


class InsightOut(BaseModel):
    """Extracted insight from a conversation."""

    content: str
    importance: float
    bloom_relevance: int = 1


class EntityOut(BaseModel):
    """Extracted entity from a conversation."""

    name: str
    entity_type: str  # concept, technology, organization, person, claim
    description: str


class RelationOut(BaseModel):
    """Extracted entity relation."""

    source: str
    target: str
    relation_type: str  # CAUSES, CONTRADICTS, SUPPORTS, RELATES_TO
    confidence: float


class ConversationResponse(BaseModel):
    """Full conversation response."""

    id: str
    agent_a_id: str
    agent_b_id: str
    topic: str
    messages: list[Message]
    insights: list[InsightOut]
    entities: list[EntityOut]
    relations: list[RelationOut]
    quality_score: float
    phase_reached: str
    turn_count: int


class ConversationSummary(BaseModel):
    """Brief conversation summary for listing."""

    id: str
    agent_a_id: str
    agent_b_id: str
    topic: str
    turn_count: int
    quality_score: float
    phase_reached: str
    created_at: str


# LangGraph state
class ConversationState(TypedDict):
    """State for LangGraph Socratic conversation."""

    conversation_id: str
    agent_a_id: str
    agent_b_id: str
    tenant_id: str
    topic: str
    current_speaker: str
    messages: list[dict]
    turn_count: int
    max_turns: int
    phase: str
    relationship: dict
    extracted_insights: list[dict]
    extracted_entities: list[dict]
    extracted_relations: list[dict]
    quality_score: float
    background: bool
    should_continue: bool
    # Context fetched per turn
    memories: list[str]
    permission_ok: bool
    system_prompt: str
