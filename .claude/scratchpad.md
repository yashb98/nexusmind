# NexusMind Scratchpad
> Claude: Update this file as you work. This persists across sessions.

## Current State
- Migration step: STEP 1 COMPLETE (critical bugs fixed)
- Last session: 2026-03-16
- Branch: main

## What's Been Done
- [x] Onboarding flow (4 steps: basics, interests, 10 scenarios, privacy)
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

## Step 1 Bugs — ALL FIXED
- [x] BUG 1: CORS/Axios — CORS middleware configured, API base URL correct, JWT interceptor works
- [x] BUG 2: Graph not showing — Fixed Neo4j query to filter null edges/neighbors, KNOWS edges auto-created on agent creation
- [x] BUG 3: Wrong agent on dashboard — Dashboard loads current user's agent via /api/v1/auth/me
- [x] BUG 4: Graph tooltips — Hover shows name, archetype, communication style, interests, trust level
- [x] BUG 5: Empty states — All tabs have helpful empty state messages
- [x] BUG 6: Agent picker — Modal with agent list, topic input, Start Debate button

## Tests
- 122 tests passing (all unit + integration)
- Test fix: added `is_mock` and `default_trust_for_strangers` to test mock_row, added `mock_pg.fetch` for auto-connect

## What's Next (Migration Steps)
1. ~~Fix critical bugs~~ ✅ DONE
2. Adaptive onboarding (context/ADAPTIVE_ONBOARDING.md)
3. Conversation modes + streaming (context/CONVERSATION_MODES.md)
4. Trust-adaptive personality (context/TRUST_ADAPTIVE.md)
5. Embedded tutor (context/EMBEDDED_TUTOR.md)
6. Profile section (context/PROFILE_SECTION.md)
7. Social layer — groups, events, feed (context/SOCIAL_LAYER.md)
8. Mock agents + connections (context/MOCK_AGENTS_CONNECTIONS.md)

## Discoveries
- Kimi API (moonshot.cn) used for LLM — key in .env as KIMI_API_KEY
- Mock agents are seeded on DB migration (5 agents: Aria, Marcus, Priya, James, Luna)
- Neo4j graph query needed null filtering for OPTIONAL MATCH edges
- Agent creation auto-connects to mock agents via KNOWS edges in Neo4j
