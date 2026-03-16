# NexusMind Scratchpad
> Claude: Update this file as you work. This persists across sessions.

## Current State
- Migration step: STEP 5 COMPLETE (embedded tutor)
- Last session: 2026-03-16
- Branch: main

## What's Been Done
- [x] Step 1: Critical bugs fixed (CORS, graph, agent loading, tooltips, empty states, agent picker)
- [x] Step 2: Adaptive onboarding (question banks, dynamic selection, domain modifiers, confidence)
- [x] Onboarding flow (4 steps: basics, interests, adaptive scenarios, privacy)
- [x] Dashboard layout (graph panel + tabbed right panel)
- [x] Agent tab with personality radar chart
- [x] Graph view with D3.js — shows user agent + 5 mock agents + edges
- [x] Graph node hover tooltips (name, archetype, interests, trust bar)
- [x] Teach Me tab with insight-based tutor sessions
- [x] Privacy dashboard shell (tables exist, no data)
- [x] Evolution dashboard shell (scheduler status, tabs)
- [x] Profile page (/profile) with user info, agent settings, personality chart
- [x] Connection service (invite, request, accept/reject)
- [x] v2.1 changelog implemented (trust-adaptive, embedded tutor, mock agents)

## Step 2 Details (Adaptive Onboarding)
- src/data/question_banks.py: 110 questions, 21 domains + 5 universal, 1374 lines
- GET /api/v1/onboarding/questions?interests=X,Y — dynamic question selection
- POST /api/v1/onboarding/personality/adaptive — scoring with domain modifiers + confidence
- Frontend: domain tags on questions, confidence bar, estimated time, domain insights on result screen
- DB: agents table has domain_modifiers (JSON), personality_confidence (Float), questions_answered (Int)
- Triple-layer personality: base × domain × trust

## Tests
- 123 tests passing (all unit + integration)

## What's Next (Migration Steps)
1. ~~Fix critical bugs~~ DONE
2. ~~Adaptive onboarding~~ DONE
3. ~~Conversation modes~~ DONE
4. ~~Trust-adaptive personality~~ DONE
5. ~~Embedded tutor~~ DONE
6. Profile section (context/PROFILE_SECTION.md)
7. Social layer — groups, events, feed (context/SOCIAL_LAYER.md)
8. Mock agents + connections (context/MOCK_AGENTS_CONNECTIONS.md)

## Discoveries
- Kimi API (moonshot.cn) used for LLM — key in .env as KIMI_API_KEY
- Mock agents are seeded on DB migration (5 agents: Aria, Marcus, Priya, James, Luna)
- Neo4j graph query needed null filtering for OPTIONAL MATCH edges
- Agent creation auto-connects to mock agents via KNOWS edges in Neo4j
- Question selection: 2-3 per interest, gap-filling with universal fallbacks
