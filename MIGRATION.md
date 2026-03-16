# MIGRATION.md — NexusMind v2 → v3 (Living Social World)
# 
# READ THIS FILE FIRST. It tells you what to change and in what order.
# Each migration step is SAFE — it adds without destroying.
# Run tests after each step. If tests fail, fix before moving on.
#
# RULE: NEVER delete existing working code. Only ADD, MODIFY, or EXTEND.
# RULE: NEVER change database column types on existing tables. Only ADD columns.
# RULE: NEVER rename existing API endpoints. Only ADD new ones.
# RULE: Run existing tests after each step to verify nothing broke.

## MIGRATION ORDER (do these in sequence):

### STEP 1: Fix Critical Bugs (do this FIRST before any new features)
Read: context/FIX_CRITICAL_BUGS.md
What: Fix Axios CORS error, fix graph not showing, fix wrong agent loading
Tests: curl localhost:8000/health works, graph shows nodes, correct agent loads
DO NOT proceed until these work.

### STEP 2: Adaptive Onboarding (question banks + domain personality)
Read: context/ADAPTIVE_ONBOARDING.md
What: Add question banks per interest, dynamic question selection, domain-specific personality modifiers, confidence scoring, "Go Deeper" adaptive follow-ups
DB changes: ADD columns to agents table (domain_modifiers, personality_confidence, questions_answered)
New files: src/data/question_banks.py, updated onboarding service + routes
Tests: Existing onboarding tests still pass + new tests for dynamic selection

### STEP 3: Conversation Modes + Streaming
Read: context/CONVERSATION_MODES.md
What: Add 8 conversation modes beyond Socratic, token-by-token WebSocket streaming, dynamic turn order for multi-agent
DB changes: ADD column to conversations table (mode)
Modified: src/services/conversation.py (add modes, add streaming)
Tests: Existing conversation tests still pass + new mode tests

### STEP 4: Trust-Adaptive Personality
Read: context/TRUST_ADAPTIVE.md
What: Personality expression adapts per-relationship based on trust. Auto-derived permissions from trust.
DB changes: ADD columns to agents table (default_trust_for_strangers). ADD trust_history to KNOWS edges.
Modified: src/services/personality.py, src/services/permission.py, conversation.py finalize node
Tests: Existing personality tests still pass + new trust modifier tests

### STEP 4.5: DSPy Modules (Structured LLM Optimization)
Read: .claude/skills/dspy-modules.md
What: Add DSPy modules for Verification Council, knowledge extraction, Bloom assessment, and quality scoring. Replace raw LLM calls with optimized structured modules. Create 20 labeled examples per module. Run optimization.
New files: src/dspy_modules/ (verification.py, extraction.py, assessment.py, optimizers.py, data/*.json)
Modified: src/services/verification.py (swap raw LLM → DSPy), src/services/knowledge.py (swap extraction), src/services/teachback.py (swap Bloom assessment), src/services/conversation.py (swap quality scoring in finalize)
Install: `uv add dspy`
Tests: Existing service tests still pass (interfaces unchanged) + new tests for DSPy module accuracy
IMPORTANT: DSPy is an INTERNAL implementation detail. Service interfaces do NOT change.

### STEP 5: Embedded Tutor During Conversations
Read: context/EMBEDDED_TUTOR.md
What: Tutor runs in parallel panel during live debates. 4 modes: explain/check/reflect/observe.
New WebSocket channels. Bloom assessment during conversation.
New files: tutor WebSocket handler, embedded tutor prompt
Modified: conversation.py (add parallel tutor node), frontend ConversationViewer (split panel)
Tests: Conversation still works without tutor (background mode) + tutor generates commentary

### STEP 6: Profile Section
Read: context/PROFILE_SECTION.md
What: Full profile page with account settings, agent settings, privacy controls, tutor preferences, learning progress, danger zone.
New files: src/routes/profile.py, frontend profile page
New endpoints: GET/PATCH /users/me, retake quiz, connection management
Tests: Profile loads, settings save, interests update

### STEP 7: Social Layer (Groups + Events + Feed)
Read: context/SOCIAL_LAYER.md
What: Groups (interest/skill/project/social), Events (hackathon/debate/research/game), Feed, Discovery, multi-agent group conversations, navigation redesign.
DB changes: New tables (groups, group_members, events, event_participants, event_teams, feed_items)
New Neo4j nodes: Group, Event
New files: Multiple new services, routes, and frontend pages
Tests: Group CRUD, event lifecycle, multi-agent conversation, feed aggregation

### STEP 8: Mock Agents + Connection System
Read: context/MOCK_AGENTS_CONNECTIONS.md  
What: 5 rich mock agents, connection requests, invite links, auto-connect on signup.
DB changes: New table (connection_requests), ADD is_mock to agents
New files: src/routes/connections.py, src/services/connection_service.py
Tests: Mock agents created on seed, new user auto-connected, connection request flow

---

## HOW TO USE THIS WITH CLAUDE CODE:

For each step, open Claude Code and say:

"Read MIGRATION.md step {N} and the referenced context file. 
Then implement the changes. Run existing tests after each change 
to make sure nothing broke. Then run the new tests."

One step per Claude Code session. Commit after each step.
