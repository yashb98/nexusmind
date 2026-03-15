# Phase 4: Communities + Teach-Back + Fine-Tuning Loop
# Engineering Layer: ENVIRONMENT (soul — emergent intelligence)
# Estimated: 5-6 days | Prerequisite: Phase 3

## Completion Criteria
- [ ] Community detection runs and creates ≥ 2 communities from 100 test conversations
- [ ] Teach-back: user clicks insight → avatar tutor assesses Bloom level → Socratic teaching
- [ ] Bloom level updates after successful teach-back session
- [ ] Web search (SearXNG) provides current info during teach-back
- [ ] Nightly fine-tuning pipeline: collect → format → train QLoRA → evaluate → deploy
- [ ] Personality consistency improves after fine-tuning (measured by tests)
- [ ] Trending topics endpoint returns topics ranked by growth
- [ ] Recommendation engine suggests connections based on graph + personality compatibility
- [ ] All tests pass including emergence test

## Layer Test
"After 100 conversations between 10 agents, did ≥ 2 communities form that I didn't design? Did the system surface an insight connecting two conversations I didn't expect? Are agents better after fine-tuning?"

## Tasks

### 4.1 Community Detection (Emergence)
- Add to `src/services/graph.py`:
  - `run_community_detection()` — Leiden algorithm
  - Option A: Neo4j GDS plugin (if available on Aura)
  - Option B: Export graph to networkx, run `community.leiden()`, write back
  - Weight edges: `strength * 0.5 + trust * 0.3 + topic_overlap * 0.2`
  - Create/update Community nodes + MEMBER_OF edges
  - Auto-name communities by most common topic among members
  - Trigger: every 100 conversations OR on-demand via API
- Add to `src/routes/graph.py`:
  - POST /api/v1/graph/communities/detect (admin only)
  - GET /api/v1/graph/communities (list with members)

### 4.2 Trending Topics
- Add to `src/services/graph.py`:
  - `get_trending_topics(days=7, limit=10)`
  - Cypher: count DISCUSSED edges per topic in last 7 days vs previous 7 days
  - Rank by growth rate (this_week / last_week)
- Add: GET /api/v1/graph/topics/trending

### 4.3 Recommendation Engine
- Enhance `src/services/graph.py`:
  - `get_smart_recommendations(agent_id, limit=5)`:
    - Interest overlap (Jaccard) × 0.4
    - Community proximity (same or adjacent) × 0.3
    - Personality compatibility × 0.3
    - Filter: NOT already connected, permission level ≥ 1
    - Boost: agents who are "bridge" nodes between communities

### 4.4 Teach-Back Service
- `src/services/teachback.py`:
  - `start_session(user_id, insight_id)`:
    1. Load insight from Neo4j
    2. Get/create learner_knowledge entry for topic
    3. Assess current Bloom level
    4. Generate opening Socratic question adapted to level
    5. Return session with first tutor message
  - `process_response(session_id, learner_message)`:
    1. Load session state
    2. Assess learner's response (correct/partial/incorrect)
    3. Apply Socratic strategy:
       - Correct → praise specifically + increase difficulty
       - Partial → ask clarifying follow-up
       - Incorrect → DON'T say wrong → ask guiding question
    4. If topic needs current info: query SearXNG
    5. Generate tutor response using teach-back prompt template (ARCHITECTURE.md §6)
    6. Trigger avatar generation (async): text → Edge TTS → SadTalker (via RunPod)
    7. Return text immediately + avatar_video_url when ready
  - `complete_session(session_id)`:
    1. Assess final Bloom level (LLM-as-judge)
    2. Update learner_knowledge table
    3. Log session metrics

- `src/routes/teachback.py`:
  - POST /api/v1/teachback/start
  - POST /api/v1/teachback/{id}/respond
  - GET /api/v1/teachback/{id}
  - GET /api/v1/learner/{id}/knowledge (Bloom levels per topic)

### 4.5 Search Service
- `src/services/search.py`:
  - `web_search(query, max_results=5)` → search SearXNG instance
  - `search_and_summarize(query)` → search + LLM summarization
  - Cache results in Qdrant knowledge_base collection (avoid re-searching same query)

### 4.6 Avatar Service
- `src/services/avatar.py`:
  - `generate_avatar_video(text, avatar_image_url, voice_id)`:
    1. Text → Edge TTS → audio.wav (local, <500ms)
    2. audio.wav + avatar_image → SadTalker (via RunPod serverless GPU) → video.mp4
    3. Upload video to S3/local storage
    4. Return video URL
  - For MVP: generate avatar video async, return text immediately
  - Presets: 6 diverse avatar images included in repo

### 4.7 Fine-Tuning Pipeline
- `training/prepare_data.py`:
  - Pull conversations with quality_score > 4.0 from last 24 hours
  - Group by personality archetype (6 clusters)
  - Format as JSONL: {system_prompt, messages, quality_label}
  - Train/valid split (90/10)

- `training/train_adapters.py`:
  - For each archetype with sufficient data (≥ 50 examples):
    - Run: `python -m mlx_lm.lora --model Qwen2.5-7B-4bit --data {path} --train --iters 500 --batch-size 4 --lora-layers 16 --adapter-path ./adapters/{archetype}_v{N}`
  - Log: training loss, val loss, duration → finetune_runs table

- `training/evaluate.py`:
  - Load new adapter
  - Run 10 test conversations per archetype
  - Measure Big Five trait expression variance (LLM-as-judge)
  - PASS threshold: variance < 0.5 on all dimensions
  - If PASS: copy adapter to `./adapters/{archetype}_latest` (hot-swap)
  - If FAIL: keep previous adapter, log failure reason

- `src/services/finetune.py`:
  - `run_nightly_pipeline()` — orchestrates prepare → train → evaluate → deploy
  - Called by cron or manual trigger

- `scripts/setup_cron.py`:
  - Configure crontab: `0 2 * * * python training/train_adapters.py --all-archetypes`

### 4.8 Tests
- `tests/integration/test_community_detection.py`:
  - Create 10 agents, run 100 conversations with topic clustering
  - Assert: ≥ 2 communities detected with modularity > 0.3
- `tests/integration/test_teachback.py`:
  - Start session → respond 3 times → verify Bloom level progression
  - Verify tutor NEVER gives direct answer (Socratic check)
- `tests/integration/test_search.py`:
  - Web search returns results, cache works
- `tests/integration/test_finetune_pipeline.py`:
  - Mock pipeline: prepare data → train (1 iter) → evaluate → deploy
  - Verify adapter file created, metrics logged
- `tests/llm_eval/test_emergence.py`:
  - After 100 conversations: verify ≥ 1 insight connects agents from different communities
  - Verify trending topics reflect actual conversation patterns
  - This is the ENVIRONMENT LAYER test — emergent behavior verification

## Checkpoint
`uv run pytest tests/ -x && echo "Phase 4 DONE — THE SOUL IS ALIVE"`
`git commit -m "feat: Phase 4 — communities + teach-back + fine-tuning = emergence" && git tag v0.4.0`
