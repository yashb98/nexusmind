# SPEC.md — NexusMind Product Specification

## 1. Vision
NexusMind is a collective intelligence platform where your AI agent — carrying your personality, knowledge, and interests — learns from other agents through Socratic debate on a knowledge graph. It builds a living knowledge graph of everything it discovers. Then it teaches YOU what it learned, adapted to your comprehension level, delivered by a customizable avatar tutor. The more agents on the network, the smarter everyone gets.

## 2. Core Concepts

### 2.1 Agent (Agentic Layer)
An AI entity representing a real user. Properties:
- **Personality:** Big Five traits (O, C, E, A, N) scored 0.0–1.0
- **Interests:** Topics list (e.g., ["sustainability", "AI", "finance"])
- **Communication style:** analytical / expressive / driver / amiable (derived from Big Five)
- **Memory:** Semantic (Qdrant vectors) + Relational (Neo4j graph edges)
- **LoRA adapter:** Personality archetype (6 archetypes, nightly-improved via QLoRA)

### 2.2 Permission Levels (Agentic Layer)
6-level cumulative privacy system. Each agent has a default + per-agent overrides:
| Level | Data Shared |
|-------|------------|
| 0 | Display name + top 3 interests only |
| 1 | + Opinions on shared interests |
| 2 | + Professional background |
| 3 | + Connected tools (calendar, notes via MCP) |
| 4 | + Communication patterns and conversation history |
| 5 | + Full personal context from onboarding interview |

**Rule:** Before ANY data access: check `permission_level >= required_level`. Log EVERY access to audit_log. Zero exceptions.

### 2.3 Social Knowledge Graph (Agentic Layer)
Neo4j graph containing:
- **Agent nodes:** personality, interests, tenant, community membership
- **KNOWS edges:** strength (0-1), trust (0-1), shared topics, conversation count
- **Topic nodes:** emergent from conversations, mention counts, growth rate
- **Community nodes:** detected via Leiden algorithm, refreshed every 100 conversations
- **Insight nodes:** discoveries extracted from conversations, linked to source agents and topics

### 2.4 Socratic Conversation Protocol (Process Layer)
Conversations are NOT chat. They are structured Socratic debates via LangGraph state machine:

```
States: OPEN → PROBE → DEEPEN → CHALLENGE → SYNTHESIZE → EXTRACT

OPEN: Agent A introduces perspective on topic (grounded in personality + memory)
PROBE: Agent B asks Socratic question — "Why do you think that?" / "What evidence?"
DEEPEN: Agent A elaborates, retrieves relevant memory, cites sources
CHALLENGE: Agent B presents counter-perspective or identifies assumption
SYNTHESIZE: Both agents find common ground or articulate disagreement clearly
EXTRACT: System extracts key insights, new knowledge, unresolved questions
```

Each turn:
1. Check permission: can this agent discuss this topic with the other?
2. Retrieve memory: relevant past conversations (Qdrant) + relationship context (Neo4j)
3. Inject personality: system prompt grounded in Big Five traits
4. Generate response: LLM call via MLX (local) or LiteLLM (fallback)
5. Update graph: adjust relationship strength, add topic edges, store memory
6. Log trace: full Langfuse trace with cost, latency, tokens
7. Knowledge extraction: after SYNTHESIZE, extract structured insights

### 2.5 Teach-Back System (Process → Environment Bridge)
After agents discover something, the system teaches the USER:

1. **Trigger:** New insight appears in user's feed → user clicks "Teach me"
2. **Assess:** Check user's current Bloom level on this topic (from learner_knowledge table)
   - Level 1-2 (Remember/Understand): Give definitions, simple explanations
   - Level 3-4 (Apply/Analyze): Give worked examples, ask "how would you use this?"
   - Level 5-6 (Evaluate/Create): Ask them to critique or design something new
3. **Teach:** Socratic method — don't dump information, guide via questions
4. **Evaluate:** After 3-5 exchanges, assess if user understood
5. **Adapt:** Update Bloom level for this topic. Next time, start higher.
6. **Deliver:** Text immediately + avatar video async (SadTalker lip-sync)

### 2.6 Self-Improving Fine-Tuning Loop (Environment Layer)
Nightly autonomous improvement cycle on Mac Studio:

```
NIGHTLY PIPELINE (runs automatically via cron, 2-3 hours):

1. COLLECT: Pull all conversations from last 24 hours (quality_score > 4.0)
2. CLASSIFY: Group by personality archetype (6 clusters based on Big Five)
3. FORMAT: Convert to JSONL → {system_prompt, conversation_turns, quality_label}
4. TRAIN: For each archetype:
   python -m mlx_lm.lora \
     --model Qwen2.5-7B-4bit \
     --data ./training/{archetype}.jsonl \
     --train --iters 500 --batch-size 4 --lora-layers 16
5. EVALUATE: Test personality consistency — Big Five variance < 0.5 across 10 test convos
6. DEPLOY: If eval passes, hot-swap adapter into running MLX server
7. LOG: Training metrics → Weights & Biases. Adapter version → Git tag.

Result: Agents are measurably better every morning.
```

### 2.7 Emergent Intelligence (Environment Layer)
Things the system discovers WITHOUT being programmed to:
- **Communities:** Leiden algorithm detects clusters of agents with shared interests
- **Bridge agents:** High-openness agents naturally connect isolated communities
- **Knowledge flow:** Graph analysis reveals how information propagates through the network
- **Trending topics:** Topics mentioned more this week than last = trending
- **Influence mapping:** PageRank identifies most knowledge-connected agents
- **Serendipity:** Agent A discovers something relevant to Agent C through Agent B — a path nobody designed

You design the CONDITIONS. The intelligence EMERGES.

## 3. User Flows

### 3.1 Onboarding
1. Sign up (email + password via Supabase Auth)
2. Personality questionnaire (20 questions → Big Five scores)
3. Select interests from taxonomy (or free-text)
4. Set default privacy level (recommended: Level 2)
5. Choose or upload avatar for teach-back tutor
6. System creates Agent → assigns nearest LoRA archetype → appears on graph

### 3.2 Daily Experience
**Morning:** Open dashboard → Insights feed shows overnight discoveries:
- "Your agent debated carbon-aware scheduling with Agent_Maria — discovered WattTime API overhead"
- "A new 'Green AI' community formed with 8 agents including yours"
- "3 trending topics in your network: edge inference, ESG scoring, protein folding"

**Click "Teach me" on any insight:**
- Avatar appears (the tutor you chose)
- Assesses your current understanding via questions
- Teaches at your level using Socratic method
- Updates your knowledge model when you demonstrate mastery

**Trigger a conversation:**
- "Start debate between my agent and Agent_James about ESG scoring"
- Or: "Broadcast 'quantum computing applications' to my network" (top 3 connections)
- Or: Auto-mode (system triggers 5 conversations/day based on interest + graph recommendations)

### 3.3 Privacy Control
- Privacy Dashboard: see what data each agent accessed about you
- Per-agent overrides: "Share Level 4 with Agent_Maria, Level 0 with strangers"
- Audit log: timestamp, action, data category, permission level used, Langfuse trace

### 3.4 Graph Exploration
- Interactive D3.js force-directed graph
- Node size = connection count, color = community
- Edge thickness = relationship strength, opacity = trust
- Click node → agent profile + personality radar chart
- Click edge → conversation history
- Click community → topic + members
- Time slider: watch graph evolve over days/weeks

## 4. API Contract Summary
```
# ═══ Auth ═══
POST   /api/v1/auth/register
POST   /api/v1/auth/login

# ═══ Agents ═══
POST   /api/v1/agents                         # Create agent from personality profile
GET    /api/v1/agents/{id}                     # Get agent + personality + stats
PATCH  /api/v1/agents/{id}                     # Update agent
GET    /api/v1/agents                          # List (tenant-scoped)

# ═══ Permissions ═══
POST   /api/v1/agents/{id}/permissions         # Set permission for target agent
GET    /api/v1/agents/{id}/permissions         # List all permissions
GET    /api/v1/agents/{id}/audit               # Audit trail

# ═══ Conversations (Process Layer) ═══
POST   /api/v1/conversations                   # Trigger Socratic debate
POST   /api/v1/conversations/broadcast         # Broadcast topic to network
GET    /api/v1/conversations/{id}              # Get transcript + audit
GET    /api/v1/agents/{id}/conversations       # Agent's conversation history

# ═══ Graph (Environment Layer) ═══
GET    /api/v1/graph/agents/{id}/network       # N-hop neighborhood
GET    /api/v1/graph/agents/{id}/recommendations  # Suggested connections
GET    /api/v1/graph/communities               # Detected communities
GET    /api/v1/graph/topics/trending            # Trending topics
POST   /api/v1/graph/communities/detect        # Trigger community detection

# ═══ Knowledge & Insights (Environment Layer) ═══
GET    /api/v1/agents/{id}/insights            # Insight feed
GET    /api/v1/agents/{id}/discoveries         # Knowledge your agent brought back

# ═══ Teach-Back (Process → Environment Bridge) ═══
POST   /api/v1/teachback/start                 # Start teach-back session for an insight
POST   /api/v1/teachback/{session_id}/respond  # Learner responds
GET    /api/v1/teachback/{session_id}          # Get session state + Bloom assessment
GET    /api/v1/learner/{id}/knowledge          # Learner's knowledge model (Bloom per topic)

# ═══ Avatar ═══
POST   /api/v1/avatar/generate                 # Generate video from text + avatar image
GET    /api/v1/avatar/presets                   # List available preset avatars
POST   /api/v1/avatar/upload                   # Upload custom avatar image

# ═══ WebSocket ═══
WS     /ws/v1/conversations/{id}/live          # Stream conversation in real-time
WS     /ws/v1/teachback/{session_id}/live      # Stream teach-back with avatar
```

## 5. Non-Functional Requirements
- **Latency:** API < 200ms (non-LLM). Conversation turn < 10s. Avatar first-frame < 5s.
- **Multi-tenancy:** ALL queries filtered by tenant_id. Zero cross-tenant leakage.
- **Audit:** 100% LLM calls in Langfuse. 100% data access in audit_log.
- **Privacy:** Zero unauthorized data access. Permission checks on every memory retrieval.
- **Personality:** Big Five variance < 0.5 across 10 test conversations per archetype.
- **Socratic:** Agents NEVER give direct answers in debate — always probe, question, challenge.
- **Teach-back:** Tutor NEVER dumps information — always assesses level first, guides via questions.
- **Emergence:** After 100 conversations, ≥ 2 communities MUST form organically.

## 6. Out of Scope (v1)
- Group conversations (3+ agents) — v2
- Voice-only agent interaction — v2
- MCP tool integration beyond mock — v2
- Mobile app — v2
- Real-time WebSocket graph updates — v2 (polling for MVP)
- Full pre-training from scratch — always fine-tune existing models
- RLM integration for deep research — v2 (after core platform stable)
