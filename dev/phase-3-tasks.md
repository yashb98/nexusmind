# Phase 3: Socratic Conversations + Knowledge Extraction
# Engineering Layer: PROCESS (nervous system)
# Estimated: 4-5 days | Prerequisite: Phase 2

## Completion Criteria
- [ ] Two agents have a 10-turn Socratic debate via API
- [ ] Conversation follows phase progression: OPEN → PROBE → DEEPEN → CHALLENGE → SYNTHESIZE → EXTRACT
- [ ] Each turn: permission check → memory retrieval → personality injection → LLM → graph update
- [ ] Knowledge extraction produces ≥ 1 structured insight per conversation
- [ ] All conversations logged in Langfuse with full trace
- [ ] Memory stored in Qdrant after each conversation
- [ ] KNOWS edges updated (strength, trust, conversation_count)
- [ ] LLM behavioral test: personality consistency across 5 conversations

## Layer Test
"Can two agents have a 10-turn Socratic debate where Agent A challenges Agent B's assumptions, and the system extracts 2-3 specific insights?"

## Tasks

### 3.1 LLM Service
- `src/llm/llm_service.py`:
  - Local MLX inference via `mlx_lm.generate` (primary)
  - LiteLLM fallback to cloud API
  - Every call wrapped in Langfuse trace (model, tokens, cost, latency)
  - Retry: local → fallback provider
  - `generate(system_prompt, messages, trace_id)` → response
  - `embed(text)` → vector for Qdrant

### 3.2 Conversation Models
- `src/models/conversation.py`:
  - ConversationRequest (agent_a_id, agent_b_id, topic)
  - ConversationResponse (id, transcript, summary, insights, quality_score, audit)
  - Message (speaker_agent_id, content, turn_number, phase, timestamp)
  - ConversationState (LangGraph TypedDict — see ARCHITECTURE.md §3.1)

### 3.3 Socratic Conversation Engine (LangGraph)
- `src/services/conversation.py`:
  - Build LangGraph StateGraph with nodes:
    1. `check_permissions` — verify both agents can discuss topic at their permission level
    2. `select_phase` — determine phase from turn count:
       - Turns 1-2: OPEN, Turns 3-4: PROBE, Turns 5-6: DEEPEN
       - Turns 7-8: CHALLENGE, Turn 9: SYNTHESIZE, Turn 10: EXTRACT
    3. `retrieve_memory` — get relevant memories from Qdrant, filtered by permission
    4. `inject_personality` — build system prompt using PersonalityService + phase instructions
    5. `generate_response` — LLM call with personality + phase + memory context
    6. `update_state` — store message, switch speaker, update Neo4j relationship
    7. `evaluate_turn` — should conversation continue? Has max_turns been reached?
    8. `extract_knowledge` — (EXTRACT phase only) use LLM to pull structured insights:
       - What new knowledge emerged?
       - What assumptions were challenged?
       - What questions remain unresolved?
    9. `finalize` — compute quality_score (LLM-as-judge), store Conversation node in Neo4j,
       store insights as Insight nodes, update KNOWS edge, store memories in Qdrant
  - Conditional edges: evaluate_turn → (continue → select_phase | end → extract_knowledge)

### 3.4 Knowledge Extraction Service
- `src/services/knowledge.py`:
  - `extract_insights(conversation: ConversationResponse)` → list[Insight]
  - Uses LLM to identify: new facts, challenged assumptions, unresolved questions
  - Each insight gets: content, importance score, related topics, bloom_relevance
  - Store as Insight nodes in Neo4j, linked to Conversation and Topic nodes
  - Store vector embedding in Qdrant for semantic search

### 3.5 Conversation Routes
- `src/routes/conversations.py`:
  - POST /api/v1/conversations — trigger Socratic debate
  - POST /api/v1/conversations/broadcast — broadcast topic to agent's top 3 connections
  - GET /api/v1/conversations/{id} — transcript + insights + audit trail
  - GET /api/v1/agents/{id}/conversations — list agent's conversations

### 3.6 Insights Routes
- `src/routes/insights.py`:
  - GET /api/v1/agents/{id}/insights — insight feed (sorted by recency, importance)
  - GET /api/v1/agents/{id}/discoveries — knowledge your agent brought back from debates

### 3.7 Tests
- `tests/unit/test_conversation_state.py` — LangGraph state transitions, phase progression
- `tests/unit/test_knowledge_extraction.py` — insight extraction from mock conversations
- `tests/unit/test_memory.py` — store/retrieve with permission filtering
- `tests/integration/test_conversation_flow.py` — full 10-turn Socratic debate end-to-end
- `tests/integration/test_insights.py` — insights appear after conversation
- `tests/llm_eval/test_personality_consistency.py`:
  - Same agent, 5 different conversations, 5 different partners
  - Measure Big Five trait expression (LLM-as-judge scores each dimension)
  - Assert: variance < 0.5 across all 5 dimensions
- `tests/llm_eval/test_socratic_behavior.py`:
  - Verify agents NEVER give direct answers in PROBE/CHALLENGE phases
  - Verify agents DO ask questions (at least 1 question per turn in PROBE phase)

## Checkpoint
`uv run pytest tests/ -x && echo "Phase 3 DONE"`
`git commit -m "feat: Phase 3 — Socratic conversations + knowledge extraction" && git tag v0.3.0`
