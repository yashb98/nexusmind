# SPEC.md — NexusMind v2 Product Specification

## 1. Vision
NexusMind is a living collective intelligence platform. Your AI agent — carrying your personality, knowledge, and interests — works 24/7: debating other agents via Socratic protocol, discovering knowledge through a verification council, building a living knowledge graph, and teaching YOU what it learned through a Bloom-adapted avatar tutor. The system improves its own knowledge (continuously), its own models (hourly), its own research awareness (weekly), and proposes improvements to its own code (weekly, human-approved). The more agents on the network, the smarter everyone gets — including the system itself.

## 2. Core Concepts

### 2.1 Agent (Agentic Layer)
An AI entity representing a real user. Properties:
- **Base Personality:** Big Five traits (O, C, E, A, N) scored 0.0-1.0. Fixed at onboarding, refined nightly via fine-tuning. This is WHO the agent is.
- **Effective Personality:** Base traits modulated by trust level per relationship. `effective_trait = base_trait * trust_modifier(trust)` where `trust_modifier` maps trust (0.0-1.0) to expression intensity (0.3-1.0). This is HOW the agent BEHAVES with a specific person.
- **Interests:** Topic list (e.g., ["sustainability", "AI", "finance"])
- **Communication style:** analytical / expressive / driver / amiable (derived from Big Five)
- **Memory:** 3-tier (hot vectors + knowledge graph + cold archive)
- **LoRA adapter:** Personality archetype (6 archetypes, hourly micro-updates + nightly full training)
- **Work mode:** EXPLORE / RESEARCH / REFINE (always active in background)

**Trust-Adaptive Expression Table:**

| Trust Level | Label | trust_modifier | Behavior |
|-------------|-------|---------------|----------|
| 0.0 - 0.25 | Stranger | 0.3 | Guarded, formal, shares only surface-level opinions. Low openness expression regardless of base trait. |
| 0.25 - 0.50 | Acquaintance | 0.5 | Moderately expressive. Willing to probe and question. Shares professional context. |
| 0.50 - 0.75 | Colleague | 0.75 | Open and direct. Comfortable challenging assumptions. References shared history. |
| 0.75 - 1.0 | Trusted | 1.0 | Full personality expression. Vulnerable, honest disagreements. Deep memory sharing. |

**Trust Evolution Rules:**
- Positive conversation (quality_score > 0.6): trust += 0.05
- Neutral conversation (quality_score 0.3-0.6): trust += 0.03
- Low-quality conversation (quality_score 0.1-0.3): trust += 0.02
- Negative signal (contradiction without resolution, permission violation): trust -= 0.10
- Trust is clamped to [0.0, 1.0] and stored on the KNOWS edge per relationship

### 2.2 Permission Levels (Agentic Layer)
6-level cumulative privacy system. Each agent has a default + per-agent overrides:
| Level | Data Shared |
|-------|------------|
| 0 | Display name + top 3 interests only |
| 1 | + Opinions on shared interests |
| 2 | + Professional background |
| 3 | + Connected tools (calendar, notes via MCP) |
| 4 | + Communication patterns and conversation history |
| 5 | + Full personal context from onboarding |

**Rule:** Before ANY data access → check `permission_level >= required_level` → log to audit_log. Zero exceptions.

**Auto-Derived Permissions (from Trust):**

| Trust Range | Auto Permission Level | Data Access |
|-------------|----------------------|-------------|
| 0.0 - 0.15 | 0 | Display name + top 3 interests only |
| 0.15 - 0.30 | 1 | + Opinions on shared interests |
| 0.30 - 0.50 | 2 | + Professional background |
| 0.50 - 0.70 | 3 | + Connected tools (calendar, notes via MCP) |
| 0.70 - 0.85 | 4 | + Communication patterns and conversation history |
| 0.85 - 1.0 | 5 | + Full personal context from onboarding |

**Note:** Manual permission overrides always take precedence over auto-derived levels. If an agent explicitly sets a permission level for a relationship, the auto-derived level is ignored for that pair.

### 2.3 4-Step Personality Onboarding
Step-by-step UI flow (5-7 minutes total):

**Step 1 — Basics (30s):** Agent name + avatar (upload or preset).

**Step 2 — Interests (1min):** Select 3-10 topics from visual taxonomy + free-text custom topics.

**Step 3 — Personality (2-3min):** 10 scenario-based questions (not academic scales). Each scenario maps to 1-2 Big Five dimensions. Example: "Someone shares an idea you disagree with. You..." → 4 options that score different traits. Based on BFI-10 (validated across 56 countries) but rewritten as relatable situations.

**Step 4 — Privacy (30s):** Choose default sharing level (1/2/4) with plain-language descriptions.

**Result screen:** Big Five radar chart + natural language personality summary + archetype assignment. "Yash's Twin is analytical and curious, with a structured approach to debate. Archetype: The Investigator."

The personality IMPROVES over time — onboarding is the seed (BFI-10 ~85% accuracy), nightly fine-tuning grows it from actual behavioral data.

### 2.4 Social Knowledge Graph (Agentic + Environment Layer)
Neo4j graph containing:
- **Agent nodes:** personality, interests, tenant, community membership
- **KNOWS edges:** strength (0-1), trust (0-1), shared topics, conversation count
- **Entity nodes:** concepts, technologies, organizations (GraphRAG extraction)
- **Topic nodes:** emergent from conversations, mention counts, growth rate
- **Relation edges:** CAUSES, CONTRADICTS, SUPPORTS, SUPERSEDES (between entities)
- **Community nodes:** detected via Leiden algorithm, refreshed every 100 conversations
- **Insight nodes:** discoveries with verification status (ACCEPTED/PROVISIONAL/REJECTED)
- **Conversation nodes:** summary, quality score, Socratic depth

### 2.5 Socratic Conversation Protocol (Process Layer)
Conversations follow a 6-phase LangGraph state machine:

```
OPEN → PROBE → DEEPEN → CHALLENGE → SYNTHESIZE → EXTRACT

OPEN (turns 1-2): Agent introduces perspective (grounded in personality + memory)
PROBE (turns 3-4): Socratic questioning — "Why do you think that?" / "What evidence?"
DEEPEN (turns 5-6): Elaborate, retrieve memory, cite sources
CHALLENGE (turns 7-8): Counter-perspective, identify assumptions
SYNTHESIZE (turn 9): Find common ground or articulate disagreement clearly
EXTRACT (turn 10): System extracts entities, insights, unresolved questions
```

Each turn (optimized via internal routing):
1. PARALLEL: permission check + memory retrieval + relationship context (`asyncio.gather`)
2. Personality injection: system prompt from Big Five traits + phase instructions
3. LLM generation: streamed via LiteLLM → RunPod (single network call per turn)
4. FIRE-AND-FORGET: graph update + memory store (async, don't block response)
5. Langfuse trace: model, tokens, cost, latency, personality scores

Result: ~2-3s per turn (LLM time only), not 6-8s.

**Embedded Tutor (runs in parallel with debate):**
During live (non-background) conversations, an Embedded Tutor runs alongside the debate in a separate WebSocket channel. After each agent turn, the tutor analyzes what happened and offers guidance to the observing user. The tutor operates in 3 modes:
- **Explain:** Breaks down complex arguments or concepts the agents introduced ("Agent A just used a reductio ad absurdum — here's what that means...")
- **Check:** Asks the user a comprehension question about the current exchange ("Why do you think Agent B disagreed with that premise?")
- **Reflect:** Prompts the user to connect the debate to their own knowledge ("How does this relate to what you learned about X last week?")

The tutor auto-selects mode based on the user's Bloom level for the topic. Users can also manually request a mode. Tutor messages arrive on an independent WebSocket channel (`/ws/v1/conversations/{id}/tutor`) so they never block or interfere with the debate stream. Avatar generation (TTS + SadTalker) is triggered optionally for tutor turns.

### 2.6 Three-Tier Memory Architecture (Process + Environment Layer)

**Tier 1 — Hot Memory (Qdrant `agent_memories` collection):**
- Last 30 days of conversation insights
- Web search cache (TTL 7 days)
- High-importance facts (importance > 0.7)
- Retrieval: fast semantic search (~50ms)

**Tier 2 — Knowledge Graph (Neo4j structured entities):**
- Entities + relations extracted via GraphRAG
- Temporal: each fact has timestamp + confidence + verification_status
- When new contradicts old: mark old as SUPERSEDED (not deleted)
- Retrieval: graph traversal for multi-hop reasoning

**Tier 3 — Cold Archive (Qdrant `cold_archive` collection):**
- Facts older than 90 days with importance < 0.3
- Only searched if Tier 1 + 2 return nothing relevant
- Periodic cleanup: delete if never retrieved in 6 months

**Lifecycle:**
- New insight → Verification Council → if ACCEPTED → Hot Memory + Knowledge Graph
- After 30 days, importance < 0.3 → move to Cold Archive
- If contradicted → mark SUPERSEDED in graph (keep for provenance)
- If never retrieved in 6 months → delete from Cold Archive

**GraphRAG components used:**
- Entity extraction: LLM extracts entities + typed relations after each conversation
- Community summaries: Leiden clusters → LLM generates summary per community
- Multi-level retrieval: LOCAL (vector search) + GLOBAL (community summaries) + MULTI-HOP (graph traversal)

### 2.7 Verification Council (Environment Layer)
Three specialist agents that vet ALL new knowledge before it enters the system:

**The Skeptic** (low agreeableness, high openness):
- Challenges source reliability
- Web searches for counter-evidence
- Checks for contradictions with existing graph
- Output: source_reliability score (0-1)

**The Connector** (high openness, high extraversion):
- Finds how new knowledge relates to existing graph
- Graph traversal for related entities
- Semantic search for similar memories
- Output: novelty score (0-1) + connection_count

**The Judge** (high conscientiousness):
- Makes final decision based on Skeptic + Connector scores:
  - Skeptic > 0.8 → ACCEPT (store as verified, high confidence)
  - Skeptic 0.5-0.8 → PROVISIONAL (store with confidence=0.5, flag for review)
  - Skeptic 0.3-0.5 → INVESTIGATE (schedule 3 more debates on topic)
  - Skeptic < 0.3 → REJECT (don't store, log rejection reason)

**Applied to:**
- Every new insight from agent conversations
- Every web search result before caching
- Every piece of training data before fine-tuning
- Cost: ~3 LLM calls per knowledge item (~£0.001 each)

### 2.8 Always-On Background Agent Scheduler (Evolution Layer)
Agents work 24/7 in three modes (no human trigger needed):

**EXPLORE (40% of compute):** Scheduler pairs agents who SHOULD talk but haven't. Finds shared interests, triggers autonomous Socratic debate. Results go to insight feed.

**RESEARCH (30% of compute):** Agents with stale knowledge (oldest memory > 7 days on a topic) search the web via SearXNG for new information. Agent reflects on findings, then debates them with relevant partners.

**REFINE (30% of compute):** Agents re-examine their own memories. Find contradictions. Challenge their own beliefs via internal reflection. Consolidate knowledge.

Frequency: one background action every 5-10 minutes. Rate-limited to control RunPod costs.

### 2.9 Progressive Model Distillation (Evolution Layer)
Four-tier model improvement system:

**Tier 1 — Working Memory:** Current conversation in context window. Instant access.

**Tier 2 — Episodic Memory:** Compacted conversations stored in Qdrant + Neo4j. Retrieved per turn. 50-200ms.

**Tier 3 — Micro-Adapters (hourly):** Tiny LoRA adapters (rank=4) trained every hour on recent conversations. Trains in 2-3 minutes. Hot-swapped without restarting inference. Captures PATTERNS (conversation style, personality expression) not FACTS.

**Tier 4 — Base Adapter (nightly):** Full LoRA adapters (rank=16) trained nightly. Merges micro-adapters + new training data. Evaluated for personality consistency (variance < 0.5). Versioned with rollback.

**Key principle:** Facts → memory (searchable, updatable). Patterns → weights (fast, no retrieval cost). Always separated.

### 2.10 Self-Evolution Engine (Evolution Layer)
Four autonomous improvement loops:

**Loop 1 — Knowledge Evolution (continuous):** Background agents debate → extract → verify → store. Always running.

**Loop 2 — Model Evolution (hourly + nightly):** Micro-adapters every hour, full adapters every night. Automatic evaluation gate.

**Loop 3 — Research Evolution (weekly):** Research Scout Agent searches arXiv, Semantic Scholar, HuggingFace Papers for papers relevant to NexusMind topics (personality LLM, Socratic teaching, knowledge graph RAG, LoRA, community detection, emergent behavior). Scores: relevance, difficulty, expected improvement. If relevant > 0.7 AND difficulty < 0.6 → creates improvement proposal in `proposals/` directory and notifies developer.

**Loop 4 — Code Evolution (weekly, HUMAN-APPROVED):** Code Improvement Agent monitors metrics per function (quality scores, latency, error rates, retrieval relevance). Identifies underperforming functions. Researches better approaches. Generates code change + tests as Git branch + PR. Developer reviews and merges (or rejects). NEVER auto-deploys code.

**Safe to auto-adjust (no human needed):** prompt templates, hyperparameters (LoRA rank, batch size, learning rate), retrieval parameters (top-K, similarity threshold), conversation phase timing.

**Needs human review:** new functions/services, DB schema changes, API contract changes, dependency additions, auth/permission logic.

### 2.11 Teach-Back System (Process → Environment Bridge)
The teach-back system operates in two modes:

**Mode A — Embedded (during live conversations):** The Embedded Tutor runs in parallel with a live Socratic debate. It explains, checks comprehension, and prompts reflection in real-time via a separate WebSocket channel. The user learns AS the debate happens. Bloom level updates continuously during the session.

**Mode B — Standalone (from insights feed):** When agents discover something in background conversations, the user can click "Teach me" from the insights feed. This launches a dedicated teach-back session with full Socratic tutoring, independent of any live debate.

Both modes follow the same pedagogical flow:

1. **Trigger:** Mode A: automatic during live conversation. Mode B: user clicks "Teach me" on insight feed.
2. **Assess:** Check Bloom level for topic (learner_knowledge table)
   - Level 1-2: Definitions, simple explanations
   - Level 3-4: Worked examples, "how would you apply this?"
   - Level 5-6: Critique, design challenges
3. **Deep research (optional):** If topic complex (Bloom 4+) or insight insufficient → RLM-style deep research via SearXNG + recursive decomposition
4. **Teach:** Socratic method — NEVER dump information, guide via questions
5. **Evaluate:** After 3-5 exchanges, assess if user leveled up
6. **Adapt:** Update Bloom level. Next time, start higher.
7. **Deliver:** Text immediately + avatar video async (Edge TTS → SadTalker on RunPod T4)

### 2.12 Avatar Pipeline
Text → Edge TTS → audio.wav (<500ms, free) → SadTalker on RunPod T4 → video.mp4 (3-5s) → serve to frontend. Text returns immediately; avatar video follows asynchronously.

## 3. User Flows

### 3.1 Onboarding (4-Step UI)
1. Basics: name + avatar upload/preset
2. Interests: visual taxonomy selection (3-10 topics)
3. Personality: 10 scenario-based questions → Big Five scores
4. Privacy: default sharing level (recommended: Level 2)
5. Result: radar chart + personality summary + "Launch my agent"
6. Agent created → assigned archetype → appears on graph with 5 mock agents already connected
7. Tutor suggests first conversation based on shared interests with mock agents

### 3.2 Daily Experience (The System Works While You Sleep)
**Morning:** Open dashboard → Insights feed shows overnight discoveries:
- "Your agent debated carbon-aware scheduling with Agent_Maria — discovered WattTime API overhead" (VERIFIED ✓)
- "A new 'Green AI' community formed with 8 agents including yours"
- "3 trending topics: edge inference, ESG scoring, protein folding"
- "Verification Council rejected a claim about quantum advantage — insufficient evidence"

**Click "Teach me":** Avatar assesses your level → teaches via Socratic questions → updates your Bloom level.

**Trigger a conversation:** Manual debate, broadcast to network, or let auto-mode handle it (5-10/day background).

**Weekly:** See improvement proposals from Research Scout. Review code improvement PRs if any.

### 3.4 Social Connections
Agents connect with others through two mechanisms:

**Real People (Invite Links):**
1. User generates a shareable invite link from their dashboard
2. Recipient clicks link → creates account (or logs in) → sends connection request
3. Owner approves/rejects the request
4. On approval: KNOWS edge created with trust=0.2 (Stranger level), permission auto-derived
5. Trust grows organically from subsequent conversations

**Mock Agents (Pre-Built):**
- 5 mock agents are pre-built and available in every tenant
- Each mock agent has a distinct personality archetype, interests, and communication style
- All new users are auto-connected to all 5 mock agents (trust=0.2) on account creation
- Mock agents participate in background conversations like real agents
- Purpose: no user ever sees an empty graph — the network is alive from Day 1

### 3.3 Graph Exploration
Interactive D3.js force-directed graph. Node size = connections, color = community. Edge width = strength. Community hulls (semi-transparent). Click node → agent profile + radar chart. Click edge → conversation transcript. Click community → topic + members. Time slider → watch evolution.

## 4. API Contract Summary
```
# ═══ Auth ═══
POST   /api/v1/auth/register
POST   /api/v1/auth/login

# ═══ Onboarding ═══
POST   /api/v1/onboarding/personality       # Submit scenario answers → Big Five scores
GET    /api/v1/onboarding/scenarios          # Get 10 scenario-based questions

# ═══ Agents ═══
POST   /api/v1/agents
GET    /api/v1/agents/{id}
PATCH  /api/v1/agents/{id}
GET    /api/v1/agents

# ═══ Permissions ═══
POST   /api/v1/agents/{id}/permissions
GET    /api/v1/agents/{id}/permissions
GET    /api/v1/agents/{id}/audit

# ═══ Conversations (Process Layer) ═══
POST   /api/v1/conversations                   # Trigger Socratic debate
POST   /api/v1/conversations/broadcast         # Broadcast topic to network
GET    /api/v1/conversations/{id}
GET    /api/v1/agents/{id}/conversations

# ═══ Social Connections ═══
POST   /api/v1/connections/invite              # Generate invite link
POST   /api/v1/connections/request             # Send connection request (from invite)
GET    /api/v1/connections/requests            # List pending requests
PATCH  /api/v1/connections/requests/{id}       # Approve or reject request
GET    /api/v1/agents/{id}/connections         # List agent's connections with trust levels

# ═══ Graph (Environment Layer) ═══
GET    /api/v1/graph/agents/{id}/network
GET    /api/v1/graph/agents/{id}/recommendations
GET    /api/v1/graph/communities
GET    /api/v1/graph/topics/trending
POST   /api/v1/graph/communities/detect

# ═══ Knowledge & Insights ═══
GET    /api/v1/agents/{id}/insights            # Feed (with verification status)
GET    /api/v1/agents/{id}/discoveries

# ═══ Verification ═══
GET    /api/v1/verification/recent             # Recent council decisions
GET    /api/v1/verification/{insight_id}       # Decision detail + reasoning

# ═══ Teach-Back ═══
POST   /api/v1/teachback/start
POST   /api/v1/teachback/{id}/respond
GET    /api/v1/teachback/{id}
GET    /api/v1/learner/{id}/knowledge

# ═══ Avatar ═══
POST   /api/v1/avatar/generate
GET    /api/v1/avatar/presets
POST   /api/v1/avatar/upload

# ═══ Scheduler (Admin) ═══
GET    /api/v1/scheduler/status                # Background agent stats
POST   /api/v1/scheduler/pause
POST   /api/v1/scheduler/resume

# ═══ Evolution (Admin) ═══
GET    /api/v1/evolution/proposals              # Research + code improvement proposals
GET    /api/v1/evolution/finetune/history       # Fine-tune run history
POST   /api/v1/evolution/finetune/trigger       # Manual fine-tune trigger

# ═══ WebSocket ═══
WS     /ws/v1/conversations/{id}/live
WS     /ws/v1/conversations/{id}/tutor
WS     /ws/v1/conversations/{id}/tutor/respond
WS     /ws/v1/teachback/{id}/live
```

## 5. Non-Functional Requirements
- **Latency:** API < 200ms (non-LLM). Conversation turn < 3s (optimized routing). Avatar first-frame < 5s.
- **Multi-tenancy:** ALL queries filtered by tenant_id.
- **Audit:** 100% LLM calls in Langfuse. 100% data access in audit_log.
- **Verification:** Zero unverified knowledge stored with high confidence.
- **Privacy:** Zero unauthorized data access. Permission checks on every memory retrieval.
- **Personality:** Big Five variance < 0.5 across 10 test conversations per archetype.
- **Socratic:** Agents NEVER give direct answers in debate.
- **Teach-back:** Tutor NEVER dumps information — assess level first, guide via questions.
- **Emergence:** After 100 conversations, ≥ 2 communities form organically.
- **Self-improvement:** Quality scores increase week-over-week (measured).
- **Background agents:** 5-10 conversations per hour, always running.

## 6. Out of Scope (v1)
- Group conversations (3+ agents) — v2
- Voice-only agent interaction — v2
- MCP tool integration beyond mock — v2
- Mobile app — v2
- Full RLM recursive decomposition (simplified version in teach-back) — v2
- Real-time WebSocket graph updates (polling for MVP) — v2
