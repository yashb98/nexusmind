# EMBEDDED_TUTOR.md — Step 5
# Tutor runs in parallel with live debates. Standalone teach-back stays for background insights.
# DO NOT modify existing TeachBackService. ADD the embedded tutor as a new parallel system.

## Architecture

When background=False (user watching), two WebSocket channels run simultaneously:
- /ws/v1/conversations/{id}/live → agent debate (existing)
- /ws/v1/conversations/{id}/tutor → tutor commentary (NEW)
- /ws/v1/conversations/{id}/tutor/respond → learner responses (NEW)

The tutor does NOT block the debate. It's fire-and-forget after each agent turn.

## Tutor Modes
- **explain** — Agent used concept user might not know → explain at Bloom level
- **check** — Debatable point raised → ask user what they think
- **reflect** — SYNTHESIZE/EXTRACT phase → ask for user's own take
- **observe** — Nothing special → brief 1-sentence contextual note

## Mode Selection Logic
```python
def select_tutor_mode(latest_message, phase, learner_bloom, conversation_history):
    if phase in ("SYNTHESIZE", "EXTRACT"):
        return "reflect"
    if contains_unfamiliar_concepts(latest_message, learner_bloom):
        return "explain"
    if phase in ("CHALLENGE", "PROBE") and is_debatable_claim(latest_message):
        return "check"
    return "observe"
```

## Implementation

Add to ConversationService as a parallel node in LangGraph:

```python
async def generate_tutor_turn(self, state):
    """Runs AFTER each agent turn. Non-blocking (fire-and-forget)."""
    if state["background"]:
        return state  # No tutor for background conversations
    
    mode = select_tutor_mode(
        state["messages"][-1], state["phase"], 
        state.get("learner_bloom", 1), state["messages"]
    )
    
    tutor_response = await self.llm.generate(
        system_prompt=EMBEDDED_TUTOR_PROMPT.format(
            user_name=state["user_name"],
            agent_a=state["agent_a_name"],
            agent_b=state["agent_b_name"],
            topic=state["topic"],
            latest_message=state["messages"][-1]["content"],
            phase=state["phase"],
            bloom_level=state.get("learner_bloom", 1),
            tutor_mode=mode,
        ),
        messages=[],
        trace_id=f"{state['conversation_id']}_tutor_{state['turn_count']}",
    )
    
    # Send via tutor WebSocket (non-blocking)
    asyncio.create_task(self.ws_manager.send_tutor(
        state["conversation_id"],
        {"type": "tutor", "mode": mode, "content": tutor_response, 
         "turn": state["turn_count"]}
    ))
    
    # Optional: trigger avatar generation async
    asyncio.create_task(self.avatar.generate_avatar_video(tutor_response, ...))
    
    return state
```

## Embedded Tutor Prompt Template

```
You are a Socratic tutor helping {user_name} understand a live debate 
between {agent_a} and {agent_b} about "{topic}".

LEARNER'S LEVEL: Bloom Level {bloom_level}

LATEST MESSAGE: "{latest_message}" — during {phase} phase

MODE: {tutor_mode}

MODE INSTRUCTIONS:
- explain: Agent used a concept learner may not know. Explain simply in 1-2 sentences. Ask ONE question.
- check: A debatable point was raised. Ask what the learner thinks. Don't explain — test reasoning.
- reflect: Debate is concluding. Ask for learner's own position. Push them to synthesize.
- observe: Nothing needs intervention. One brief sentence about what's happening.

RULES:
1. Keep it SHORT. 1-3 sentences max. The debate is the main show.
2. NEVER spoil upcoming turns. Only comment on what already happened.
3. If learner hasn't responded to previous questions, switch to observe.
4. NEVER say "wrong." Guide with questions.
```

## Bloom Assessment via DSPy
The Bloom level assessment (used in both embedded tutor and standalone teach-back) uses a DSPy BloomAssessor module for reliable classification. This is NOT in the tutor generation — the tutor prompt is still hand-written for natural conversation. Only the ASSESSMENT of the learner's response uses DSPy.

## Learner Response Handling

```python
async def handle_tutor_response(self, conversation_id: str, learner_message: str):
    """User responds to tutor during live debate. Updates Bloom level."""
    state = await self.get_conversation_state(conversation_id)
    
    bloom = await self.teachback.assess_bloom_level(
        state["user_id"], state["topic"],
        [{"role": "tutor", "content": state["last_tutor_message"]},
         {"role": "learner", "content": learner_message}]
    )
    
    # Update learner knowledge
    await self.db.execute("""
        INSERT INTO learner_knowledge (user_id, topic, bloom_level, last_assessed)
        VALUES ($1, $2, $3, NOW())
        ON CONFLICT (user_id, topic) 
        DO UPDATE SET bloom_level = GREATEST(learner_knowledge.bloom_level, $3), last_assessed = NOW()
    """, state["user_id"], state["topic"], bloom)
    
    # Send bloom update to tutor channel
    await self.ws_manager.send_tutor(conversation_id, {
        "type": "bloom_update", "level": bloom
    })
```

## Frontend: Split Panel

Conversation tab becomes a 60/40 split:
- LEFT: Agent debate (chat bubbles, streaming tokens, phase badges)
- RIGHT: Tutor panel (commentary, learner input, Bloom bar, avatar)

The tutor panel has a minimize button. If user doesn't interact for 30s, it auto-minimizes to a small indicator.
