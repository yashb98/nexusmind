---
name: self-evolution
description: Work on research scout, code improvement agent, auto-parameter adjustment, evolution proposals, or src/services/evolution.py
allowed-tools: Read, Bash, Grep, Glob, Edit, Write
---

# Skill: Self-Evolution Engine

## When to use
Use this skill when working on the research scout, code improvement agent, auto-parameter adjustment, or anything in `src/services/evolution.py`.

## Four Improvement Loops

### Loop 1: Knowledge Evolution (continuous)
Handled by background scheduler + verification council. See those skills.

### Loop 2: Model Evolution (hourly + nightly)
Handled by fine-tuning pipeline. See that skill.

### Loop 3: Research Scout (weekly — Sunday midnight)
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
```

For each topic: search SearXNG → for each new paper → LLM summarizes → score relevance (0-1), difficulty (0-1), improvement (0-1) → if relevance > 0.7 AND difficulty < 0.6 → create proposal.

Store in: `evolution_proposals` table (type='research') + `proposals/research/{date}_{title}.md`

### Loop 4: Code Improvement Agent (weekly — Monday midnight)
1. Pull metrics from Langfuse + scheduler_metrics
2. Flag functions where metrics degraded > 10% this week
3. Research solutions via SearXNG
4. Generate improved code + tests via LLM
5. Store in: `evolution_proposals` table (type='code')
6. NEVER auto-deploy. Human reviews.

## Safe Auto-Adjustments (no human needed)
These are reversible and low-risk:
- Prompt template wording (A/B test 10 conversations)
- LoRA hyperparameters (rank, learning rate)
- Retrieval parameters (top-K, similarity threshold)
- Conversation phase timing (turns per phase)
- Scheduler mode weights (based on quality metrics)
- Verification thresholds (based on acceptance rate)

Log every adjustment with before/after values. Rollback capability required.

## Needs Human Approval
- New functions or services
- Database schema changes
- API contract changes
- Dependency additions
- Auth/permission logic changes

## Rules
- Research scout: check for duplicates (don't propose same paper twice)
- Code agent: include problem, solution, expected improvement, tests, and risk
- Auto-adjustments: A/B test before committing (run N conversations with old vs new)
- ALL proposals logged to evolution_proposals table with status tracking
