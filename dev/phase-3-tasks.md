# Phase 3: Socratic Conversations + Knowledge Extraction + Internal Routing
# Engineering Layer: PROCESS (nervous system)
# Estimated: 4-5 days | Prerequisite: Phase 2

## Completion Criteria
- [ ] Two agents have a 10-turn Socratic debate via API
- [ ] Conversation follows phase progression: OPEN → PROBE → DEEPEN → CHALLENGE → SYNTHESIZE → EXTRACT
- [ ] Each turn uses optimized routing: parallel I/O (asyncio.gather) + fire-and-forget updates
- [ ] Turn latency ≈ LLM inference time only (~2-3s), NOT sequential DB calls
- [ ] LLM responses stream via LiteLLM → RunPod Serverless
- [ ] GraphRAG entity extraction: entities + typed relations stored in Neo4j
- [ ] Knowledge extraction produces ≥ 1 structured insight per conversation
- [ ] All conversations logged in Langfuse with full trace
- [ ] Memory stored in Qdrant hot collection after each conversation
- [ ] KNOWS edges updated (strength, trust, conversation_count)
- [ ] LLM behavioral test: personality consistency across 5 conversations

## Layer Test
"Can two agents have a 10-turn Socratic debate where Agent A challenges Agent B's assumptions, the system extracts entity-relation triples, and the turn latency is ~2-3s (not 6-8s)?"

## Tasks

### 3.1 LLM Service (with streaming + Langfuse)
- `src/llm/llm_service.py`:
  - `generate(system_prompt, messages, trace_id, stream=False)` → full response
  - `generate_stream(system_prompt, messages, trace_id)` → async generator of chunks
  - LiteLLM routing: RunPod Serverless (primary) → Anthropic (fallback)
  - Every call wrapped in Langfuse trace (model, tokens, cost, latency)
  - Retry: primary → fallback
- `src/llm/embeddings.py`:
  - `embed(text)` → 768d vector (sentence-transformers, CPU)
  - Batch embed support for bulk operations

### 3.2 Conversation Models
- `src/models/conversation.py`:
  - ConversationRequest (agent_a_id, agent_b_id, topic, background=False)
  - ConversationResponse (id, transcript, summary, insights, entities, quality_score, audit)
  - Message (speaker_agent_id, content, turn_number, phase, timestamp)
  - ConversationState (LangGraph TypedDict — see ARCHITECTURE.md §4.1)

### 3.3 Socratic Conversation Engine (LangGraph + Optimized Routing)
- `src/services/conversation.py`:
  - Build LangGraph StateGraph with nodes:
    1. `parallel_context` — asyncio.gather(check_permissions, retrieve_memory, get_relationship)
       These 3 are INDEPENDENT — run in parallel, not sequential
    2. `select_phase` — determine phase from turn count
    3. `inject_personality` — build system prompt using PersonalityService + phase + context
    4. `generate_response` — LLM call via LiteLLM (streamed for user-facing, non-streamed for background)
    5. `fire_and_forget_updates` — asyncio.create_task for:
       - Store message in conversation history
       - Update Neo4j KNOWS edge (strength, trust, conversation_count)
       - Store memory in Qdrant hot collection
       DO NOT await these — return response immediately
    6. `evaluate_turn` — should conversation continue? advance phase?
    7. `extract_knowledge` — (EXTRACT phase only):
       a. Extract structured insights (what was discovered, challenged, unresolved)
       b. Extract GraphRAG entities + typed relations:
          "carbon-aware scheduling" -[:REDUCES]→ "compute cost" -[:REDUCES]→ "carbon emissions"
       c. Score conversation quality (LLM-as-judge)
    8. `finalize` — store Conversation + Insight + Entity nodes in Neo4j
  - **Embedded Tutor integration:**
    - After each agent turn, generate a tutor turn on the parallel tutor WebSocket channel
    - Tutor WebSocket: `/ws/v1/conversations/{id}/tutor` (read) and `/ws/v1/conversations/{id}/tutor/respond` (write)
    - Auto-select tutor mode (explain/check/reflect/observe) based on user's Bloom level for the topic
    - User can manually override mode via tutor/respond channel
    - Update Bloom level after each CHECK response from the learner

### 3.4 GraphRAG Entity Extraction
- Add to `src/services/knowledge.py`:
  - `extract_insights(conversation)` → list[Insight] (same as before)
  - `extract_entities(conversation)` → list[Entity] with typed relations
    - Entity types: concept, technology, organization, person, claim
    - Relation types: CAUSES, CONTRADICTS, SUPPORTS, RELATES_TO
    - Each relation has: confidence, source_conversation_id, discovered_at
  - `check_contradictions(new_entity, existing_graph)` → list[Contradiction]
    - If new entity contradicts existing: create SUPERSEDES relation (don't delete old)
  - Store entities + relations in Neo4j
  - Store entity embeddings in Qdrant hot collection

### 3.5 Conversation Routes
- `src/routes/conversations.py`:
  - POST /api/v1/conversations — trigger Socratic debate
  - POST /api/v1/conversations/broadcast — broadcast to agent's top 3 connections
  - GET /api/v1/conversations/{id} — transcript + insights + entities + audit
  - GET /api/v1/agents/{id}/conversations — list

### 3.6 Insights Routes
- `src/routes/insights.py`:
  - GET /api/v1/agents/{id}/insights — feed (sorted by recency, importance)
  - GET /api/v1/agents/{id}/discoveries — knowledge your agent brought back

### 3.7 Tests
- `tests/unit/test_conversation_state.py` — state transitions, phase progression
- `tests/unit/test_knowledge_extraction.py` — insight + entity extraction from mock
- `tests/unit/test_entity_extraction.py` — GraphRAG entities + contradiction detection
- `tests/unit/test_memory.py` — store/retrieve with permission filtering
- `tests/integration/test_conversation_flow.py` — full 10-turn Socratic debate
- `tests/integration/test_routing_performance.py` — verify parallel I/O:
  - Mock 3 DB calls at 100ms each
  - Sequential: ~300ms. Parallel (asyncio.gather): ~100ms. Assert < 150ms.
- `tests/integration/test_insights.py` — insights + entities appear after conversation
- `tests/llm_eval/test_personality_consistency.py` — same agent, 5 convos, variance < 0.5
- `tests/llm_eval/test_socratic_behavior.py` — agents never give direct answers in PROBE/CHALLENGE

### 3.8 Embedded Tutor Integration
- `src/services/tutor.py`:
  - LangGraph node `generate_tutor_turn(state, latest_message)`:
    - Runs as Node 8.5 in the conversation graph (after agent turn, before extract)
    - Only active for live (non-background) conversations with tutor enabled
    - Auto-selects mode based on user's Bloom level: L1-2 → EXPLAIN, L3-4 → CHECK, L5-6 → REFLECT
    - Falls back to OBSERVE if exchange is straightforward (no complex arguments detected)
    - Does NOT block the debate flow — runs in parallel via asyncio.create_task
  - WebSocket channels:
    - `/ws/v1/conversations/{id}/tutor` — server pushes tutor messages (explain, check, reflect)
    - `/ws/v1/conversations/{id}/tutor/respond` — user sends responses to CHECK questions
  - Prompt template: Embedded Tutor Prompt (see ARCHITECTURE.md section 6)
  - Mode logic:
    - Auto-mode: Bloom level determines default mode per turn
    - Manual override: user requests a mode → applies for next 3 turns, then reverts to auto
    - OBSERVE: tutor stays silent (no message sent on WebSocket)
  - Bloom updates: after user responds to CHECK question, assess and update learner_knowledge
- **Test criteria:**
  - `tests/unit/test_tutor_mode_selection.py` — mode auto-selects correctly based on Bloom level
  - `tests/unit/test_tutor_prompt.py` — prompt includes latest agent message and correct mode instructions
  - `tests/integration/test_tutor_websocket.py` — tutor messages arrive on separate channel, do not block debate
  - `tests/integration/test_tutor_bloom_update.py` — Bloom level updates after CHECK response

## Checkpoint
```bash
uv run pytest tests/ -x && echo "Phase 3 DONE"
git commit -m "feat: Phase 3 — Socratic engine + GraphRAG + optimized routing" && git tag v0.3.0
```
