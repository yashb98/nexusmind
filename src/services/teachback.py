"""Teach-back service — Bloom-adapted Socratic tutoring."""

import uuid

import structlog

from src.db import postgres
from src.llm import llm_service

logger = structlog.get_logger(__name__)

BLOOM_INSTRUCTIONS = {
    1: "The learner is at REMEMBER level. Ask simple recall questions.",
    2: "The learner is at UNDERSTAND level. Ask them to explain in their own words.",
    3: "The learner is at APPLY level. Ask how they would apply this concept.",
    4: "The learner is at ANALYZE level. Ask them to compare, contrast, or break down.",
    5: "The learner is at EVALUATE level. Ask them to critique or judge.",
    6: "The learner is at CREATE level. Ask them to design or propose something new.",
}

TUTOR_PROMPT = """You are a Socratic tutor helping {user_name} understand: "{insight}"

LEARNER'S LEVEL: Bloom Level {bloom_level} on "{topic}"
{bloom_instructions}

RULES:
1. NEVER give direct answers. Guide through questions.
2. If wrong: DON'T say "wrong." Ask "What if we considered...?"
3. If right: acknowledge specifically WHAT was right, then increase difficulty.
4. Keep responses 2-3 sentences. Ask exactly ONE question per turn.
5. After 3-5 turns, assess if learner has leveled up.
6. Weave any research naturally (never dump raw data)."""


async def start_session(user_id: str, insight_id: str, insight_content: str, topic: str) -> dict:
    """Start a teach-back session."""
    session_id = str(uuid.uuid4())

    # Get or create learner knowledge
    knowledge = await _get_or_create_knowledge(user_id, topic)
    bloom_level = knowledge.get("bloom_level", 1)

    # Create session record
    await postgres.execute(
        """INSERT INTO teachback_sessions
           (id, user_id, insight_id, topic, bloom_level_start, status)
           VALUES ($1, $2, $3, $4, $5, 'active')""",
        uuid.UUID(session_id),
        uuid.UUID(user_id),
        insight_id,
        topic,
        bloom_level,
    )

    # Generate opening question
    opening = await _generate_tutor_message(
        user_name="learner",
        insight=insight_content,
        topic=topic,
        bloom_level=bloom_level,
        history=[],
    )

    logger.info("teachback_started", session_id=session_id, bloom=bloom_level)
    return {
        "session_id": session_id,
        "topic": topic,
        "bloom_level": bloom_level,
        "tutor_message": opening,
    }


async def process_response(session_id: str, learner_message: str) -> dict:
    """Process learner's response and generate next tutor turn."""
    session = await _get_session(session_id)
    if not session:
        return {"error": "Session not found"}

    # Increment turn count
    turns = (session.get("turns") or 0) + 1
    await postgres.execute(
        "UPDATE teachback_sessions SET turns = $1 WHERE id = $2",
        turns,
        uuid.UUID(session_id),
    )

    # Generate tutor response
    history = [{"role": "user", "content": learner_message}]
    tutor_response = await _generate_tutor_message(
        user_name="learner",
        insight=session.get("insight_id", ""),
        topic=session["topic"],
        bloom_level=session.get("bloom_level_start") or 1,
        history=history,
    )

    result = {
        "session_id": session_id,
        "tutor_message": tutor_response,
        "turn": turns,
    }

    # After 3-5 turns, assess level up
    if turns >= 3:
        result["assessment_available"] = True

    return result


async def complete_session(session_id: str) -> dict:
    """Complete a teach-back session and assess Bloom level change."""
    session = await _get_session(session_id)
    if not session:
        return {"error": "Session not found"}

    bloom_start = session.get("bloom_level_start") or 1
    # Simple heuristic: level up if >= 3 turns completed
    turns = session.get("turns") or 0
    bloom_end = min(6, bloom_start + (1 if turns >= 3 else 0))

    # Update session
    await postgres.execute(
        """UPDATE teachback_sessions
           SET bloom_level_end = $1, status = 'completed', ended_at = NOW()
           WHERE id = $2""",
        bloom_end,
        uuid.UUID(session_id),
    )

    # Update learner knowledge
    if bloom_end > bloom_start and session.get("user_id"):
        await postgres.execute(
            """UPDATE learner_knowledge
               SET bloom_level = $1, last_assessed = NOW()
               WHERE user_id = $2 AND topic = $3""",
            bloom_end,
            session["user_id"],
            session["topic"],
        )

    logger.info(
        "teachback_completed",
        session_id=session_id,
        bloom_start=bloom_start,
        bloom_end=bloom_end,
    )

    return {
        "session_id": session_id,
        "bloom_level_start": bloom_start,
        "bloom_level_end": bloom_end,
        "leveled_up": bloom_end > bloom_start,
        "turns": turns,
    }


async def _generate_tutor_message(
    user_name: str,
    insight: str,
    topic: str,
    bloom_level: int,
    history: list[dict],
) -> str:
    """Generate a Socratic tutor response."""
    bloom_instructions = BLOOM_INSTRUCTIONS.get(bloom_level, BLOOM_INSTRUCTIONS[1])

    system_prompt = TUTOR_PROMPT.format(
        user_name=user_name,
        insight=insight,
        topic=topic,
        bloom_level=bloom_level,
        bloom_instructions=bloom_instructions,
    )

    if not history:
        history = [{"role": "user", "content": f"I want to learn about: {topic}"}]

    return await llm_service.generate(
        system_prompt=system_prompt,
        messages=history,
        trace_id=f"teachback-{uuid.uuid4()}",
        temperature=0.7,
        max_tokens=256,
    )


async def _get_or_create_knowledge(user_id: str, topic: str) -> dict:
    """Get or create learner knowledge record."""
    row = await postgres.fetchrow(
        "SELECT * FROM learner_knowledge WHERE user_id = $1 AND topic = $2",
        uuid.UUID(user_id),
        topic,
    )
    if row:
        return dict(row)

    await postgres.execute(
        """INSERT INTO learner_knowledge (user_id, topic, bloom_level)
           VALUES ($1, $2, 1)""",
        uuid.UUID(user_id),
        topic,
    )
    return {"bloom_level": 1, "confidence": 0.0}


async def _get_session(session_id: str) -> dict | None:
    """Get a teach-back session."""
    row = await postgres.fetchrow(
        "SELECT * FROM teachback_sessions WHERE id = $1",
        uuid.UUID(session_id),
    )
    return dict(row) if row else None
