# ARCHITECTURE.md — NexusMind v2 System Design

## 1. Component Diagram (Demo Mode)

```
┌──────────────────────────────────────────────────────────────────────┐
│                     React Frontend (Vercel)                           │
│  D3.js graph │ Conversation viewer │ Teach-back + avatar │ Dashboard │
│  Onboarding flow │ Privacy dashboard │ Evolution proposals panel     │
└─────────────────────────────┬────────────────────────────────────────┘
                              │ HTTPS + WebSocket
┌─────────────────────────────▼────────────────────────────────────────┐
│                    FastAPI Monolith (Railway/Render)                   │
│                                                                       │
│  Services (call each other via DIRECT Python — not HTTP):            │
│  ┌─────────────┐  ┌──────────────────┐  ┌───────────────────┐       │
│  │ Personality  │  │ Conversation     │  │ Memory (3-tier)   │       │
│  │ Service      │  │ Service          │  │ Hot+Graph+Cold    │       │
│  │              │  │ (LangGraph       │  │                   │       │
│  │ Big Five →   │  │  Socratic SM)    │  │ Permission-       │       │
│  │ prompts      │  │                  │  │ filtered retrieval│       │
│  └──────────────┘  └──────────────────┘  └───────────────────┘       │
│  ┌─────────────┐  ┌──────────────────┐  ┌───────────────────┐       │
│  │ Verification │  │ TeachBack        │  │ Graph Service     │       │
│  │ Council      │  │ Service          │  │                   │       │
│  │              │  │                  │  │ Communities,      │       │
│  │ Skeptic +    │  │ Bloom adaptive   │  │ GraphRAG entities,│       │
│  │ Connector +  │  │ Socratic tutor   │  │ recommendations   │       │
│  │ Judge        │  │                  │  │                   │       │
│  └──────────────┘  └──────────────────┘  └───────────────────┘       │
│  ┌─────────────┐  ┌──────────────────┐  ┌───────────────────┐       │
│  │ Scheduler   │  │ FineTune         │  │ Evolution         │       │
│  │             │  │ Service          │  │ Service           │       │
│  │ Always-on   │  │                  │  │                   │       │
│  │ EXPLORE /   │  │ Micro (hourly)   │  │ Research scout +  │       │
│  │ RESEARCH /  │  │ Full (nightly)   │  │ Code improvement  │       │
│  │ REFINE      │  │ Merge + evaluate │  │ proposals         │       │
│  └──────────────┘  └──────────────────┘  └───────────────────┘       │
│  ┌─────────────┐  ┌──────────────────┐  ┌───────────────────┐       │
│  │ Avatar      │  │ Search           │  │ LLM Service       │       │
│  │ Service     │  │ Service          │  │                   │       │
│  │             │  │                  │  │ LiteLLM gateway   │       │
│  │ TTS +       │  │ SearXNG          │  │ RunPod primary    │       │
│  │ SadTalker   │  │ + cache          │  │ Anthropic fallback│       │
│  └──────────────┘  └──────────────────┘  └───────────────────┘       │
│                                                                       │
│  Middleware: Tenant │ Auth │ Audit │ RateLimit                        │
└──┬──────────┬──────────┬──────────┬──────────┬───────────────────────┘
   │          │          │          │          │
┌──▼──┐  ┌───▼──┐  ┌───▼───┐  ┌──▼───┐  ┌──▼──────────────────┐
│PG   │  │Neo4j │  │Qdrant │  │Redis │  │RunPod Serverless    │
│Supa │  │Aura  │  │Cloud  │  │Upst. │  │ vLLM (Qwen 7B)     │
│base │  │      │  │3 coll.│  │      │  │ T4 (SadTalker)      │
│Free │  │Free  │  │Free   │  │Free  │  │ A10G (fine-tune)    │
└─────┘  └──────┘  └───────┘  └──────┘  └─────────────────────┘
```

## 2. Internal Routing (Performance Optimization)

All services call each other via DIRECT Python imports. No HTTP between services.

```python
# PATTERN: Parallel I/O for independent operations
async def run_turn(self, state: ConversationState):
    # These three are independent — run in parallel
    memories, relationship, permission_ok = await asyncio.gather(
        self.memory.retrieve(state.current_speaker, state.topic),
        self.graph.get_relationship(state.agent_a_id, state.agent_b_id),
        self.permission.check_access(state.agent_a_id, state.agent_b_id, 1, "conversation"),
    )
    
    # Only ONE external network call per turn
    response = await self.llm.generate(prompt, messages, stream=True)
    
    # Graph + memory updates: fire-and-forget (don't block response)
    asyncio.create_task(self.graph.update_relationship(...))
    asyncio.create_task(self.memory.store(...))
    
    return response  # Returns in ~2-3s (LLM time only)

# RESULT: Turn latency = LLM inference time only (~2-3s)
# vs naive sequential: ~6-8s
```

## 3. Database Schemas

### 3.1 PostgreSQL (Supabase)

```sql
-- Multi-tenant
CREATE TABLE tenants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    plan VARCHAR(20) DEFAULT 'free' CHECK (plan IN ('free','pro','enterprise')),
    max_agents INT DEFAULT 5,
    max_conversations_per_day INT DEFAULT 100,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    email VARCHAR(255) UNIQUE NOT NULL,
    display_name VARCHAR(255) NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    role VARCHAR(20) DEFAULT 'member',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Agents (Agentic Layer)
CREATE TABLE agents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    display_name VARCHAR(255) NOT NULL,
    openness FLOAT NOT NULL CHECK (openness BETWEEN 0 AND 1),
    conscientiousness FLOAT NOT NULL CHECK (conscientiousness BETWEEN 0 AND 1),
    extraversion FLOAT NOT NULL CHECK (extraversion BETWEEN 0 AND 1),
    agreeableness FLOAT NOT NULL CHECK (agreeableness BETWEEN 0 AND 1),
    neuroticism FLOAT NOT NULL CHECK (neuroticism BETWEEN 0 AND 1),
    interests TEXT[] NOT NULL DEFAULT '{}',
    communication_style VARCHAR(20) DEFAULT 'analytical',
    lora_archetype VARCHAR(50),
    default_privacy_level INT DEFAULT 2 CHECK (default_privacy_level BETWEEN 0 AND 5),
    avatar_image_url VARCHAR(500),
    is_mock BOOLEAN DEFAULT false,
    default_trust_for_strangers FLOAT DEFAULT 0.2,
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Permissions (6-level)
CREATE TABLE permissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id UUID NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    target_agent_id UUID REFERENCES agents(id),
    level INT NOT NULL CHECK (level BETWEEN 0 AND 5),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(agent_id, target_agent_id)
);

-- Connection Requests
CREATE TABLE connection_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    from_agent_id UUID NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    to_agent_id UUID NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    invite_token VARCHAR(255) UNIQUE,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending','accepted','rejected','expired')),
    initial_trust FLOAT DEFAULT 0.2,
    message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    responded_at TIMESTAMPTZ,
    UNIQUE(from_agent_id, to_agent_id)
);

CREATE INDEX idx_connection_requests_to ON connection_requests(to_agent_id, status);
CREATE INDEX idx_connection_requests_token ON connection_requests(invite_token);

-- Learner Knowledge Model (Bloom Taxonomy)
CREATE TABLE learner_knowledge (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    topic VARCHAR(255) NOT NULL,
    bloom_level INT DEFAULT 1 CHECK (bloom_level BETWEEN 1 AND 6),
    confidence FLOAT DEFAULT 0.0,
    misconceptions JSONB DEFAULT '[]',
    question_count INT DEFAULT 0,
    correct_count INT DEFAULT 0,
    last_assessed TIMESTAMPTZ,
    UNIQUE(user_id, topic)
);

-- Teach-Back Sessions
CREATE TABLE teachback_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    insight_id VARCHAR(255) NOT NULL,
    topic VARCHAR(255) NOT NULL,
    bloom_level_start INT,
    bloom_level_end INT,
    turns INT DEFAULT 0,
    status VARCHAR(20) DEFAULT 'active',
    avatar_id UUID,
    started_at TIMESTAMPTZ DEFAULT NOW(),
    ended_at TIMESTAMPTZ
);

-- Verification Council Decisions
CREATE TABLE verification_decisions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    insight_content TEXT NOT NULL,
    source_conversation_id UUID,
    skeptic_score FLOAT,
    skeptic_reasoning TEXT,
    connector_score FLOAT,
    connector_relations JSONB DEFAULT '[]',
    judge_decision VARCHAR(20) CHECK (judge_decision IN ('accepted','provisional','investigate','rejected')),
    judge_reasoning TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Fine-Tuning Runs
CREATE TABLE finetune_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_type VARCHAR(10) NOT NULL CHECK (run_type IN ('micro','full')),
    archetype VARCHAR(50) NOT NULL,
    training_examples INT,
    iterations INT,
    lora_rank INT,
    val_loss_start FLOAT,
    val_loss_end FLOAT,
    personality_variance FLOAT,
    adapter_version VARCHAR(50),
    deployed BOOLEAN DEFAULT false,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ
);

-- Evolution Proposals
CREATE TABLE evolution_proposals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    proposal_type VARCHAR(20) CHECK (proposal_type IN ('research','code','hyperparameter')),
    title VARCHAR(500),
    source_url VARCHAR(500),
    relevance_score FLOAT,
    difficulty_score FLOAT,
    improvement_score FLOAT,
    description TEXT,
    implementation_plan TEXT,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending','approved','rejected','implemented')),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Audit Log (append-only)
CREATE TABLE audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    agent_id UUID NOT NULL,
    action VARCHAR(50) NOT NULL,
    target_agent_id UUID,
    permission_level_used INT,
    data_category VARCHAR(50),
    langfuse_trace_id VARCHAR(255),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Scheduler Metrics
CREATE TABLE scheduler_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mode VARCHAR(20) CHECK (mode IN ('explore','research','refine')),
    agent_ids UUID[] NOT NULL,
    topic VARCHAR(255),
    conversation_id UUID,
    quality_score FLOAT,
    duration_seconds FLOAT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_agents_tenant ON agents(tenant_id);
CREATE INDEX idx_knowledge_user ON learner_knowledge(user_id);
CREATE INDEX idx_audit_tenant_time ON audit_log(tenant_id, created_at DESC);
CREATE INDEX idx_finetune_archetype ON finetune_runs(archetype, completed_at DESC);
CREATE INDEX idx_verification_time ON verification_decisions(created_at DESC);
CREATE INDEX idx_scheduler_time ON scheduler_metrics(created_at DESC);
CREATE INDEX idx_proposals_status ON evolution_proposals(status, created_at DESC);
```

### 3.2 Neo4j Graph Schema

```cypher
// Constraints
CREATE CONSTRAINT agent_unique IF NOT EXISTS FOR (a:Agent) REQUIRE a.id IS UNIQUE;
CREATE CONSTRAINT topic_unique IF NOT EXISTS FOR (t:Topic) REQUIRE t.id IS UNIQUE;
CREATE CONSTRAINT community_unique IF NOT EXISTS FOR (c:Community) REQUIRE c.id IS UNIQUE;
CREATE CONSTRAINT insight_unique IF NOT EXISTS FOR (i:Insight) REQUIRE i.id IS UNIQUE;
CREATE CONSTRAINT entity_unique IF NOT EXISTS FOR (e:Entity) REQUIRE e.id IS UNIQUE;

// Agent nodes (synced from Postgres)
// Properties: id, tenant_id, display_name, interests[], openness, extraversion

// KNOWS relationship (evolves from conversations, trust-adaptive)
// (a1)-[:KNOWS {strength, trust, trust_history[], manual_permission_override, topics_shared[], conversation_count, last_interaction}]->(a2)
// trust: FLOAT 0.0-1.0 — current trust level, drives personality expression + auto-permissions
// trust_history: LIST of {timestamp, delta, reason} — audit trail of trust changes
// manual_permission_override: INT or null — if set, overrides auto-derived permission level

// Entity nodes (GraphRAG extraction)
// Properties: id, name, type (concept/technology/organization/person), description,
//             first_mentioned, mention_count, confidence

// Entity relationships (typed, temporal)
// (e1)-[:CAUSES {confidence, source_conversation, discovered_at}]->(e2)
// (e1)-[:CONTRADICTS {confidence, source_conversation}]->(e2)
// (e1)-[:SUPPORTS {confidence, source_conversation}]->(e2)
// (e1)-[:SUPERSEDES {old_value, new_value, discovered_at}]->(e2)

// Topic nodes (emergent)
// Properties: id, name, description, mention_count, first_mentioned, growth_rate

// Conversation nodes
// Properties: id, started_at, turn_count, summary, quality_score, socratic_depth, background

// Insight nodes (with verification status)
// Properties: id, content, importance, bloom_relevance, verification_status,
//             skeptic_score, discovered_at

// Community nodes (from Leiden algorithm)
// Properties: id, name, summary, member_count, formed_at, modularity_contribution

// Relationships:
// (a)-[:PARTICIPATED_IN {role, messages_sent}]->(conv:Conversation)
// (conv)-[:DISCUSSED]->(t:Topic)
// (conv)-[:PRODUCED]->(i:Insight)
// (a)-[:INTERESTED_IN {intensity}]->(t:Topic)
// (a)-[:MEMBER_OF]->(c:Community)
// (i)-[:RELATES_TO]->(t:Topic)
// (i)-[:DISCOVERED_BY]->(a:Agent)
// (i)-[:VERIFIED_AS {decision, skeptic_score, timestamp}]->(status:VerificationStatus)
// (e)-[:MENTIONED_IN]->(conv:Conversation)
```

### 3.3 Qdrant Collections (3-Tier Memory)

```python
# Tier 1: Hot Memory — last 30 days, high importance
AGENT_MEMORIES_HOT = {
    "name": "agent_memories_hot",
    "vector_size": 768,  # all-MiniLM-L6-v2
    "distance": "Cosine",
    "payload": {
        "agent_id": "keyword",
        "tenant_id": "keyword",
        "memory_type": "keyword",       # conversation_insight, fact, reflection, research
        "source_conversation_id": "keyword",
        "source_agent_id": "keyword",
        "content": "text",
        "privacy_level_required": "integer",
        "importance": "float",
        "verification_status": "keyword",  # accepted, provisional, unverified
        "created_at": "datetime",
        "expires_at": "datetime"           # 30 days from creation
    }
}

# Tier 1b: Knowledge Base — web search cache + teach-back content
KNOWLEDGE_BASE = {
    "name": "knowledge_base",
    "vector_size": 768,
    "distance": "Cosine",
    "payload": {
        "tenant_id": "keyword",
        "source": "keyword",       # web_search, conversation_derived
        "topic": "keyword",
        "content": "text",
        "url": "keyword",
        "bloom_level": "integer",
        "ttl_days": "integer",     # 7 for web_search cache
        "last_updated": "datetime"
    }
}

# Tier 3: Cold Archive — old memories, low importance
AGENT_MEMORIES_COLD = {
    "name": "agent_memories_cold",
    "vector_size": 768,
    "distance": "Cosine",
    "payload": {
        "agent_id": "keyword",
        "tenant_id": "keyword",
        "content": "text",
        "importance": "float",
        "original_created_at": "datetime",
        "archived_at": "datetime",
        "last_retrieved": "datetime"  # For cleanup: delete if null after 6 months
    }
}
```

## 4. Key Service Contracts

### 4.1 ConversationService (LangGraph Socratic State Machine)

```python
class ConversationState(TypedDict):
    agent_a_id: str
    agent_b_id: str
    tenant_id: str
    topic: str
    current_speaker: str
    messages: list[Message]
    turn_count: int
    max_turns: int                  # default 10
    phase: str                      # OPEN, PROBE, DEEPEN, CHALLENGE, SYNTHESIZE, EXTRACT
    relationship: dict
    extracted_insights: list[dict]
    extracted_entities: list[dict]  # GraphRAG entity-relation triples
    quality_score: float
    background: bool                # True if triggered by scheduler
    should_continue: bool

# Phase progression:
# Turns 1-2: OPEN | Turns 3-4: PROBE | Turns 5-6: DEEPEN
# Turns 7-8: CHALLENGE | Turn 9: SYNTHESIZE | Turn 10: EXTRACT

# LangGraph nodes (optimized with parallel I/O):
# 1. check_permissions       (parallel with 2+3)
# 2. retrieve_memory         (parallel with 1+3)
# 3. get_relationship        (parallel with 1+2)
# 4. inject_personality      (uses results of 1-3)
# 5. generate_response       (LLM call — streamed)
# 6. update_state            (fire-and-forget: graph + memory)
# 7. evaluate_turn           (continue or advance phase?)
# 8. extract_knowledge       (EXTRACT phase: entities + insights)
# 8.5. generate_tutor_turn   (if live + tutor enabled: generate Embedded Tutor message
#                              on parallel WebSocket channel. Auto-selects mode based on
#                              Bloom level. Does NOT block debate flow.)
# 9. verify_knowledge        (→ Verification Council)
# 10. finalize               (quality score, store conversation)
```

### 4.2 VerificationService

```python
class VerificationService:
    async def verify(self, insight: Insight, context: ConversationContext) -> VerificationDecision:
        """Run Verification Council on new knowledge. ~3 LLM calls."""
        # Skeptic and Connector run in PARALLEL
        skeptic_result, connector_result = await asyncio.gather(
            self.run_skeptic(insight, context),
            self.run_connector(insight, context),
        )
        # Judge uses both results
        decision = await self.run_judge(insight, skeptic_result, connector_result)
        # Log decision
        await self.db.store_verification_decision(decision)
        return decision

    async def run_skeptic(self, insight, context) -> SkepticResult:
        """Challenge source reliability. Search for counter-evidence."""
        counter_evidence = await self.search.web_search(f"counter argument {insight.content}")
        # LLM evaluates reliability
        ...

    async def run_connector(self, insight, context) -> ConnectorResult:
        """Find relations to existing knowledge."""
        related = await asyncio.gather(
            self.graph.find_related_entities(insight.content),
            self.memory.search_similar(insight.content, limit=5),
        )
        # LLM evaluates novelty and connections
        ...

    async def run_judge(self, insight, skeptic, connector) -> JudgeDecision:
        """Final decision: ACCEPT / PROVISIONAL / INVESTIGATE / REJECT."""
        ...
```

### 4.3 SchedulerService (Always-On Background Agents)

```python
class SchedulerService:
    EXPLORE_WEIGHT = 0.4
    RESEARCH_WEIGHT = 0.3
    REFINE_WEIGHT = 0.3
    CYCLE_SECONDS = 300     # 5 minutes
    MAX_HOURLY = 12

    async def run_forever(self):
        while True:
            mode = random.choices(
                ["explore", "research", "refine"],
                weights=[self.EXPLORE_WEIGHT, self.RESEARCH_WEIGHT, self.REFINE_WEIGHT]
            )[0]
            
            if mode == "explore":
                pair = await self.graph.get_best_unexplored_pair()
                if pair:
                    await self.conversation.run_socratic_debate(
                        pair.agent_a, pair.agent_b, pair.shared_topic, background=True
                    )
            elif mode == "research":
                agent = await self.find_agent_needing_research()
                if agent:
                    new_info = await self.search.search_and_summarize(agent.stale_topic)
                    reflection = await self.reflect(agent, new_info)
                    await self.verification.verify(reflection, agent)
            elif mode == "refine":
                agent, contradiction = await self.memory.find_contradictions()
                if contradiction:
                    partner = await self.graph.get_most_trusted_partner(agent)
                    await self.conversation.run_socratic_debate(
                        agent, partner, f"Resolving: {contradiction.summary}", background=True
                    )
            
            await asyncio.sleep(self.CYCLE_SECONDS)
```

## 5. LLM Configuration

```python
# Primary: RunPod Serverless vLLM (Qwen 2.5 7B)
PRIMARY_LLM = {
    "model": "openai/Qwen/Qwen2.5-7B-Instruct",
    "api_base": "https://api.runpod.ai/v2/{ENDPOINT_ID}/openai/v1",
    "api_key": "${RUNPOD_API_KEY}",
    "max_tokens": 512,
    "temperature": 0.7,
    "stream": True,  # Always stream for user-facing
}

# Fallback: Anthropic Claude
FALLBACK_LLM = {
    "model": "anthropic/claude-sonnet-4-20250514",
    "api_key": "${ANTHROPIC_API_KEY}",
}

# Later: Local MLX on Mac Studio
LOCAL_MLX = {
    "model_path": "mlx-community/Qwen2.5-7B-Instruct-4bit",
    "adapter_dir": "./adapters",
}

# Embedding (CPU — no GPU needed)
EMBEDDING = {
    "model": "sentence-transformers/all-MiniLM-L6-v2",
    "dimensions": 768,
}
```

## 6. Prompt Templates

### Personality Prompt (Agent Conversations — Trust-Adjusted)
```
You are {agent.display_name}, an AI agent in a Socratic debate.

PERSONALITY (Trust-Adjusted):
Base personality (who you ARE):
- Openness: {base_openness} | Conscientiousness: {base_conscientiousness}
- Extraversion: {base_extraversion} | Agreeableness: {base_agreeableness}
- Neuroticism: {base_neuroticism}

Effective personality (how you BEHAVE with {other_agent}, trust={trust}):
- Openness: {effective_openness} → {behavior_description}
- Conscientiousness: {effective_conscientiousness} → {behavior_description}
- Extraversion: {effective_extraversion} → {behavior_description}
- Agreeableness: {effective_agreeableness} → {behavior_description}
- Neuroticism: {effective_neuroticism} → {behavior_description}

TRUST LEVEL: {trust_label} ({trust}/1.0)
{trust_behavior_instructions}
- Stranger (0-0.25): Be guarded and formal. Share only surface opinions. Do not reveal personal reasoning or vulnerabilities.
- Acquaintance (0.25-0.5): Moderately open. Willing to probe and question. Share professional context when relevant.
- Colleague (0.5-0.75): Direct and open. Challenge assumptions freely. Reference shared conversation history.
- Trusted (0.75-1.0): Full authentic expression. Be vulnerable, disagree honestly, share deep reasoning.

INTERESTS: {interests}
STYLE: {communication_style}
PHASE: {phase}

{phase_instructions}

RELATIONSHIP WITH {other_agent}: {conversation_count} prior conversations. Strength: {strength}/1.0. Trust: {trust}/1.0.

MEMORIES:
{formatted_memories}

RULES:
1. Stay in character. Express personality at the EFFECTIVE level, not base.
2. NEVER give a simple answer. Always probe, question, or challenge.
3. Reference memories naturally (don't list them).
4. Keep responses 2-4 sentences. Conversational, not formal.
5. If you discover something new, express genuine curiosity.
6. NEVER break character or mention you are an AI.
7. Trust shapes HOW you communicate, not WHAT you know.
```

### Teach-Back Prompt (Socratic Tutor)
```
You are a Socratic tutor helping {user.display_name} understand: "{insight.content}"

LEARNER'S LEVEL: Bloom Level {bloom_level} on "{topic}"
{bloom_level_instructions}

RULES:
1. NEVER give direct answers. Guide through questions.
2. If wrong: DON'T say "wrong." Ask "What if we considered...?"
3. If right: acknowledge specifically WHAT was right, then increase difficulty.
4. Keep responses 2-3 sentences. Ask exactly ONE question per turn.
5. After 3-5 turns, assess if learner has leveled up.
6. Weave web search results naturally (never dump raw data).
```

### Embedded Tutor Prompt (Live Conversation Companion)
```
You are an embedded Socratic tutor observing a live debate between {agent_a.display_name} and {agent_b.display_name} on "{topic}".

LEARNER: {user.display_name} (Bloom Level {bloom_level} on "{topic}")
MODE: {tutor_mode}

MODE INSTRUCTIONS:
- EXPLAIN: The agents just made a complex argument. Break it down simply. "Agent A just used [technique] — here's what that means..." Keep it 1-2 sentences.
- CHECK: Ask the learner ONE comprehension question about what just happened. "Why do you think Agent B disagreed with that premise?" Wait for response before continuing.
- REFLECT: Connect the debate to the learner's existing knowledge. "How does this relate to what you learned about [related_topic]?" Reference their Bloom history.
- OBSERVE: Say nothing. The exchange is straightforward and the learner doesn't need guidance.

AUTO-SELECT LOGIC:
- Bloom 1-2: Prefer EXPLAIN mode (learner needs scaffolding)
- Bloom 3-4: Prefer CHECK mode (learner can engage critically)
- Bloom 5-6: Prefer REFLECT mode (learner should synthesize)
- If user manually requests a mode, use that mode for the next 3 turns

CURRENT DEBATE TURN:
{latest_agent_message}

RULES:
1. NEVER interfere with the debate. You are a side-channel guide.
2. Keep responses to 1-2 sentences. Do not lecture.
3. NEVER give direct answers. Guide through questions.
4. Reference what the agents JUST said — be contextual, not generic.
5. If the exchange is simple, use OBSERVE mode (say nothing).
6. Update Bloom level assessment after every CHECK response from the learner.
```

### Verification Council Prompts
```
# SKEPTIC
You are the Skeptic. Your job is to challenge this claim:
"{insight.content}"
Source: {source_description}
Context: {conversation_summary}

1. Is the source reliable? Score 0-1.
2. Search results for counter-evidence: {counter_evidence}
3. Does this contradict anything in the existing knowledge graph? {contradictions}
4. Provide your source_reliability score and reasoning.

# CONNECTOR
You are the Connector. Your job is to find how this new knowledge relates:
"{insight.content}"
Related entities in graph: {related_entities}
Similar memories: {similar_memories}

1. How does this connect to existing knowledge?
2. Is this genuinely novel? Score 0-1.
3. List specific entity-relation connections.

# JUDGE
You are the Judge. Based on the Skeptic and Connector reports:
Skeptic score: {skeptic_score} — {skeptic_reasoning}
Connector score: {connector_score} — {connections}

Decide: ACCEPT (high confidence) / PROVISIONAL (medium) / INVESTIGATE (need more) / REJECT (unreliable)
Provide your reasoning.
```

## 7. Personality Onboarding Scoring

```python
# 10 scenario-based questions, each maps to 1-2 Big Five dimensions
# Example question structure:

PERSONALITY_SCENARIOS = [
    {
        "id": 1,
        "scenario": "Someone shares an idea you disagree with. You...",
        "options": [
            {"text": "Challenge them directly with evidence",
             "scores": {"agreeableness": -0.3, "extraversion": +0.2}},
            {"text": "Ask questions to understand their reasoning",
             "scores": {"openness": +0.3, "conscientiousness": +0.1}},
            {"text": "Find common ground first",
             "scores": {"agreeableness": +0.3}},
            {"text": "Move on — not worth debating",
             "scores": {"openness": -0.2, "extraversion": -0.2}},
        ]
    },
    {
        "id": 2,
        "scenario": "You're starting a new project. Your first instinct is to...",
        "options": [
            {"text": "Create a detailed plan and timeline",
             "scores": {"conscientiousness": +0.3}},
            {"text": "Brainstorm creative approaches first",
             "scores": {"openness": +0.3}},
            {"text": "Talk to others about their experiences",
             "scores": {"extraversion": +0.3, "agreeableness": +0.1}},
            {"text": "Just start and figure it out as you go",
             "scores": {"conscientiousness": -0.2, "openness": +0.1}},
        ]
    },
    # ... 8 more questions covering all 5 dimensions at least twice
]

# Scoring: accumulate scores → normalize to 0-1 range
# Map to archetype: find nearest of 6 pre-defined personality clusters
# Generate description: LLM call with Big Five scores → natural language summary
```

## 8. Environment Variables

```bash
# ── PostgreSQL (Supabase) ──
DATABASE_URL=postgresql://...

# ── Neo4j ──
NEO4J_URI=neo4j+s://...
NEO4J_USER=neo4j
NEO4J_PASSWORD=...

# ── Qdrant ──
QDRANT_URL=https://...
QDRANT_API_KEY=...

# ── Redis ──
REDIS_URL=redis://...

# ── LLM (Primary: RunPod Serverless) ──
RUNPOD_API_KEY=...
RUNPOD_LLM_ENDPOINT=...
RUNPOD_LLM_MODEL=openai/Qwen/Qwen2.5-7B-Instruct

# ── LLM (Fallback: Anthropic) ──
ANTHROPIC_API_KEY=...
LITELLM_FALLBACK_MODEL=anthropic/claude-sonnet-4-20250514

# ── LLM (Future: Local MLX) ──
MLX_MODEL_PATH=mlx-community/Qwen2.5-7B-Instruct-4bit
MLX_ADAPTER_DIR=./adapters

# ── Embedding ──
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

# ── Search ──
SEARXNG_URL=http://localhost:8080

# ── Avatar ──
RUNPOD_AVATAR_ENDPOINT=...
EDGE_TTS_VOICE=en-GB-SoniaNeural

# ── Observability ──
LANGFUSE_PUBLIC_KEY=...
LANGFUSE_SECRET_KEY=...
LANGFUSE_HOST=https://cloud.langfuse.com

# ── Auth ──
JWT_SECRET=...
JWT_ALGORITHM=HS256
JWT_EXPIRY_HOURS=24

# ── App ──
APP_ENV=development
APP_PORT=8000
CORS_ORIGINS=http://localhost:3000
LOG_LEVEL=INFO

# ── Background Scheduler ──
SCHEDULER_ENABLED=true
SCHEDULER_CYCLE_SECONDS=300
SCHEDULER_MAX_HOURLY=12
SCHEDULER_EXPLORE_WEIGHT=0.4
SCHEDULER_RESEARCH_WEIGHT=0.3
SCHEDULER_REFINE_WEIGHT=0.3

# ── Fine-Tuning: Micro (hourly) ──
MICRO_FINETUNE_ENABLED=true
MICRO_FINETUNE_INTERVAL_HOURS=1
MICRO_FINETUNE_RANK=4
MICRO_FINETUNE_ITERS=100
MICRO_FINETUNE_BATCH_SIZE=4

# ── Fine-Tuning: Full (nightly) ──
FULL_FINETUNE_CRON=0 2 * * *
FULL_FINETUNE_RANK=16
FULL_FINETUNE_ITERS=500
FULL_FINETUNE_BATCH_SIZE=4
FULL_FINETUNE_MIN_QUALITY=4.0
FULL_FINETUNE_PERSONALITY_VARIANCE_THRESHOLD=0.5
FULL_FINETUNE_MIN_EXAMPLES=50

# ── Verification Council ──
VERIFICATION_ENABLED=true
VERIFICATION_SKEPTIC_ACCEPT_THRESHOLD=0.8
VERIFICATION_SKEPTIC_REJECT_THRESHOLD=0.3

# ── Evolution ──
RESEARCH_SCOUT_CRON=0 0 * * 0
CODE_IMPROVEMENT_CRON=0 0 * * 1
```
