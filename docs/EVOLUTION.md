# EVOLUTION.md — NexusMind Self-Evolution Systems

## Overview
NexusMind has four autonomous improvement loops. Three are fully autonomous. One requires human approval. Together, they create a system that gets smarter every hour.

## Loop 1: Knowledge Evolution (Continuous, Autonomous)

### Always-On Background Agent Scheduler
Agents work 24/7 in three modes. The scheduler picks work based on weighted random selection.

```python
# Scheduler configuration
EXPLORE_WEIGHT = 0.4   # 40% — pair agents for new debates
RESEARCH_WEIGHT = 0.3  # 30% — agents search web for new info
REFINE_WEIGHT = 0.3    # 30% — agents re-examine own memories
CYCLE_INTERVAL = 300   # 5 minutes between cycles
MAX_HOURLY = 12        # Max 12 background conversations per hour
```

**EXPLORE mode:** Find best unexplored pair (shared interests, never debated). Trigger autonomous Socratic debate. Results go to insight feed after Verification Council approval.

**RESEARCH mode:** Find agent with stale knowledge (oldest memory > 7 days on a topic). Search SearXNG for new information. Agent reflects on findings, then debates them with relevant partners.

**REFINE mode:** Find agent with contradictory memories (via Qdrant similarity search + Neo4j contradiction check). Agent debates the contradiction with its most trusted partner to resolve.

### Verification Council Pipeline

```
New knowledge enters
       │
       ├──→ Skeptic (parallel): source reliability check + counter-evidence search
       ├──→ Connector (parallel): graph relation mapping + novelty assessment
       │
       ▼
Judge decides:
  Skeptic > 0.8             → ACCEPT:      store verified, confidence=0.9
  Skeptic 0.5-0.8           → PROVISIONAL: store, confidence=0.5, flag review
  Skeptic 0.3-0.5           → INVESTIGATE: schedule 3 debates on topic
  Skeptic < 0.3             → REJECT:      don't store, log reason

Applied BEFORE:
  - Any insight stored in Neo4j or Qdrant
  - Any web search result cached
  - Any conversation becomes training data for fine-tuning
```

Cost: ~3 LLM calls per knowledge item (one per council member). ~£0.001 per verification.

## Loop 2: Model Evolution (Hourly + Nightly, Autonomous)

### Progressive Distillation Architecture

```
Tier 1: WORKING MEMORY (context window)
  Lives in: LLM context (8K-32K tokens)
  Content: current conversation + retrieved memories
  Speed: instant
  When full: compact → extract key facts → store in Tier 2

Tier 2: EPISODIC MEMORY (structured storage)
  Lives in: Qdrant hot collection + Neo4j entities
  Content: compacted conversations, entity-relation triples, social context
  Speed: 50-200ms retrieval
  Always available for next conversation turn
  Every hour: distill patterns into Tier 3

Tier 3: MICRO-ADAPTERS (hourly LoRA updates)
  Lives in: adapter files (~5MB each)
  Config: rank=4, 100 iterations, 2-3 minutes training
  Content: PATTERNS (conversation style, personality expression, Socratic technique)
  NOT facts (facts stay in Tier 2 — always separated)
  Hot-swapped without restarting inference
  Every night: merge into Tier 4

Tier 4: BASE ADAPTER (nightly full fine-tune)
  Lives in: versioned adapter files (~50MB each)
  Config: rank=16, 500 iterations, 25 minutes training
  Process: merge all micro-adapters + new training data
  Evaluated: personality consistency variance < 0.5 on all 5 dimensions
  If PASS: deploy as new base. If FAIL: keep previous, log failure.
  Versioned with git tag. Previous version always available for rollback.
```

### Key Separation Principle
Facts → MEMORY (searchable, updatable, deletable)
Patterns → WEIGHTS (baked into model, fast, no retrieval cost)

Examples:
- "Bitcoin price is $95K" → MEMORY (changes daily)
- "Agent_Maria argues analytically" → WEIGHTS (stable pattern)
- "Carbon-aware scheduling reduces cost by 40%" → MEMORY (verifiable claim)
- "How to ask good Socratic follow-up questions" → WEIGHTS (skill)

### Micro-Adapter Training Script

```bash
# Runs every hour via APScheduler (or cron)
# Takes 2-3 minutes per archetype on RunPod A10G (or Mac Studio MLX)

python training/train_micro.py \
  --archetype analytical \
  --data-source "last_hour" \
  --rank 4 \
  --iters 100 \
  --batch-size 4 \
  --adapter-path ./adapters/micro/{archetype}_{timestamp}

# After training, hot-swap signal via Redis pub/sub
# MLX / vLLM picks up new adapter without restart
```

### Nightly Full Training Script

```bash
# Runs at 2 AM via cron
# Takes 25 minutes per archetype

python training/train_full.py \
  --all-archetypes \
  --merge-micro  # Merge all micro-adapters from today
  --data-source "last_24h" \
  --min-quality 4.0 \
  --verification-filter "accepted_only" \  # ONLY verified training data
  --rank 16 \
  --iters 500 \
  --batch-size 4 \
  --adapter-path ./adapters/full/{archetype}_v{N}

python training/evaluate.py \
  --adapter-path ./adapters/full/{archetype}_v{N} \
  --test-conversations 10 \
  --variance-threshold 0.5

# If evaluation passes: symlink to ./adapters/{archetype}_latest
# If fails: keep previous version, log failure metrics
```

## Loop 3: Research Evolution (Weekly, Autonomous)

### Research Scout Agent
Runs every Sunday at midnight. Searches for papers and techniques that could improve NexusMind.

```python
RESEARCH_TOPICS = [
    "personality LLM fine-tuning",
    "Socratic teaching AI",
    "knowledge graph RAG",
    "LoRA adapter merging",
    "community detection dynamic graphs",
    "emergent behavior multi-agent",
    "self-improving AI systems",
    "Bloom taxonomy adaptive learning",
    "conversation quality evaluation",
    "hallucination detection verification",
]

SEARCH_SOURCES = [
    "arxiv.org",
    "semanticscholar.org",
    "huggingface.co/papers",
]
```

For each new paper found:
1. Summarize key finding (1 paragraph)
2. Score relevance to NexusMind (0-1)
3. Score implementation difficulty (0-1)
4. Score expected improvement (0-1)
5. If relevance > 0.7 AND difficulty < 0.6 → create proposal

Proposals stored in `proposals/research/` as markdown files:
```
# Proposal: Implement LoRA-Flow for Dynamic Personality Mixing
Date: 2026-04-01
Source: arXiv 2025.xxxxx
Relevance: 0.9
Difficulty: 0.4
Expected Improvement: Replace 6 fixed archetypes with continuous personality space

## Summary
LoRA-Flow allows dynamic weight mixing between multiple LoRA adapters at inference time...

## Implementation Plan
1. Install lora-flow library
2. Modify LLMService to accept personality vector instead of archetype string
3. At inference: mix adapters based on user's exact Big Five scores
4. Expected: more nuanced personality expression, no archetype bucketing

## Risks
- May increase inference latency by 50-100ms
- Requires evaluation across all personality combinations
```

## Loop 4: Code Evolution (Weekly, Human-Approved)

### Code Improvement Agent
Runs every Monday. Monitors metrics, identifies underperformers, proposes fixes.

**Step 1 — Monitor:** Collect per-function metrics from Langfuse + app logs:
- Conversation quality scores (trending up or down?)
- Teach-back Bloom progression rates
- Verification Council acceptance rate
- Memory retrieval relevance scores (Qdrant search quality)
- Latency per service function
- Error rates per endpoint

**Step 2 — Identify:** Flag functions where metrics degraded this week:
"memory.retrieve_memories() relevance dropped from 0.82 to 0.71"

**Step 3 — Research:** Search for better approaches via SearXNG:
"Found: HyDE (Hypothetical Document Embeddings) improves retrieval by 15%"

**Step 4 — Propose:** Generate improved code + tests. Create as git branch + PR.
```
Branch: improve/memory-retrieve-hyde
PR Title: [Auto] Add HyDE to memory retrieval (+15% relevance)
PR Body:
  Problem: retrieve_memories relevance dropped 13% this week
  Solution: Implement HyDE — generate hypothetical answer, embed that, search
  Expected: +15% relevance based on published benchmarks
  Tests: tests/unit/test_memory_hyde.py (5 new tests)
  Risk: +50ms latency per retrieval
```

**Step 5 — Wait:** Developer reviews. Merges or rejects. System never auto-deploys code.

### Safe Auto-Adjustments (No Human Needed)
These parameters can be adjusted autonomously because they're safe + reversible:
- Prompt template wording (LLM-generated improvements)
- LoRA hyperparameters (rank, learning rate, iterations)
- Retrieval parameters (top-K, similarity threshold, MMR diversity)
- Conversation phase timing (turn count per phase)
- Background scheduler weights (EXPLORE/RESEARCH/REFINE ratios)
- Verification Council thresholds (Skeptic score boundaries)

### Cost Estimates

| Loop | Frequency | Compute | Monthly Cost |
|------|-----------|---------|-------------|
| Loop 1: Knowledge | Continuous (12/hr) | RunPod LLM + Verification | £9-18 |
| Loop 2: Model micro | Hourly | RunPod A10G burst (3min) | £5-10 |
| Loop 2: Model full | Nightly | RunPod A10G (30min) | £8-12 |
| Loop 3: Research | Weekly | SearXNG + LLM summarize | £0.50 |
| Loop 4: Code | Weekly | LLM analysis + generation | £1 |
| **Total evolution cost** | | | **£24-42/month** |
