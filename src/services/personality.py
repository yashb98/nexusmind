"""Personality service — scoring, archetypes, prompt generation."""

import math

from src.models.onboarding import (
    BigFiveScores,
    PersonalityResult,
    ScenarioAnswer,
    ScenarioOption,
    ScenarioQuestion,
)

PERSONALITY_SCENARIOS: list[ScenarioQuestion] = [
    ScenarioQuestion(
        id=1,
        scenario="Someone shares an idea you disagree with. You...",
        options=[
            ScenarioOption(
                text="Challenge them directly with evidence",
                scores={"agreeableness": -0.3, "extraversion": 0.2},
            ),
            ScenarioOption(
                text="Ask questions to understand their reasoning",
                scores={"openness": 0.3, "conscientiousness": 0.1},
            ),
            ScenarioOption(
                text="Find common ground first",
                scores={"agreeableness": 0.3},
            ),
            ScenarioOption(
                text="Move on — not worth debating",
                scores={"openness": -0.2, "extraversion": -0.2},
            ),
        ],
    ),
    ScenarioQuestion(
        id=2,
        scenario="You're starting a new project. Your first instinct is to...",
        options=[
            ScenarioOption(
                text="Create a detailed plan and timeline",
                scores={"conscientiousness": 0.3},
            ),
            ScenarioOption(
                text="Brainstorm creative approaches first",
                scores={"openness": 0.3},
            ),
            ScenarioOption(
                text="Talk to others about their experiences",
                scores={"extraversion": 0.3, "agreeableness": 0.1},
            ),
            ScenarioOption(
                text="Just start and figure it out as you go",
                scores={"conscientiousness": -0.2, "openness": 0.1},
            ),
        ],
    ),
    ScenarioQuestion(
        id=3,
        scenario="At a networking event, you typically...",
        options=[
            ScenarioOption(
                text="Work the room, meet as many people as possible",
                scores={"extraversion": 0.3},
            ),
            ScenarioOption(
                text="Find one or two people for deep conversation",
                scores={"openness": 0.2, "extraversion": -0.1},
            ),
            ScenarioOption(
                text="Listen more than you talk, observe the group",
                scores={"neuroticism": 0.1, "extraversion": -0.2},
            ),
            ScenarioOption(
                text="Look for people who share your specific interests",
                scores={"conscientiousness": 0.2, "openness": 0.1},
            ),
        ],
    ),
    ScenarioQuestion(
        id=4,
        scenario="When you receive critical feedback, your first reaction is to...",
        options=[
            ScenarioOption(
                text="Analyze it objectively and extract useful parts",
                scores={"conscientiousness": 0.2, "neuroticism": -0.2},
            ),
            ScenarioOption(
                text="Feel hurt but try to learn from it",
                scores={"neuroticism": 0.3, "agreeableness": 0.1},
            ),
            ScenarioOption(
                text="Push back if you think it's unfair",
                scores={"agreeableness": -0.2, "extraversion": 0.2},
            ),
            ScenarioOption(
                text="Seek more perspectives before deciding",
                scores={"openness": 0.2, "conscientiousness": 0.1},
            ),
        ],
    ),
    ScenarioQuestion(
        id=5,
        scenario="You discover a flaw in a popular theory. You...",
        options=[
            ScenarioOption(
                text="Publish your counter-argument immediately",
                scores={"extraversion": 0.2, "openness": 0.2},
            ),
            ScenarioOption(
                text="Research extensively before saying anything",
                scores={"conscientiousness": 0.3, "neuroticism": 0.1},
            ),
            ScenarioOption(
                text="Discuss it with trusted colleagues first",
                scores={"agreeableness": 0.2, "extraversion": 0.1},
            ),
            ScenarioOption(
                text="Consider whether the flaw actually matters",
                scores={"openness": -0.1, "agreeableness": 0.2},
            ),
        ],
    ),
    ScenarioQuestion(
        id=6,
        scenario="Your team is stuck on a problem. You suggest...",
        options=[
            ScenarioOption(
                text="A completely unconventional approach",
                scores={"openness": 0.3, "conscientiousness": -0.1},
            ),
            ScenarioOption(
                text="Breaking it down into smaller, manageable parts",
                scores={"conscientiousness": 0.3},
            ),
            ScenarioOption(
                text="Getting everyone's input before deciding",
                scores={"agreeableness": 0.2, "extraversion": 0.1},
            ),
            ScenarioOption(
                text="Taking a break and coming back with fresh eyes",
                scores={"neuroticism": -0.2, "openness": 0.1},
            ),
        ],
    ),
    ScenarioQuestion(
        id=7,
        scenario="When learning something new, you prefer to...",
        options=[
            ScenarioOption(
                text="Dive into the theory and understand the 'why'",
                scores={"openness": 0.3, "conscientiousness": 0.1},
            ),
            ScenarioOption(
                text="Get hands-on practice immediately",
                scores={"extraversion": 0.1, "conscientiousness": -0.1},
            ),
            ScenarioOption(
                text="Learn from others who've done it before",
                scores={"agreeableness": 0.2, "extraversion": 0.1},
            ),
            ScenarioOption(
                text="Follow a structured curriculum step by step",
                scores={"conscientiousness": 0.3, "openness": -0.1},
            ),
        ],
    ),
    ScenarioQuestion(
        id=8,
        scenario="Under pressure with a tight deadline, you...",
        options=[
            ScenarioOption(
                text="Thrive — pressure brings out your best work",
                scores={"neuroticism": -0.3, "extraversion": 0.1},
            ),
            ScenarioOption(
                text="Get anxious but push through methodically",
                scores={"neuroticism": 0.2, "conscientiousness": 0.2},
            ),
            ScenarioOption(
                text="Delegate and coordinate with the team",
                scores={"extraversion": 0.2, "agreeableness": 0.1},
            ),
            ScenarioOption(
                text="Focus on what's essential, cut the rest",
                scores={"conscientiousness": 0.1, "neuroticism": -0.1},
            ),
        ],
    ),
    ScenarioQuestion(
        id=9,
        scenario="In a group discussion, you notice someone being talked over. You...",
        options=[
            ScenarioOption(
                text="Directly ask the group to let them finish",
                scores={"extraversion": 0.2, "agreeableness": 0.2},
            ),
            ScenarioOption(
                text="Privately check in with them afterward",
                scores={"agreeableness": 0.3, "extraversion": -0.1},
            ),
            ScenarioOption(
                text="Note it but don't intervene — it's not your place",
                scores={"agreeableness": -0.1, "neuroticism": 0.1},
            ),
            ScenarioOption(
                text="Redirect the conversation to include their point",
                scores={"openness": 0.1, "agreeableness": 0.2},
            ),
        ],
    ),
    ScenarioQuestion(
        id=10,
        scenario="You have a free weekend with no obligations. You...",
        options=[
            ScenarioOption(
                text="Explore a new hobby or visit somewhere unfamiliar",
                scores={"openness": 0.3, "extraversion": 0.1},
            ),
            ScenarioOption(
                text="Catch up on a personal project you've been planning",
                scores={"conscientiousness": 0.3},
            ),
            ScenarioOption(
                text="Spend time with friends or family",
                scores={"extraversion": 0.2, "agreeableness": 0.2},
            ),
            ScenarioOption(
                text="Recharge alone — read, rest, reflect",
                scores={"extraversion": -0.3, "neuroticism": 0.1},
            ),
        ],
    ),
]

ARCHETYPES = {
    "The Investigator": {
        "openness": 0.8,
        "conscientiousness": 0.7,
        "extraversion": 0.3,
        "agreeableness": 0.4,
        "neuroticism": 0.4,
    },
    "The Diplomat": {
        "openness": 0.6,
        "conscientiousness": 0.5,
        "extraversion": 0.6,
        "agreeableness": 0.9,
        "neuroticism": 0.3,
    },
    "The Commander": {
        "openness": 0.5,
        "conscientiousness": 0.8,
        "extraversion": 0.8,
        "agreeableness": 0.3,
        "neuroticism": 0.2,
    },
    "The Innovator": {
        "openness": 0.9,
        "conscientiousness": 0.4,
        "extraversion": 0.6,
        "agreeableness": 0.5,
        "neuroticism": 0.5,
    },
    "The Guardian": {
        "openness": 0.3,
        "conscientiousness": 0.9,
        "extraversion": 0.4,
        "agreeableness": 0.7,
        "neuroticism": 0.5,
    },
    "The Maverick": {
        "openness": 0.7,
        "conscientiousness": 0.3,
        "extraversion": 0.7,
        "agreeableness": 0.4,
        "neuroticism": 0.6,
    },
}

TRAIT_DESCRIPTIONS = {
    "openness": {
        "high": "intellectually curious, open to new ideas and experiences",
        "mid": "balanced between tradition and novelty",
        "low": "practical, prefers proven approaches",
    },
    "conscientiousness": {
        "high": "organized, detail-oriented, and methodical",
        "mid": "flexible but can be structured when needed",
        "low": "spontaneous, adaptable, prefers flexibility",
    },
    "extraversion": {
        "high": "energized by social interaction, outgoing",
        "mid": "comfortable in both social and solitary settings",
        "low": "reflective, prefers deep one-on-one conversations",
    },
    "agreeableness": {
        "high": "cooperative, empathetic, harmony-seeking",
        "mid": "balances assertiveness with cooperation",
        "low": "direct, challenging, prioritizes truth over harmony",
    },
    "neuroticism": {
        "high": "emotionally sensitive, deeply processing",
        "mid": "emotionally balanced with occasional intensity",
        "low": "calm under pressure, emotionally stable",
    },
}


def get_scenarios() -> list[ScenarioQuestion]:
    """Return the 10 scenario-based personality questions."""
    return PERSONALITY_SCENARIOS


def score_personality(answers: list[ScenarioAnswer]) -> BigFiveScores:
    """Score Big Five traits from scenario answers, normalized to 0-1."""
    raw: dict[str, float] = {
        "openness": 0.0,
        "conscientiousness": 0.0,
        "extraversion": 0.0,
        "agreeableness": 0.0,
        "neuroticism": 0.0,
    }

    scenarios_by_id = {s.id: s for s in PERSONALITY_SCENARIOS}

    for answer in answers:
        scenario = scenarios_by_id.get(answer.question_id)
        if not scenario or answer.option_index >= len(scenario.options):
            continue
        option = scenario.options[answer.option_index]
        for trait, delta in option.scores.items():
            if trait in raw:
                raw[trait] += delta

    # Normalize: theoretical range per trait is roughly -0.9 to +0.9
    # Map to 0-1 with 0.5 as neutral
    for trait in raw:
        raw[trait] = max(0.0, min(1.0, 0.5 + raw[trait]))

    return BigFiveScores(**raw)


def compute_communication_style(scores: BigFiveScores) -> str:
    """Derive communication style from Big Five scores."""
    assertive = scores.extraversion + (1 - scores.agreeableness)
    responsive = scores.agreeableness + scores.extraversion

    if assertive >= 1.0 and responsive >= 1.0:
        return "expressive"
    elif assertive >= 1.0:
        return "driver"
    elif responsive >= 1.0:
        return "amiable"
    return "analytical"


def assign_archetype(scores: BigFiveScores) -> str:
    """Find nearest archetype by Euclidean distance."""
    scores_vec = [
        scores.openness,
        scores.conscientiousness,
        scores.extraversion,
        scores.agreeableness,
        scores.neuroticism,
    ]

    best_name = "The Investigator"
    best_dist = float("inf")

    for name, proto in ARCHETYPES.items():
        proto_vec = [
            proto["openness"],
            proto["conscientiousness"],
            proto["extraversion"],
            proto["agreeableness"],
            proto["neuroticism"],
        ]
        dist = math.sqrt(sum((a - b) ** 2 for a, b in zip(scores_vec, proto_vec)))
        if dist < best_dist:
            best_dist = dist
            best_name = name

    return best_name


def _trait_level(value: float) -> str:
    """Classify trait value as high/mid/low."""
    if value >= 0.65:
        return "high"
    if value <= 0.35:
        return "low"
    return "mid"


def generate_description(scores: BigFiveScores, archetype: str) -> str:
    """Generate a natural language personality description."""
    traits = []
    for trait_name, value in [
        ("openness", scores.openness),
        ("conscientiousness", scores.conscientiousness),
        ("extraversion", scores.extraversion),
        ("agreeableness", scores.agreeableness),
        ("neuroticism", scores.neuroticism),
    ]:
        level = _trait_level(value)
        desc = TRAIT_DESCRIPTIONS[trait_name][level]
        traits.append(desc)

    return (
        f"Archetype: {archetype}. "
        f"This agent is {traits[0]}, {traits[1]}, and {traits[2]}. "
        f"In interactions, they are {traits[3]} and {traits[4]}."
    )


def compute_personality_result(answers: list[ScenarioAnswer]) -> PersonalityResult:
    """Full pipeline: answers → scores → archetype → style → description."""
    scores = score_personality(answers)
    style = compute_communication_style(scores)
    archetype = assign_archetype(scores)
    description = generate_description(scores, archetype)
    return PersonalityResult(
        scores=scores,
        archetype=archetype,
        communication_style=style,
        description=description,
    )


def compute_trust_modifier(trust_level: float) -> float:
    """Convert trust level (0-1) to personality expression multiplier."""
    if trust_level <= 0.2:
        return 0.3
    elif trust_level <= 0.5:
        return 0.3 + (trust_level - 0.2) * (0.6 - 0.3) / (0.5 - 0.2)
    elif trust_level <= 0.8:
        return 0.6 + (trust_level - 0.5) * (0.85 - 0.6) / (0.8 - 0.5)
    else:
        return 0.85 + (trust_level - 0.8) * (1.0 - 0.85) / (1.0 - 0.8)


def compute_effective_personality(
    base_big_five: dict[str, float],
    trust_level: float,
) -> dict[str, float]:
    """Apply trust modifier to base personality."""
    modifier = compute_trust_modifier(trust_level)
    return {trait: value * modifier for trait, value in base_big_five.items()}


def get_trust_label(trust_level: float) -> str:
    """Human-readable trust label for prompts."""
    if trust_level < 0.2:
        return "stranger"
    elif trust_level < 0.5:
        return "acquaintance"
    elif trust_level < 0.8:
        return "colleague"
    else:
        return "trusted"


def trust_derived_permission(trust_level: float) -> int:
    """Auto-derive permission level from trust. Users can override."""
    if trust_level < 0.2:
        return 0
    elif trust_level < 0.4:
        return 1
    elif trust_level < 0.6:
        return 2
    elif trust_level < 0.8:
        return 3
    else:
        return 4


def generate_system_prompt(
    agent_name: str,
    scores: BigFiveScores,
    communication_style: str,
    interests: list[str],
    phase: str,
    other_agent_name: str,
    relationship: dict | None = None,
    memories: list[str] | None = None,
) -> str:
    """Generate a personality-grounded system prompt for conversations."""
    trait_lines = []
    for trait_name, value in [
        ("Openness", scores.openness),
        ("Conscientiousness", scores.conscientiousness),
        ("Extraversion", scores.extraversion),
        ("Agreeableness", scores.agreeableness),
        ("Neuroticism", scores.neuroticism),
    ]:
        level = _trait_level(value)
        desc_key = trait_name.lower()
        desc = TRAIT_DESCRIPTIONS[desc_key][level]
        trait_lines.append(f"- {trait_name}: {value:.2f} → {desc}")

    phase_instructions = _get_phase_instructions(phase)
    rel_str = _format_relationship(other_agent_name, relationship)
    mem_str = _format_memories(memories)

    return (
        f"You are {agent_name}, an AI agent in a Socratic debate.\n\n"
        f"PERSONALITY (Big Five 0-1):\n"
        + "\n".join(trait_lines)
        + f"\n\nINTERESTS: {', '.join(interests)}\n"
        f"STYLE: {communication_style}\n"
        f"PHASE: {phase}\n\n"
        f"{phase_instructions}\n\n"
        f"{rel_str}\n\n"
        f"{mem_str}\n\n"
        "RULES:\n"
        "1. Stay in character. Personality MUST be consistent.\n"
        "2. NEVER give a simple answer. Always probe, question, or challenge.\n"
        "3. Reference memories naturally (don't list them).\n"
        "4. Keep responses 2-4 sentences. Conversational, not formal.\n"
        "5. If you discover something new, express genuine curiosity.\n"
        "6. NEVER break character or mention you are an AI."
    )


def compute_compatibility(a: BigFiveScores, b: BigFiveScores) -> float:
    """Compute compatibility score (0-1) between two agents."""
    # Complementary traits: some opposition is good for debate
    diff = math.sqrt(
        (a.openness - b.openness) ** 2
        + (a.conscientiousness - b.conscientiousness) ** 2
        + (a.extraversion - b.extraversion) ** 2
        + (a.agreeableness - b.agreeableness) ** 2
        + (a.neuroticism - b.neuroticism) ** 2
    )
    max_dist = math.sqrt(5)  # max possible distance
    similarity = 1 - (diff / max_dist)
    # Optimal compatibility is moderate similarity (~0.5-0.7)
    return min(1.0, similarity * 1.3)


def _get_phase_instructions(phase: str) -> str:
    """Get instructions for the current conversation phase."""
    instructions = {
        "OPEN": (
            "Introduce your perspective on the topic. "
            "Share your initial thoughts grounded in your personality."
        ),
        "PROBE": (
            "Ask Socratic questions. 'Why do you think that?' 'What evidence supports this?'"
        ),
        "DEEPEN": (
            "Elaborate on your position. Retrieve relevant memories. Cite sources if available."
        ),
        "CHALLENGE": (
            "Present counter-perspectives. Identify assumptions. Push back constructively."
        ),
        "SYNTHESIZE": ("Find common ground or articulate the core disagreement clearly."),
        "EXTRACT": ("Summarize key insights discovered. What's new? What remains unresolved?"),
    }
    return instructions.get(phase, instructions["OPEN"])


def _format_relationship(other_name: str, rel: dict | None) -> str:
    """Format relationship context for prompt."""
    if not rel:
        return f"RELATIONSHIP WITH {other_name}: First conversation."
    count = rel.get("conversation_count", 0)
    strength = rel.get("strength", 0)
    return (
        f"RELATIONSHIP WITH {other_name}: {count} prior conversations. Strength: {strength:.1f}/1.0"
    )


def _format_memories(memories: list[str] | None) -> str:
    """Format memories for prompt injection."""
    if not memories:
        return "MEMORIES: None yet."
    formatted = "\n".join(f"- {m}" for m in memories[:5])
    return f"MEMORIES:\n{formatted}"
