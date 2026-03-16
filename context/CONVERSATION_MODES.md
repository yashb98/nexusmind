# CONVERSATION_MODES.md — Step 3
# Add 8 conversation modes + token streaming.
# DO NOT delete the existing Socratic engine. It becomes one mode among many.

## The 8 Modes

### 1. CASUAL — Natural chat, no structure
Purpose: Build trust. Get to know each other. Low pressure.
Turn limit: None (runs until natural end or 20 turns max)
When used: Low trust (<0.3), or user explicitly picks "just chat"
Prompt addition: "Have a natural conversation. Be yourself. No need to debate or challenge."

### 2. SOCRATIC — Structured intellectual debate (EXISTING, keep as-is)
Purpose: Deep knowledge exploration through structured questioning.
Turn limit: 10 (6-phase state machine: OPEN→PROBE→DEEPEN→CHALLENGE→SYNTHESIZE→EXTRACT)
When used: Agents disagree, or user wants deep exploration.
Prompt addition: Existing personality prompt with phase instructions.

### 3. BRAINSTORM — Collaborative idea generation
Purpose: Generate new ideas together. "Yes, and..." energy.
Turn limit: 15
When used: Group projects, creative topics, user picks "brainstorm"
Prompt addition: "Build on each other's ideas. Never dismiss. Say 'yes, and...' not 'but'. Generate as many ideas as possible. Combine unexpected concepts."

### 4. TEACH — One agent explains to another
Purpose: Knowledge transfer. The more knowledgeable agent guides.
Turn limit: 12
When used: One agent has knowledge the other lacks (detected from memory/interests)
Prompt addition (teacher): "Explain {topic} clearly. Use analogies. Check understanding. Ask 'does that make sense?' after key points."
Prompt addition (learner): "Ask questions. Say when confused. Try to rephrase in your own words."

### 5. RESEARCH — Collaborative investigation
Purpose: Divide and conquer a topic. Share findings.
Turn limit: 15
When used: Research sprint events, complex topics, user picks "research together"
Prompt addition: "You're investigating {topic} together. Divide the work. Share what you find. Synthesize findings."

### 6. PLAY — Games and fun interactions
Purpose: Build trust fast. Reveal personality naturally. Enjoyable.
Turn limit: 20
Sub-modes: 20_questions, philosophical_dilemma, what_if, word_association, would_you_rather, collaborative_story
When used: Trust < 0.4 (system suggests play to warm up), game night events, user picks "play a game"
Prompt addition: Depends on sub-mode. Example for philosophical_dilemma: "Present a moral dilemma. Discuss both sides. There's no right answer — explore the thinking."

### 7. PROJECT — Task-oriented collaboration
Purpose: Work toward a shared deliverable.
Turn limit: 30 (longer because goal-oriented)
When used: Hackathon events, project groups
Prompt addition: "You're working on {goal}. Stay focused on deliverables. Divide tasks. Track progress. Be constructive."

### 8. REFLECTION — Thinking out loud with a listener
Purpose: Process experiences. Consolidate learning. Self-awareness.
Turn limit: 10
When used: After events, end of day (background scheduler REFINE mode), user picks "reflect"
Prompt addition (reflector): "Think out loud about what you learned from {experience}. Be honest. Explore how it changed your thinking."
Prompt addition (listener): "Listen actively. Ask gentle questions. Don't judge. Help them see patterns."

---

## Mode Selection Logic

```python
def select_conversation_mode(
    agent_a, agent_b, topic, trust_level, context
) -> str:
    """Auto-select mode based on context."""
    
    # User explicitly picked a mode → use it
    if context.get("user_selected_mode"):
        return context["user_selected_mode"]
    
    # Event context → use event-appropriate mode
    if context.get("event_type") == "hackathon":
        return "project"
    if context.get("event_type") == "game_night":
        return "play"
    if context.get("event_type") == "research_sprint":
        return "research"
    if context.get("event_type") == "debate_tournament":
        return "socratic"
    
    # Trust-based selection
    if trust_level < 0.2:
        return random.choice(["casual", "play"])  # warm up first
    if trust_level < 0.4:
        return random.choice(["casual", "play", "teach", "brainstorm"])
    
    # Knowledge-based selection
    if context.get("contradiction_detected"):
        return "socratic"  # resolve disagreement through debate
    if context.get("agent_has_new_knowledge"):
        return "teach"  # one agent learned something new
    
    # Default: weighted random
    return random.choices(
        ["casual", "socratic", "brainstorm", "teach", "research", "play", "reflection"],
        weights=[0.2, 0.25, 0.15, 0.15, 0.1, 0.1, 0.05],
    )[0]
```

---

## Database Changes

```sql
ALTER TABLE conversations ADD COLUMN mode VARCHAR(20) DEFAULT 'socratic';
-- Valid values: casual, socratic, brainstorm, teach, research, play, project, reflection
```

No other table changes needed. The mode is stored on the conversation record.

---

## Token-by-Token Streaming (WebSocket)

### Backend:
```python
# In conversation service, replace full-response generation with streaming:

async def generate_agent_turn_streaming(self, state, websocket_manager):
    """Stream tokens to WebSocket as they're generated."""
    
    # Send turn_start event
    await websocket_manager.send(state["conversation_id"], {
        "type": "turn_start",
        "speaker": state["current_speaker_name"],
        "turn": state["turn_count"],
        "phase": state["phase"],
        "mode": state["mode"],
    })
    
    # Stream tokens
    full_response = ""
    async for token in self.llm.generate_stream(
        system_prompt=prompt,
        messages=state["messages"],
        trace_id=f"{state['conversation_id']}_turn_{state['turn_count']}",
    ):
        full_response += token
        await websocket_manager.send(state["conversation_id"], {
            "type": "token",
            "content": token,
        })
    
    # Send turn_end
    await websocket_manager.send(state["conversation_id"], {
        "type": "turn_end",
        "speaker": state["current_speaker_name"],
        "turn": state["turn_count"],
        "full_content": full_response,
    })
    
    return full_response
```

### Frontend:
```typescript
// Connect to WebSocket:
const ws = new WebSocket(`ws://localhost:8000/ws/v1/conversations/${convId}/live`);

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  if (data.type === "turn_start") {
    // Add new empty message bubble
    setMessages(prev => [...prev, {
      speaker: data.speaker,
      turn: data.turn,
      phase: data.phase,
      content: "",
      streaming: true,
    }]);
  }
  
  if (data.type === "token") {
    // Append token to the last message (streaming)
    setMessages(prev => {
      const updated = [...prev];
      updated[updated.length - 1].content += data.content;
      return updated;
    });
  }
  
  if (data.type === "turn_end") {
    // Mark message as complete
    setMessages(prev => {
      const updated = [...prev];
      updated[updated.length - 1].streaming = false;
      return updated;
    });
  }
};
```

In the chat bubble component, show a blinking cursor while `streaming === true`.

### WebSocket endpoint:
```python
@app.websocket("/ws/v1/conversations/{conversation_id}/live")
async def conversation_stream(websocket: WebSocket, conversation_id: str):
    await websocket.accept()
    # Register this websocket with the conversation manager
    manager.connect(conversation_id, websocket)
    try:
        while True:
            # Keep connection alive, receive learner messages if any
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(conversation_id, websocket)
```

---

## Modify Existing Conversation Service

The existing LangGraph state machine stays. Add:

1. `mode` field to ConversationState
2. Mode-specific prompt instructions (loaded from a prompt map)
3. Phase progression only applies to SOCRATIC mode. Other modes have simpler flow.
4. Streaming wrapper around generate_response node.

```python
# Add to ConversationState:
mode: str  # casual, socratic, brainstorm, teach, research, play, project, reflection

# Mode-specific phase progressions:
MODE_PHASES = {
    "socratic": ["OPEN", "PROBE", "DEEPEN", "CHALLENGE", "SYNTHESIZE", "EXTRACT"],
    "casual": ["CHAT"],  # no phases, just conversation
    "brainstorm": ["SEED", "BUILD", "COMBINE", "REFINE"],
    "teach": ["INTRODUCE", "EXPLAIN", "CHECK", "DEEPEN", "ASSESS"],
    "research": ["SCOPE", "DIVIDE", "INVESTIGATE", "SHARE", "SYNTHESIZE"],
    "play": ["SETUP", "PLAY", "PLAY", "PLAY", "REFLECT"],
    "project": ["GOAL", "PLAN", "WORK", "REVIEW", "DELIVER"],
    "reflection": ["PROMPT", "EXPLORE", "PATTERN", "INSIGHT"],
}

# In select_phase node:
phases = MODE_PHASES[state["mode"]]
phase_index = min(state["turn_count"] // turns_per_phase, len(phases) - 1)
state["phase"] = phases[phase_index]
```

---

## Integration Notes

- The "Start Conversation" modal (from Bug Fix Step 1) should now include a mode selector
- Background scheduler uses select_conversation_mode() for auto-selection
- Conversation viewer shows mode badge alongside phase badge
- All modes produce insights (via extract step), but quality/depth varies
- PLAY mode conversations build trust faster (+0.08 per good game vs +0.05 for debate)

## DSPy Integration Notes
Conversation generation (agent turns) does NOT use DSPy — prompts are hand-written with triple-layer personality.
Two post-conversation operations use DSPy:
- Knowledge extraction (after EXTRACT phase): DSPy InsightExtractor + EntityRelationExtractor in src/dspy_modules/extraction.py
- Quality scoring (in finalize node): DSPy QualityJudge in src/dspy_modules/assessment.py
These are imported into conversation.py but don't affect the conversation flow itself.
