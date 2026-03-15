"""Socratic conversation engine with optimized parallel I/O routing."""

import asyncio
import uuid
from datetime import UTC, datetime

import structlog

from src.db import neo4j_client, postgres
from src.llm import llm_service
from src.llm.embeddings import embed
from src.models.conversation import ConversationState
from src.models.onboarding import BigFiveScores
from src.services import graph as graph_service
from src.services import knowledge as knowledge_service
from src.services import memory as memory_service
from src.services import permission as permission_service
from src.services.personality import generate_system_prompt

logger = structlog.get_logger(__name__)

PHASE_MAP = {
    1: "OPEN",
    2: "OPEN",
    3: "PROBE",
    4: "PROBE",
    5: "DEEPEN",
    6: "DEEPEN",
    7: "CHALLENGE",
    8: "CHALLENGE",
    9: "SYNTHESIZE",
    10: "EXTRACT",
}


async def run_socratic_debate(
    agent_a_id: str,
    agent_b_id: str,
    topic: str,
    tenant_id: str,
    background: bool = False,
    max_turns: int = 10,
) -> ConversationState:
    """Run a full Socratic debate between two agents."""
    conversation_id = str(uuid.uuid4())

    state: ConversationState = {
        "conversation_id": conversation_id,
        "agent_a_id": agent_a_id,
        "agent_b_id": agent_b_id,
        "tenant_id": tenant_id,
        "topic": topic,
        "current_speaker": agent_a_id,
        "messages": [],
        "turn_count": 0,
        "max_turns": max_turns,
        "phase": "OPEN",
        "relationship": {},
        "extracted_insights": [],
        "extracted_entities": [],
        "extracted_relations": [],
        "quality_score": 0.0,
        "background": background,
        "should_continue": True,
        "memories": [],
        "permission_ok": True,
        "system_prompt": "",
    }

    logger.info(
        "conversation_started",
        conversation_id=conversation_id,
        agent_a=agent_a_id,
        agent_b=agent_b_id,
        topic=topic,
    )

    while state["should_continue"] and state["turn_count"] < state["max_turns"]:
        state = await _run_turn(state)

    # Extract knowledge in the final phase
    state = await _extract_and_finalize(state)

    logger.info(
        "conversation_completed",
        conversation_id=conversation_id,
        turns=state["turn_count"],
        quality=state["quality_score"],
        insights=len(state["extracted_insights"]),
    )

    return state


async def _run_turn(state: ConversationState) -> ConversationState:
    """Execute a single conversation turn with optimized parallel I/O."""
    state["turn_count"] += 1
    state["phase"] = PHASE_MAP.get(state["turn_count"], "EXTRACT")

    speaker_id = state["current_speaker"]
    other_id = state["agent_b_id"] if speaker_id == state["agent_a_id"] else state["agent_a_id"]

    # Step 1: PARALLEL context retrieval (asyncio.gather)
    state = await _parallel_context(state, speaker_id, other_id)

    if not state["permission_ok"]:
        state["should_continue"] = False
        return state

    # Step 2: Build personality prompt
    state = await _inject_personality(state, speaker_id, other_id)

    # Step 3: Generate LLM response (single network call)
    response = await _generate_response(state)

    # Step 4: Record message
    message = {
        "speaker_agent_id": speaker_id,
        "content": response,
        "turn_number": state["turn_count"],
        "phase": state["phase"],
        "timestamp": datetime.now(UTC).isoformat(),
    }
    state["messages"].append(message)

    # Step 5: FIRE-AND-FORGET updates (don't block response)
    asyncio.create_task(_background_updates(state, speaker_id, other_id, response))

    # Step 6: Evaluate and swap speaker
    state = _evaluate_turn(state)
    state["current_speaker"] = other_id

    return state


async def _parallel_context(
    state: ConversationState, speaker_id: str, other_id: str
) -> ConversationState:
    """Fetch context in parallel: permissions + memory + relationship."""
    perm_task = permission_service.check_access(
        speaker_id, other_id, 1, "conversation", state["tenant_id"]
    )
    mem_task = _retrieve_memories_safe(speaker_id, state["tenant_id"], state["topic"])
    rel_task = _get_relationship_safe(speaker_id, other_id)

    permission_ok, memories, relationship = await asyncio.gather(perm_task, mem_task, rel_task)

    state["permission_ok"] = permission_ok
    state["memories"] = memories
    state["relationship"] = relationship or {}

    return state


async def _retrieve_memories_safe(agent_id: str, tenant_id: str, topic: str) -> list[str]:
    """Retrieve memories, returning empty on failure."""
    try:
        query_embedding = embed(topic)
        results = await memory_service.retrieve_memories(
            agent_id, tenant_id, query_embedding, limit=5
        )
        return [r["content"] for r in results]
    except Exception as e:
        logger.warning("memory_retrieval_failed", error=str(e))
        return []


async def _get_relationship_safe(agent_a_id: str, agent_b_id: str) -> dict | None:
    """Get relationship, returning None on failure."""
    try:
        return await graph_service.get_relationship(agent_a_id, agent_b_id)
    except Exception as e:
        logger.warning("relationship_fetch_failed", error=str(e))
        return None


async def _inject_personality(
    state: ConversationState, speaker_id: str, other_id: str
) -> ConversationState:
    """Build the personality-grounded system prompt."""
    agent = await _get_agent_data(speaker_id)
    other_agent = await _get_agent_data(other_id)

    if not agent or not other_agent:
        state["system_prompt"] = f"You are an AI agent debating: {state['topic']}"
        return state

    scores = BigFiveScores(
        openness=agent["openness"],
        conscientiousness=agent["conscientiousness"],
        extraversion=agent["extraversion"],
        agreeableness=agent["agreeableness"],
        neuroticism=agent["neuroticism"],
    )

    state["system_prompt"] = generate_system_prompt(
        agent_name=agent["display_name"],
        scores=scores,
        communication_style=agent.get("communication_style", "analytical"),
        interests=agent.get("interests", []),
        phase=state["phase"],
        other_agent_name=other_agent["display_name"],
        relationship=state["relationship"] or None,
        memories=state["memories"] or None,
    )

    return state


async def _generate_response(state: ConversationState) -> str:
    """Generate LLM response for the current turn."""
    messages = []
    for m in state["messages"][-6:]:
        is_speaker = m["speaker_agent_id"] == state["current_speaker"]
        role = "assistant" if is_speaker else "user"
        messages.append({"role": role, "content": m["content"]})

    if not messages:
        messages = [{"role": "user", "content": f"Let's discuss: {state['topic']}"}]

    trace_id = f"{state['conversation_id']}-turn-{state['turn_count']}"

    return await llm_service.generate(
        system_prompt=state["system_prompt"],
        messages=messages,
        trace_id=trace_id,
        temperature=0.7,
    )


async def _background_updates(
    state: ConversationState,
    speaker_id: str,
    other_id: str,
    response: str,
) -> None:
    """Fire-and-forget: update graph + store memory (runs after response)."""
    try:
        await asyncio.gather(
            graph_service.upsert_relationship(
                speaker_id,
                other_id,
                strength_delta=0.05,
                topics=[state["topic"]],
            ),
            _store_memory_safe(speaker_id, state["tenant_id"], response, state["topic"]),
        )
    except Exception as e:
        logger.warning("background_update_failed", error=str(e))


async def _store_memory_safe(agent_id: str, tenant_id: str, content: str, topic: str) -> None:
    """Store memory in hot tier, swallowing errors."""
    try:
        embedding = embed(content[:500])
        await memory_service.store_memory(
            agent_id=agent_id,
            tenant_id=tenant_id,
            content=f"[{topic}] {content[:500]}",
            embedding=embedding,
            memory_type="conversation_insight",
            importance=0.5,
        )
    except Exception as e:
        logger.warning("memory_store_failed", error=str(e))


def _evaluate_turn(state: ConversationState) -> ConversationState:
    """Decide whether to continue the conversation."""
    if state["turn_count"] >= state["max_turns"]:
        state["should_continue"] = False
    return state


async def _extract_and_finalize(state: ConversationState) -> ConversationState:
    """Extract knowledge and finalize the conversation."""
    if len(state["messages"]) < 2:
        state["quality_score"] = 0.0
        return state

    # Extract insights and entities
    try:
        transcript = "\n".join(
            f"{m['speaker_agent_id']}: {m['content']}" for m in state["messages"]
        )

        insights, entities, relations = await knowledge_service.extract_knowledge(
            transcript=transcript,
            topic=state["topic"],
            conversation_id=state["conversation_id"],
            tenant_id=state["tenant_id"],
        )

        state["extracted_insights"] = insights
        state["extracted_entities"] = entities
        state["extracted_relations"] = relations
    except Exception as e:
        logger.warning("knowledge_extraction_failed", error=str(e))

    # Quality score based on conversation depth
    state["quality_score"] = min(
        10.0, state["turn_count"] * 0.8 + len(state["extracted_insights"]) * 1.5
    )

    # Store conversation in Neo4j
    try:
        await _store_conversation_node(state)
    except Exception as e:
        logger.warning("conversation_store_failed", error=str(e))

    return state


async def _store_conversation_node(state: ConversationState) -> None:
    """Store the conversation as a node in Neo4j."""
    summary = state["messages"][-1]["content"][:200] if state["messages"] else ""

    await neo4j_client.execute_write(
        """CREATE (c:Conversation {
               id: $id,
               started_at: datetime(),
               turn_count: $turns,
               summary: $summary,
               quality_score: $quality,
               socratic_depth: $depth,
               background: $bg
           })
           WITH c
           MATCH (a:Agent {id: $a_id}), (b:Agent {id: $b_id})
           CREATE (a)-[:PARTICIPATED_IN {role: 'initiator'}]->(c)
           CREATE (b)-[:PARTICIPATED_IN {role: 'responder'}]->(c)""",
        id=state["conversation_id"],
        turns=state["turn_count"],
        summary=summary,
        quality=state["quality_score"],
        depth=state["phase"],
        bg=state["background"],
        a_id=state["agent_a_id"],
        b_id=state["agent_b_id"],
    )


async def _get_agent_data(agent_id: str) -> dict | None:
    """Fetch agent data from Postgres."""
    try:
        row = await postgres.fetchrow(
            "SELECT * FROM agents WHERE id = $1",
            uuid.UUID(agent_id),
        )
        return dict(row) if row else None
    except Exception:
        return None
