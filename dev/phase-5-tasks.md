# Phase 5: Always-On Agents + Progressive Distillation + Self-Evolution
# Engineering Layer: EVOLUTION (the system improves itself)
# Estimated: 5-6 days | Prerequisite: Phase 4

## Completion Criteria
- [ ] Background scheduler runs continuously: EXPLORE + RESEARCH + REFINE modes
- [ ] Agents have autonomous conversations without human trigger (5-10/hr)
- [ ] All background conversation insights pass through Verification Council
- [ ] Micro-adapter training: hourly, rank=4, 2-3 minutes, hot-swappable
- [ ] Full adapter training: nightly, rank=16, 25 minutes, evaluated before deploy
- [ ] Training data filtered: ONLY verified conversations (Verification Council ACCEPTED)
- [ ] Personality consistency improves after fine-tuning (measured variance)
- [ ] Research Scout: weekly arXiv/paper search → generates improvement proposals
- [ ] Code Improvement Agent: weekly metric analysis → generates PRs (not auto-deployed)
- [ ] Safe auto-adjustments: prompt templates, hyperparameters, retrieval params
- [ ] Evolution dashboard API: proposals list, fine-tune history, scheduler stats
- [ ] All tests pass

## Layer Test
"After running for 24 hours, are background conversations happening? Has the micro-adapter been trained at least once? Has the Research Scout found ≥ 1 relevant paper? Is conversation quality measurably improving?"

## Tasks

### 5.1 Background Agent Scheduler
- `src/services/scheduler.py`:
  - `AgentScheduler` class with APScheduler or asyncio loop
  - `run_forever()`: main loop, picks mode based on weighted random
  - `explore_mode()`:
    1. `graph.get_best_unexplored_pair()` — shared interests, never debated
    2. Trigger autonomous Socratic debate (background=True)
    3. Results → insight feed after Verification Council
  - `research_mode()`:
    1. `find_agent_needing_research()` — stale knowledge (oldest memory > 7 days)
    2. Search SearXNG for new info on agent's stale topic
    3. Agent reflects on findings (LLM call)
    4. Reflection → Verification Council
    5. If accepted: schedule debates with relevant partners (queue)
  - `refine_mode()`:
    1. `memory.find_contradictions(agent)` — Qdrant similarity + Neo4j contradiction check
    2. If found: debate with most trusted partner to resolve
    3. Resolution → update graph (SUPERSEDES if applicable)
  - Configuration: cycle interval, max hourly, mode weights (from env vars)
  - Metrics: log every cycle to scheduler_metrics table
- `scripts/run_scheduler.py` — standalone runner (or integrated into FastAPI lifespan)
- `src/routes/scheduler.py`:
  - GET /api/v1/scheduler/status — running, paused, cycle count, mode distribution
  - POST /api/v1/scheduler/pause
  - POST /api/v1/scheduler/resume

### 5.2 Progressive Model Distillation

#### 5.2a Micro-Adapter Training (Hourly)
- `training/train_micro.py`:
  - Collect conversations from last hour with quality_score > 3.5
  - Filter: ONLY conversations with verified insights (Verification Council ACCEPTED)
  - Group by personality archetype
  - Format as JSONL: {system_prompt, messages}
  - Train: rank=4, 100 iterations, batch_size=4
  - On RunPod A10G: ~2-3 minutes per archetype
  - On Mac Studio MLX: ~2-3 minutes per archetype (same)
  - Hot-swap: signal via Redis pub/sub → inference server reloads adapter
  - Log: finetune_runs table (run_type='micro')
- Integration: APScheduler runs every hour

#### 5.2b Full Adapter Training (Nightly)
- `training/train_full.py`:
  - Merge all micro-adapters from today (training/merge_adapters.py)
  - Collect conversations from last 24 hours with quality_score > 4.0
  - Filter: ONLY Verification Council ACCEPTED conversations
  - Train: rank=16, 500 iterations, batch_size=4
  - On RunPod A10G: ~25 minutes per archetype
  - Log: finetune_runs table (run_type='full')

#### 5.2c Adapter Evaluation
- `training/evaluate.py`:
  - Load new adapter
  - Run 10 test conversations per archetype
  - Measure Big Five trait expression variance (LLM-as-judge)
  - PASS: variance < 0.5 on all 5 dimensions
  - If PASS: symlink to ./adapters/{archetype}_latest
  - If FAIL: keep previous adapter, log failure reason + metrics
  - Compare quality scores: new adapter vs previous adapter on same test prompts
  - Log: evaluation metrics to finetune_runs table

#### 5.2d Adapter Merge
- `training/merge_adapters.py`:
  - Merge multiple micro-adapters using weighted average
  - Weights: proportional to training data quality scores
  - Output: single merged adapter for nightly full training base

### 5.3 Fact/Pattern Separation Enforcement
- Update `training/prepare_data.py`:
  - Strip factual claims from training data (they belong in memory, not weights)
  - Keep: conversation style, personality expression, Socratic technique, emotional patterns
  - Remove: specific numbers, dates, named entities, URLs
  - This prevents the model from "memorizing" facts that will become stale
  - Facts stay in Qdrant/Neo4j (updatable). Patterns go into weights (stable).

### 5.4 Research Scout (Loop 3)
- `src/services/evolution.py` (research section):
  - `run_research_scout()` — weekly (Sunday midnight)
  - Search topics: personality LLM, Socratic teaching, knowledge graph RAG, LoRA merging, community detection, emergent behavior, self-improving AI, Bloom taxonomy, conversation evaluation, hallucination detection
  - Sources: SearXNG queries for "arxiv {topic} 2026", "huggingface papers {topic}"
  - For each new paper found:
    1. Summarize (LLM)
    2. Score: relevance (0-1), difficulty (0-1), expected improvement (0-1)
    3. If relevance > 0.7 AND difficulty < 0.6:
       → Create proposal in evolution_proposals table (type='research')
       → Write detailed markdown in proposals/research/{date}_{title}.md
  - Log: proposals created this run

### 5.5 Code Improvement Agent (Loop 4)
- `src/services/evolution.py` (code section):
  - `run_code_improvement()` — weekly (Monday midnight)
  - Step 1 — Monitor: collect metrics from Langfuse + scheduler_metrics:
    - Average conversation quality (trending?)
    - Teach-back Bloom progression rate
    - Verification acceptance rate
    - Memory retrieval relevance (if tracked)
    - Error rates per endpoint
    - Turn latency per conversation
  - Step 2 — Identify: flag functions where metrics degraded >10% this week
  - Step 3 — Research: SearXNG search for solutions to identified problems
  - Step 4 — Propose: generate improved code + tests via LLM
    - Store in evolution_proposals table (type='code')
    - Write to proposals/code/{date}_{function_name}.md
    - Include: problem, solution, expected improvement, code diff, new tests
    - NEVER auto-deploy. Developer reviews.

### 5.6 Safe Auto-Adjustments
- `src/services/evolution.py` (auto-adjust section):
  - Parameters that CAN be auto-adjusted (reversible, low-risk):
    - Prompt template wording (A/B test: generate variant, run 10 convos, compare quality)
    - LoRA hyperparameters (rank, learning rate — evaluate after each run)
    - Retrieval parameters (top-K, similarity threshold — measure relevance)
    - Conversation phase timing (turn counts per phase — measure Socratic depth)
    - Scheduler mode weights (adjust based on which mode produces highest quality)
    - Verification thresholds (tighten/loosen based on acceptance rate trends)
  - Each auto-adjustment: logged with before/after values + rollback capability

### 5.7 Evolution Dashboard Routes
- `src/routes/evolution.py`:
  - GET /api/v1/evolution/proposals — list all (filtered by type, status)
  - GET /api/v1/evolution/proposals/{id} — detail
  - PATCH /api/v1/evolution/proposals/{id} — update status (approved/rejected)
  - GET /api/v1/evolution/finetune/history — all runs with metrics
  - POST /api/v1/evolution/finetune/trigger — manual trigger (admin)
  - GET /api/v1/evolution/metrics — system health dashboard data

### 5.8 Tests
- `tests/unit/test_scheduler.py` — mode selection, rate limiting, pause/resume
- `tests/unit/test_fact_pattern_separation.py` — training data correctly strips facts, keeps patterns
- `tests/integration/test_scheduler_cycle.py` — run 3 cycles, verify conversations created
- `tests/integration/test_micro_finetune.py` — prepare → train (1 iter) → evaluate → hot-swap signal
- `tests/integration/test_full_finetune.py` — merge → train (1 iter) → evaluate → deploy/rollback
- `tests/integration/test_verification_filters_training.py` — only ACCEPTED convos become training data
- `tests/integration/test_research_scout.py` — mock arXiv search → proposal generated
- `tests/integration/test_code_improvement.py` — mock metrics → proposal generated (not deployed)
- `tests/llm_eval/test_improvement_over_time.py`:
  - Run 20 conversations with base adapter
  - Train micro-adapter on best 10
  - Run 20 more conversations
  - Assert: average quality score improved ≥ 0.1

## Checkpoint
```bash
uv run pytest tests/ -x && echo "Phase 5 DONE — THE SYSTEM EVOLVES"
git commit -m "feat: Phase 5 — always-on agents + distillation + self-evolution" && git tag v0.5.0
```
