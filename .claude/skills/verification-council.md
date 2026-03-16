---
name: verification-council
description: Work on knowledge verification, Skeptic/Connector/Judge pipeline, insight quality scoring, or src/services/verification.py
allowed-tools: Read, Bash, Grep, Glob, Edit, Write
---

# Skill: Verification Council

## When to use
Use this skill when working on knowledge verification, the Skeptic/Connector/Judge pipeline, or anything in `src/services/verification.py`.

## Architecture
Every new piece of knowledge passes through 3 specialist LLM agents before storage. This is the system's immune system.

### Pipeline
```
New insight enters
       │
       ├──→ Skeptic (PARALLEL with Connector)
       ├──→ Connector (PARALLEL with Skeptic)
       │
       ▼
    Judge (after both complete)
       │
       ▼
    Decision: ACCEPT / PROVISIONAL / INVESTIGATE / REJECT
```

### Agent Roles

**Skeptic:**
- Searches SearXNG for counter-evidence
- Checks Neo4j graph for contradictions
- LLM scores source_reliability (0-1)
- Output: SkepticResult(score, reasoning, counter_evidence[], contradictions[])

**Connector:**
- Neo4j graph traversal for related entities
- Qdrant semantic search for similar memories
- LLM scores novelty (0-1) and lists connections
- Output: ConnectorResult(score, novelty, connections[], related_entities[])

**Judge:**
- Uses Skeptic + Connector results
- Decision matrix:
  - Skeptic score > 0.8 → ACCEPT (confidence=0.9)
  - Skeptic 0.5-0.8 → PROVISIONAL (confidence=0.5)
  - Skeptic 0.3-0.5 → INVESTIGATE (schedule more debates)
  - Skeptic < 0.3 → REJECT (don't store, log reason)

### Rules
- Skeptic and Connector ALWAYS run in parallel: `asyncio.gather(run_skeptic(), run_connector())`
- ALL decisions logged to `verification_decisions` table
- REJECTED insights are NEVER stored in Neo4j or Qdrant
- Training data for fine-tuning MUST be filtered: only ACCEPTED conversations
- Thresholds are configurable via env vars (VERIFICATION_SKEPTIC_ACCEPT_THRESHOLD etc.)
- Each verification costs ~3 LLM calls (~£0.001)

### DSPy Integration
The Skeptic, Connector, and Judge are implemented as DSPy modules (not raw prompts).
This guarantees structured output and enables auto-optimization.

Modules in src/dspy_modules/verification.py:
- SkepticModule: claim, source, counter_evidence, contradictions → reliability_score, reasoning, is_reliable
- ConnectorModule: claim, related_entities, similar_memories → novelty_score, connections, reasoning
- JudgeModule: claim, skeptic_score, skeptic_reasoning, connector_score, connector_reasoning → decision, confidence, reasoning

Services call DSPy modules instead of raw LLM calls.
Optimization: run `python -m src.dspy_modules.optimizers optimize_verification` with 20 labeled examples.

### Applied To
1. Every insight extracted from agent conversations
2. Every web search result before caching in knowledge_base
3. Every piece of training data before fine-tuning
