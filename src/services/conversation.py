"""Socratic conversation engine with optimized parallel I/O routing."""

import asyncio
import random
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

MODE_PHASES = {
    "socratic": ["OPEN", "PROBE", "DEEPEN", "CHALLENGE", "SYNTHESIZE", "EXTRACT"],
    "casual": ["CHAT"],
    "brainstorm": ["SEED", "BUILD", "COMBINE", "REFINE"],
    "teach": ["INTRODUCE", "EXPLAIN", "CHECK", "DEEPEN", "ASSESS"],
    "research": ["SCOPE", "DIVIDE", "INVESTIGATE", "SHARE", "SYNTHESIZE"],
    "play": ["SETUP", "PLAY", "PLAY", "PLAY", "REFLECT"],
    "project": ["GOAL", "PLAN", "WORK", "REVIEW", "DELIVER"],
    "reflection": ["PROMPT", "EXPLORE", "PATTERN", "INSIGHT"],
}

MODE_TURN_LIMITS = {
    "casual": 20,
    "socratic": 10,
    "brainstorm": 15,
    "teach": 12,
    "research": 15,
    "play": 20,
    "project": 30,
    "reflection": 10,
}

MODE_PROMPTS = {
    "casual": (
        "Have a natural conversation. Be yourself. No need to debate or challenge. "
        "Build rapport."
    ),
    "socratic": "",  # uses existing phase instructions
    "brainstorm": (
        "Build on each other's ideas. Never dismiss. Say 'yes, and...' not 'but'. "
        "Generate as many ideas as possible. Combine unexpected concepts."
    ),
    "teach": (
        "You are in a teaching conversation. If you have more knowledge on this topic, "
        "explain clearly using analogies. If learning, ask questions and rephrase in "
        "your own words."
    ),
    "research": (
        "You're investigating this topic together. Divide the work. Share what you find. "
        "Synthesize findings. Be systematic."
    ),
    "play": (
        "You're playing a collaborative thinking game. Be creative, spontaneous, and fun. "
        "Enjoy the interaction."
    ),
    "project": (
        "You're working toward a shared goal. Stay focused on deliverables. Divide tasks. "
        "Track progress. Be constructive."
    ),
    "reflection": (
        "Think out loud about this topic. Be honest about what you've learned and how your "
        "thinking has changed. The other agent should listen actively and ask gentle guiding "
        "questions."
    ),
}


def select_conversation_mode(trust_level: float, context: dict | None = None) -> str:
    """Auto-select conversation mode based on context and trust level.

    Args:
        trust_level: Trust score between 0.0 and 1.0.
        context: Optional dict with keys like ``user_selected_mode`` or ``event_type``.

    Returns:
        One of the eight conversation mode strings.
    """
    ctx = context or {}
    if ctx.get("user_selected_mode"):
        return ctx["user_selected_mode"]
    if ctx.get("event_type") == "hackathon":
        return "project"
    if ctx.get("event_type") == "game_night":
        return "play"
    if ctx.get("event_type") == "research_sprint":
        return "research"
    if ctx.get("event_type") == "debate_tournament":
        return "socratic"
    if trust_level < 0.2:
        return random.choice(["casual", "play"])
    if trust_level < 0.4:
        return random.choice(["casual", "play", "teach", "brainstorm"])
    return random.choices(
        ["casual", "socratic", "brainstorm", "teach", "research", "play", "reflection"],
        weights=[0.2, 0.25, 0.15, 0.15, 0.1, 0.1, 0.05],
    )[0]


async def init_debate_state(
    agent_a_id: str,
    agent_b_id: str,
    topic: str,
    tenant_id: str,
    background: bool = False,
    max_turns: int = 10,
    mode: str = "socratic",
) -> ConversationState:
    """Initialize debate state without running turns (for streaming)."""
    conversation_id = str(uuid.uuid4())
    effective_max = MODE_TURN_LIMITS.get(mode, max_turns)

    state: ConversationState = {
        "conversation_id": conversation_id,
        "agent_a_id": agent_a_id,
        "agent_b_id": agent_b_id,
        "tenant_id": tenant_id,
        "topic": topic,
        "current_speaker": agent_a_id,
        "messages": [],
        "turn_count": 0,
        "max_turns": effective_max,
        "phase": "OPEN",
        "relationship": {},
        "extracted_insights": [],
        "extracted_entities": [],
        "extracted_relations": [],
        "quality_score": 0.0,
        "background": background,
        "should_continue": True,
        "mode": mode,
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

    return state


async def run_socratic_debate(
    agent_a_id: str,
    agent_b_id: str,
    topic: str,
    tenant_id: str,
    background: bool = False,
    max_turns: int = 10,
    mode: str = "socratic",
) -> ConversationState:
    """Run a full Socratic debate between two agents."""
    conversation_id = str(uuid.uuid4())
    effective_max = MODE_TURN_LIMITS.get(mode, max_turns)

    state: ConversationState = {
        "conversation_id": conversation_id,
        "agent_a_id": agent_a_id,
        "agent_b_id": agent_b_id,
        "tenant_id": tenant_id,
        "topic": topic,
        "current_speaker": agent_a_id,
        "messages": [],
        "turn_count": 0,
        "max_turns": effective_max,
        "phase": "OPEN",
        "relationship": {},
        "extracted_insights": [],
        "extracted_entities": [],
        "extracted_relations": [],
        "quality_score": 0.0,
        "background": background,
        "should_continue": True,
        "mode": mode,
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
    mode = state.get("mode", "socratic")
    if mode == "socratic":
        state["phase"] = PHASE_MAP.get(state["turn_count"], "EXTRACT")
    else:
        phases = MODE_PHASES.get(mode, ["CHAT"])
        turns_per_phase = max(1, state["max_turns"] // len(phases))
        phase_index = min(state["turn_count"] // turns_per_phase, len(phases) - 1)
        state["phase"] = phases[phase_index]

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

    # Resolve domain modifiers for the conversation topic
    agent_domain_mods = agent.get("domain_modifiers") or {}
    topic_domain_mods = _resolve_topic_domain_mods(state["topic"], agent.get("interests", []), agent_domain_mods)

    state["system_prompt"] = generate_system_prompt(
        agent_name=agent["display_name"],
        scores=scores,
        communication_style=agent.get("communication_style", "analytical"),
        interests=agent.get("interests", []),
        phase=state["phase"],
        other_agent_name=other_agent["display_name"],
        relationship=state["relationship"] or None,
        memories=state["memories"] or None,
        domain_modifiers=topic_domain_mods,
    )

    mode = state.get("mode", "socratic")
    mode_prompt = MODE_PROMPTS.get(mode, "")
    if mode_prompt:
        state["system_prompt"] += f"\n\nMODE: {mode.upper()}\n{mode_prompt}"

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


# ---------------------------------------------------------------------------
# Embedded tutor commentary
# ---------------------------------------------------------------------------

TUTOR_PROMPT_TEMPLATE = """You are a Socratic tutor helping a learner understand a live debate about "{topic}".

LATEST MESSAGE: "{latest_message}" — said during {phase} phase

YOUR MODE: {tutor_mode}

MODE INSTRUCTIONS:
- explain: The agent used a concept the learner may not know. Explain it simply in 1-2 sentences. Then ask ONE question to check understanding.
- check: A debatable point was raised. Ask the learner what THEY think about it. Don't explain — test their reasoning.
- reflect: The debate is wrapping up. Ask the learner for their own position on the topic. Push them to synthesize what they heard.
- observe: Nothing requires intervention. Give a brief 1-sentence note about what's happening in the debate.

RULES:
1. Keep it SHORT. 1-3 sentences max. The debate is the main show — you're the commentary.
2. NEVER spoil what's coming in the debate. Only comment on what already happened.
3. NEVER say "wrong." If learner is incorrect, ask a guiding question.
4. Be warm and encouraging. Use casual tone."""


def _select_tutor_mode(phase: str, turn_count: int, total_turns: int) -> str:
    """Select tutor mode based on conversation phase and progress."""
    if phase in ("SYNTHESIZE", "EXTRACT", "INSIGHT", "REFLECT", "DELIVER"):
        return "reflect"
    if phase in ("CHALLENGE", "PROBE", "CHECK"):
        return "check"
    if turn_count <= 2:
        return "explain"
    # Default to observe for most turns to avoid being annoying
    return "observe" if turn_count % 3 != 0 else "explain"


async def generate_tutor_commentary(state: ConversationState) -> dict | None:
    """Generate tutor commentary for the latest turn.

    Returns None for background conversations.
    """
    if state.get("background", True):
        return None

    if not state["messages"]:
        return None

    latest = state["messages"][-1]
    mode = _select_tutor_mode(
        state["phase"], state["turn_count"], state["max_turns"],
    )

    prompt = TUTOR_PROMPT_TEMPLATE.format(
        topic=state["topic"],
        latest_message=latest["content"][:500],
        phase=state["phase"],
        tutor_mode=mode,
    )

    try:
        tutor_response = await llm_service.generate(
            system_prompt=prompt,
            messages=[],
            trace_id=f"{state['conversation_id']}-tutor-{state['turn_count']}",
            temperature=0.6,
        )
        return {
            "type": "tutor",
            "mode": mode,
            "content": tutor_response,
            "turn": state["turn_count"],
        }
    except Exception as e:
        logger.warning("tutor_generation_failed", error=str(e))
        return None


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

    # Update trust based on conversation quality
    try:
        trust_delta = 0.0
        mode = state.get("mode", "socratic")
        if state["quality_score"] > 3.5:
            trust_delta += 0.05
        if state["extracted_insights"]:
            trust_delta += 0.03
        challenge_turns = [m for m in state["messages"] if m.get("phase") in ("CHALLENGE", "CHECK")]
        if len(challenge_turns) >= 2:
            trust_delta += 0.02
        if mode == "play":
            trust_delta += 0.08
        if trust_delta > 0:
            await graph_service.update_trust(
                state["agent_a_id"], state["agent_b_id"], trust_delta
            )
            logger.info("trust_updated", delta=trust_delta, mode=mode)
    except Exception as e:
        logger.warning("trust_update_failed", error=str(e))

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
               mode: $mode,
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
        mode=state.get("mode", "socratic"),
        bg=state["background"],
        a_id=state["agent_a_id"],
        b_id=state["agent_b_id"],
    )


def _resolve_topic_domain_mods(
    topic: str, interests: list[str], domain_modifiers: dict
) -> dict[str, float] | None:
    """Find domain modifiers matching the conversation topic."""
    topic_lower = topic.lower()
    for interest in interests:
        if interest.lower() in topic_lower or topic_lower in interest.lower():
            mods = domain_modifiers.get(interest)
            if mods:
                return mods
    return None


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
