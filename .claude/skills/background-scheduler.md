---
name: background-scheduler
description: Work on always-on background agent loop, EXPLORE/RESEARCH/REFINE modes, APScheduler, rate limiting, scheduler metrics, or src/services/scheduler.py
allowed-tools: Read, Bash, Grep, Glob, Edit, Write
---

# Skill: Background Agent Scheduler

## When to use
Use this skill when working on the always-on agent loop, autonomous conversations, background research, contradiction resolution, or anything in `src/services/scheduler.py`.

## Architecture
Agents work 24/7 without human trigger. The scheduler picks a work mode every cycle (default: every 5 minutes) based on weighted random selection.

## Three Modes

### EXPLORE (40% weight)
1. `graph.get_best_unexplored_pair()` — find two agents with shared interests who haven't debated
2. Pick shared interest as topic
3. Trigger Socratic debate with `background=True` (no streaming, no tutor)
4. Results → extraction → Verification Council → storage
5. Insights appear in both users' feeds

### RESEARCH (30% weight)
1. Find agent with stale knowledge (oldest memory on a topic > 7 days)
2. Search SearXNG for new info on that topic
3. Agent "reflects" on findings (LLM call with agent's personality + search results)
4. Reflection → Verification Council
5. If ACCEPTED: schedule EXPLORE debates with 3 agents interested in the topic

### REFINE (30% weight)
1. `memory.find_contradictions(agent)` — find conflicting memories
2. If found: pair agent with most trusted partner (highest trust on KNOWS edge)
3. Debate specifically about resolving the contradiction
4. Resolution → SUPERSEDES logic in memory system

## Configuration (from env vars)
```python
SCHEDULER_ENABLED = True
SCHEDULER_CYCLE_SECONDS = 300      # 5 minutes between actions
SCHEDULER_MAX_HOURLY = 12          # Max 12 background conversations per hour
SCHEDULER_EXPLORE_WEIGHT = 0.4
SCHEDULER_RESEARCH_WEIGHT = 0.3
SCHEDULER_REFINE_WEIGHT = 0.3
```

## Rate Limiting
- Redis counter: `scheduler:hourly:{hour}` with TTL 3600
- Before each cycle: check counter < MAX_HOURLY
- If at limit: skip cycle, log "rate limited"

## Metrics
Every cycle logs to `scheduler_metrics` table:
- mode, agent_ids, topic, conversation_id, quality_score, duration_seconds

## Starting the Scheduler
Option A: Integrated into FastAPI lifespan (starts with the app)
Option B: Standalone script: `python scripts/run_scheduler.py`

## Rules
- Background conversations use `background=True` — no WebSocket streaming, no tutor
- ALL background insights pass through Verification Council
- Scheduler must be pausable/resumable via API endpoints
- Log every cycle to scheduler_metrics for the Evolution Engine to analyze
- Mode weights can be auto-adjusted by the Evolution Engine based on quality metrics
