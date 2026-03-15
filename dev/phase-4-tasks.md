# Phase 4: Verification Council + 3-Tier Memory + Communities + Teach-Back
# Engineering Layer: ENVIRONMENT (soul — verified emergent intelligence)
# Estimated: 5-6 days | Prerequisite: Phase 3

## Completion Criteria
- [ ] Verification Council: all new insights pass through Skeptic + Connector + Judge
- [ ] Insights have verification_status: ACCEPTED / PROVISIONAL / INVESTIGATE / REJECTED
- [ ] 3-tier memory lifecycle: hot (30 days) → cold (>90 days, low importance). Superseded facts marked, not deleted
- [ ] Community detection: ≥ 2 communities from 100 test conversations
- [ ] Teach-back: user clicks insight → avatar tutor assesses Bloom → Socratic teaching
- [ ] Bloom level updates after successful session
- [ ] SearXNG web search provides current info during teach-back (results cached in knowledge_base)
- [ ] Avatar pipeline: text → Edge TTS → SadTalker (RunPod T4) → video
- [ ] Trending topics endpoint works
- [ ] All tests pass including emergence + verification tests

## Layer Test
"After 100 conversations, did ≥ 2 communities form? Did the Verification Council catch at least 1 low-quality claim? Did a user's Bloom level increase through teach-back?"

## Tasks

### 4.1 Verification Council Service
- `src/services/verification.py`:
  - `verify(insight, conversation_context)` → VerificationDecision
  - `run_skeptic(insight, context)` → parallel:
    1. Web search for counter-evidence via SearXNG
    2. Check for contradictions in Neo4j graph
    3. LLM evaluates source reliability → score 0-1 + reasoning
  - `run_connector(insight, context)` → parallel:
    1. Neo4j: find related entities (graph traversal)
    2. Qdrant: find similar memories (semantic search)
    3. LLM evaluates novelty + connections → score 0-1 + connection list
  - `run_judge(insight, skeptic_result, connector_result)`:
    - Decision matrix based on skeptic_score thresholds (ARCHITECTURE.md §4.2)
    - Store decision in verification_decisions table
  - Skeptic + Connector run in PARALLEL (asyncio.gather)
- `src/routes/verification.py`:
  - GET /api/v1/verification/recent
  - GET /api/v1/verification/{insight_id}

### 4.2 Integrate Verification into Conversation Pipeline
- Update `src/services/conversation.py` finalize step:
  - After extract_knowledge: for each insight → run verification.verify()
  - Only ACCEPTED insights stored with high confidence in Neo4j + Qdrant
  - PROVISIONAL insights stored with confidence=0.5
  - INVESTIGATE triggers: schedule 3 more debates on topic (queue for scheduler)
  - REJECTED insights: logged but NOT stored in graph or memory

### 4.3 Three-Tier Memory Lifecycle
- Update `src/services/memory.py`:
  - `store_memory()` — stores in hot collection with expires_at (30 days)
  - `retrieve_memories()` — search hot first, then graph entities, then cold (if hot returns < 3 results)
  - `run_memory_lifecycle()` — scheduled task:
    1. Move hot memories older than 30 days + importance < 0.3 → cold archive
    2. Keep hot memories with importance ≥ 0.3 (extend expires_at)
    3. Delete cold memories never retrieved in 6 months (last_retrieved = null, archived > 6mo ago)
  - `handle_contradiction(new_fact, old_fact)`:
    - Mark old entity as SUPERSEDED in Neo4j (keep for provenance)
    - New entity gets SUPERSEDES relation pointing to old
    - Retrieval always prefers newest version (sort by discovered_at DESC)
  - Add to graph.py: `multi_hop_query(start_entity, max_hops=3)` — traverse typed relations

### 4.4 Community Detection
- Add to `src/services/graph.py`:
  - `run_community_detection()` — Leiden algorithm
    - Export graph to networkx if Neo4j GDS not available on Aura Free
    - Weight edges: strength * 0.5 + trust * 0.3 + topic_overlap * 0.2
    - Create/update Community nodes + MEMBER_OF edges
    - Auto-name: LLM generates community name from top topics
    - Generate community summary (GraphRAG community summaries)
  - `get_trending_topics(days=7, limit=10)` — growth rate this week vs last
  - `get_smart_recommendations(agent_id, limit=5)`:
    - Interest overlap * 0.4 + community proximity * 0.3 + personality compatibility * 0.3
    - Filter: NOT connected, permission ≥ 1
    - Boost: bridge nodes between communities
- Add routes: POST /communities/detect, GET /communities, GET /topics/trending

### 4.5 Search Service
- `src/services/search.py`:
  - `web_search(query, max_results=5)` → SearXNG
  - `search_and_summarize(query)` → search + LLM summary
  - Cache results in Qdrant knowledge_base collection (TTL 7 days)
  - Before caching: run through Verification Council (web search results are unverified)

### 4.6 Teach-Back Service
- `src/services/teachback.py`:
  - `start_session(user_id, insight_id)`:
    1. Load insight (must be ACCEPTED or PROVISIONAL)
    2. Get/create learner_knowledge for topic
    3. Assess Bloom level
    4. Generate opening Socratic question adapted to level
    5. Return session + first tutor message
  - `process_response(session_id, learner_message)`:
    1. Assess response (correct / partial / incorrect)
    2. Socratic strategy: correct → harder | partial → clarify | incorrect → guide (never say "wrong")
    3. If topic needs current info: query SearXNG
    4. Generate tutor response (teach-back prompt template)
    5. Trigger avatar async: text → Edge TTS → SadTalker (RunPod T4)
    6. Return text immediately + avatar_video_url when ready
  - `complete_session(session_id)`:
    1. LLM-as-judge: assess final Bloom level
    2. Update learner_knowledge table
    3. Log session metrics
- `src/routes/teachback.py` — POST /start, POST /{id}/respond, GET /{id}, GET /learner/{id}/knowledge

### 4.7 Avatar Service
- `src/services/avatar.py`:
  - `generate_avatar_video(text, avatar_image_url, voice_id)`:
    1. Text → Edge TTS → audio.wav (local, <500ms, free)
    2. audio.wav + image → SadTalker (RunPod Serverless T4) → video.mp4
    3. Store video (local or S3)
    4. Return URL
  - 6 diverse preset avatar images in repo
- `src/routes/avatar.py` — POST /generate, GET /presets, POST /upload

### 4.8 Tests
- `tests/unit/test_verification.py` — skeptic scoring, judge decision matrix, all 4 outcomes
- `tests/integration/test_verification_pipeline.py` — end-to-end: insert insight → council → decision stored
- `tests/integration/test_memory_lifecycle.py` — hot → cold migration, contradiction handling, SUPERSEDES
- `tests/integration/test_community_detection.py` — 10 agents, 100 convos → ≥ 2 communities
- `tests/integration/test_teachback.py` — start → 3 responses → Bloom level update
- `tests/integration/test_search.py` — web search + cache in knowledge_base
- `tests/llm_eval/test_verification_catches_bad.py` — feed 5 good + 5 bad insights → council rejects bad ones
- `tests/llm_eval/test_teachback_socratic.py` — tutor NEVER gives direct answer
- `tests/llm_eval/test_emergence.py` — after 100 convos: ≥ 1 cross-community insight, trending topics match patterns

## Checkpoint
```bash
uv run pytest tests/ -x && echo "Phase 4 DONE — VERIFIED EMERGENCE"
git commit -m "feat: Phase 4 — verification + 3-tier memory + communities + teach-back" && git tag v0.4.0
```
