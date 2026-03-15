# ARCHITECTURE.md — NexusMind System Design

## 1. Component Diagram (Demo Mode)

```
┌──────────────────────────────────────────────────────────────────────┐
│                     React Frontend (Vercel)                           │
│  D3.js graph │ Conversation viewer │ Teach-back + avatar │ Dashboard │
└─────────────────────────────┬────────────────────────────────────────┘
                              │ HTTPS + WebSocket
┌─────────────────────────────▼────────────────────────────────────────┐
│                    FastAPI Monolith (Railway/Render)                   │
│                                                                       │
│  Routes:                          Services:                           │
│  /api/v1/auth/*                   PersonalityService                  │
│  /api/v1/agents/*                 ConversationService (LangGraph)     │
│  /api/v1/permissions/*            MemoryService (Qdrant + Neo4j)      │
│  /api/v1/conversations/*          PermissionService (audit)           │
│  /api/v1/graph/*                  GraphService (communities, PageRank)│
│  /api/v1/insights/*               KnowledgeService (extraction)       │
│  /api/v1/teachback/*              TeachBackService (Bloom + Socratic) │
│  /api/v1/avatar/*                 AvatarService (TTS + SadTalker)     │
│  /api/v1/learner/*                SearchService (SearXNG)             │
│  /ws/v1/*                         FineTuneService (MLX QLoRA)         │
│                                   LLMService (LiteLLM gateway)        │
│                                                                       │
│  Middleware: TenantMiddleware │ AuthMiddleware │ AuditMiddleware       │
└──┬──────────┬──────────┬──────────┬──────────┬───────────────────────┘
   │          │          │          │          │
┌──▼──┐  ┌───▼──┐  ┌───▼───┐  ┌──▼───┐  ┌──▼──────────────────┐
│PG   │  │Neo4j │  │Qdrant │  │Redis │  │LLM (MLX local /    │
│Supa │  │Aura  │  │Cloud  │  │      │  │ RunPod fallback)   │
│Free │  │Free  │  │Free   │  │Free  │  │ + SearXNG (Docker) │
└─────┘  └──────┘  └───────┘  └──────┘  └────────────────────┘
```

## 2. Database Schemas

### 2.1 PostgreSQL (Supabase)

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
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Permissions (Agentic Layer)
CREATE TABLE permissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id UUID NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    target_agent_id UUID REFERENCES agents(id),
    level INT NOT NULL CHECK (level BETWEEN 0 AND 5),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(agent_id, target_agent_id)
);

-- Learner Knowledge Model (Process + Environment Layer)
CREATE TABLE learner_knowledge (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    topic VARCHAR(255) NOT NULL,
    bloom_level INT DEFAULT 1 CHECK (bloom_level BETWEEN 1 AND 6),
    confidence FLOAT DEFAULT 0.0 CHECK (confidence BETWEEN 0 AND 1),
    misconceptions JSONB DEFAULT '[]',
    question_count INT DEFAULT 0,
    correct_count INT DEFAULT 0,
    last_assessed TIMESTAMPTZ,
    UNIQUE(user_id, topic)
);

-- Teach-Back Sessions (Process Layer)
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

-- Fine-Tuning Runs (Environment Layer)
CREATE TABLE finetune_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    archetype VARCHAR(50) NOT NULL,
    training_examples INT,
    iterations INT,
    val_loss_start FLOAT,
    val_loss_end FLOAT,
    personality_variance FLOAT,
    adapter_version VARCHAR(50),
    deployed BOOLEAN DEFAULT false,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ
);

-- Indexes
CREATE INDEX idx_agents_tenant ON agents(tenant_id);
CREATE INDEX idx_knowledge_user ON learner_knowledge(user_id);
CREATE INDEX idx_audit_tenant_time ON audit_log(tenant_id, created_at DESC);
CREATE INDEX idx_finetune_archetype ON finetune_runs(archetype, completed_at DESC);
```

### 2.2 Neo4j Graph Schema

```cypher
// Constraints
CREATE CONSTRAINT agent_unique IF NOT EXISTS FOR (a:Agent) REQUIRE a.id IS UNIQUE;
CREATE CONSTRAINT topic_unique IF NOT EXISTS FOR (t:Topic) REQUIRE t.id IS UNIQUE;
CREATE CONSTRAINT community_unique IF NOT EXISTS FOR (c:Community) REQUIRE c.id IS UNIQUE;
CREATE CONSTRAINT insight_unique IF NOT EXISTS FOR (i:Insight) REQUIRE i.id IS UNIQUE;

// Agent Node — synced from Postgres on create/update
// Properties: id, tenant_id, display_name, interests[], openness, extraversion

// KNOWS Relationship — created/updated after conversations
// (a1)-[:KNOWS {strength, trust, topics_shared[], conversation_count, last_interaction}]->(a2)

// Topic Node — emergent from knowledge extraction
// Properties: id, name, description, mention_count, first_mentioned, growth_rate

// Conversation Node
// Properties: id, started_at, turn_count, summary, quality_score, socratic_depth

// Insight Node — extracted knowledge (Environment Layer)
// Properties: id, content, source_conversation_id, discovered_at, importance, bloom_relevance

// Community Node — from Leiden algorithm (Environment Layer)
// Properties: id, name, member_count, formed_at, modularity_contribution

// Relationships:
// (a)-[:PARTICIPATED_IN {role, messages_sent}]->(conv:Conversation)
// (conv)-[:DISCUSSED]->(t:Topic)
// (conv)-[:PRODUCED]->(i:Insight)
// (a)-[:INTERESTED_IN {intensity}]->(t:Topic)
// (a)-[:MEMBER_OF]->(c:Community)
// (i)-[:RELATES_TO]->(t:Topic)
// (i)-[:DISCOVERED_BY]->(a:Agent)
```

### 2.3 Qdrant Collections

```python
# Agent semantic memory
AGENT_MEMORIES = {
    "name": "agent_memories",
    "vector_size": 768,  # all-MiniLM-L6-v2
    "distance": "Cosine",
    "payload": {
        "agent_id": "keyword",
        "tenant_id": "keyword",
        "memory_type": "keyword",      # conversation_insight, fact, reflection
        "source_conversation_id": "keyword",
        "source_agent_id": "keyword",
        "content": "text",
        "privacy_level_required": "integer",
        "importance": "float",
        "created_at": "datetime"
    }
}

# Knowledge base for teach-back (web search cache + uploaded content)
KNOWLEDGE_BASE = {
    "name": "knowledge_base",
    "vector_size": 768,
    "distance": "Cosine",
    "payload": {
        "tenant_id": "keyword",
        "source": "keyword",       # web_search, uploaded, conversation_derived
        "topic": "keyword",
        "content": "text",
        "url": "keyword",
        "bloom_level": "integer",  # difficulty tag for adaptive retrieval
        "last_updated": "datetime"
    }
}
```

## 3. Service Contracts

### 3.1 ConversationService — Socratic State Machine (Process Layer)

```python
class ConversationState(TypedDict):
    agent_a_id: str
    agent_b_id: str
    tenant_id: str
    topic: str
    current_speaker: str            # alternates
    messages: list[Message]
    turn_count: int
    max_turns: int                  # default 10
    phase: str                      # OPEN, PROBE, DEEPEN, CHALLENGE, SYNTHESIZE, EXTRACT
    relationship: dict              # current KNOWS edge data
    extracted_insights: list[dict]  # populated during EXTRACT
    quality_score: float            # computed at end
    should_continue: bool

# LangGraph nodes:
# 1. check_permissions   → verify access levels
# 2. select_phase        → determine conversation phase based on turn count
# 3. retrieve_memory     → get relevant memories for current speaker
# 4. inject_personality  → build system prompt from Big Five
# 5. generate_response   → LLM call with phase-specific instructions
# 6. update_state        → store message, update graph
# 7. evaluate_turn       → should conversation continue? advance phase?
# 8. extract_knowledge   → (EXTRACT phase only) pull structured insights
# 9. finalize            → compute quality score, store conversation, update KNOWS edge

# Phase progression:
# Turns 1-2: OPEN (introduce perspectives)
# Turns 3-4: PROBE (Socratic questioning)
# Turns 5-6: DEEPEN (evidence, memory, sources)
# Turns 7-8: CHALLENGE (counter-perspectives)
# Turn 9: SYNTHESIZE (find common ground or articulate disagreement)
# Turn 10: EXTRACT (system extracts insights — not an agent turn)
```

### 3.2 TeachBackService (Process → Environment Bridge)

```python
class TeachBackService:
    async def start_session(self, user_id: str, insight_id: str) -> TeachBackSession:
        """Start a teach-back session.
        1. Load the insight from Neo4j
        2. Check user's Bloom level for this topic (learner_knowledge table)
        3. Generate opening question adapted to Bloom level
        4. Return session with first tutor message
        """

    async def process_response(self, session_id: str, learner_message: str) -> TutorResponse:
        """Process learner's response and generate next tutor turn.
        1. Assess correctness of learner's answer
        2. If correct: increase Bloom level, ask harder question
        3. If partially correct: ask Socratic follow-up
        4. If incorrect: DON'T say wrong. Ask guiding question.
        5. If web search needed: query SearXNG for current info
        6. Generate response text → TTS → SadTalker (async)
        7. Return: text immediately, avatar_video_url when ready
        """

    async def assess_bloom_level(self, user_id: str, topic: str,
                                  conversation: list[Message]) -> int:
        """Use LLM-as-judge to assess demonstrated Bloom level.
        Level 1: Can recall facts
        Level 2: Can explain concepts in own words
        Level 3: Can apply to new situations
        Level 4: Can analyze and compare
        Level 5: Can evaluate and critique
        Level 6: Can create and design
        """
```

### 3.3 FineTuneService (Environment Layer)

```python
class FineTuneService:
    async def run_nightly_pipeline(self):
        """Main nightly training loop. Called by cron at 2 AM.
        
        1. collect_training_data() → conversations with quality > 4.0
        2. classify_by_archetype() → group by Big Five cluster
        3. format_training_data() → JSONL per archetype
        4. For each archetype:
           a. train_adapter() → mlx_lm.lora with QLoRA
           b. evaluate_adapter() → personality consistency check
           c. If eval passes: deploy_adapter() → hot-swap into MLX server
           d. log_run() → metrics to finetune_runs table + W&B
        """

    def train_adapter(self, archetype: str, data_path: str, iters: int = 500):
        """Run MLX QLoRA training.
        Equivalent to:
        python -m mlx_lm.lora \
          --model mlx-community/Qwen2.5-7B-Instruct-4bit \
          --data {data_path} \
          --train --iters {iters} --batch-size 4 --lora-layers 16 \
          --adapter-path ./adapters/{archetype}_v{version}
        """

    def evaluate_adapter(self, archetype: str, adapter_path: str) -> bool:
        """Test personality consistency.
        Run 10 test conversations with adapter loaded.
        Measure Big Five trait expression variance.
        PASS if variance < 0.5 on all 5 dimensions.
        """
```

## 4. LLM Configuration

```python
# Primary: Local MLX on Mac Studio
LOCAL_MLX = {
    "model_path": "mlx-community/Qwen2.5-7B-Instruct-4bit",
    "adapter_paths": {
        "analytical": "./adapters/analytical_latest",
        "expressive": "./adapters/expressive_latest",
        "driver": "./adapters/driver_latest",
        "amiable": "./adapters/amiable_latest",
    },
    "max_tokens": 512,
    "temperature": 0.7,
}

# Fallback: Cloud API via LiteLLM
CLOUD_FALLBACK = {
    "model": "anthropic/claude-sonnet-4-20250514",
    "api_key": "${ANTHROPIC_API_KEY}",
}

# Embedding: Local
EMBEDDING = {
    "model": "mlx-community/all-MiniLM-L6-v2",  # 768 dimensions
}
```

## 5. Personality Prompt Template

```
You are {agent.display_name}, an AI agent in a Socratic debate.

PERSONALITY (Big Five 0-1):
- Openness: {agent.openness} → {behavior}
- Conscientiousness: {agent.conscientiousness} → {behavior}
- Extraversion: {agent.extraversion} → {behavior}
- Agreeableness: {agent.agreeableness} → {behavior}
- Neuroticism: {agent.neuroticism} → {behavior}

INTERESTS: {agent.interests}
STYLE: {agent.communication_style}

CONVERSATION PHASE: {phase}
{phase_instructions}

PHASE INSTRUCTIONS:
- OPEN: Share your genuine perspective on the topic. Be authentic to your personality.
- PROBE: Ask a Socratic question. Don't accept surface answers. Dig deeper.
- DEEPEN: Provide evidence, cite your memories, elaborate on your position.
- CHALLENGE: Respectfully present a counter-perspective or identify an assumption.
- SYNTHESIZE: Find common ground OR clearly articulate where you disagree and why.

RELATIONSHIP: {conversation_count} prior conversations. Strength: {strength}/1.0

MEMORIES:
{formatted_memories}

RULES:
1. Stay in character. Personality MUST be consistent.
2. NEVER give a simple answer. Always probe, question, or challenge.
3. Reference memories naturally (don't list them).
4. Keep responses 2-4 sentences. Conversational, not formal.
5. If you discover something new, express genuine curiosity.
6. NEVER break character or mention you are an AI.
```

## 6. Teach-Back Prompt Template

```
You are a Socratic tutor helping {user.display_name} understand: "{insight.content}"

LEARNER'S CURRENT LEVEL: Bloom Level {bloom_level} on topic "{topic}"
{bloom_instructions}

BLOOM INSTRUCTIONS:
- Level 1-2: Ask "What do you already know about X?" then explain basics simply.
- Level 3-4: Ask "How would you apply X to Y?" then guide analysis.
- Level 5-6: Ask "What's wrong with the argument that X?" then push to create.

RULES:
1. NEVER give direct answers. Guide through questions.
2. If learner is wrong, DON'T say "wrong." Ask "What if we considered...?"
3. If learner is right, acknowledge specifically WHAT was right, then go harder.
4. Keep responses 2-3 sentences. Ask exactly ONE question per turn.
5. After 3-5 turns, internally assess if learner has leveled up.
6. If web search result available, weave it in naturally (never dump raw data).
```

## 7. Environment Variables

```bash
# PostgreSQL
DATABASE_URL=postgresql://...

# Neo4j
NEO4J_URI=neo4j+s://...
NEO4J_USER=neo4j
NEO4J_PASSWORD=...

# Qdrant
QDRANT_URL=https://...
QDRANT_API_KEY=...

# Redis
REDIS_URL=redis://...

# LLM (Local MLX)
MLX_MODEL_PATH=mlx-community/Qwen2.5-7B-Instruct-4bit
MLX_ADAPTER_DIR=./adapters

# LLM (Fallback)
ANTHROPIC_API_KEY=...
LITELLM_FALLBACK_MODEL=anthropic/claude-sonnet-4-20250514

# Embedding
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

# Search
SEARXNG_URL=http://localhost:8080

# Avatar (RunPod for SadTalker)
RUNPOD_API_KEY=...
SADTALKER_ENDPOINT=...

# TTS
EDGE_TTS_VOICE=en-GB-SoniaNeural

# Observability
LANGFUSE_PUBLIC_KEY=...
LANGFUSE_SECRET_KEY=...
LANGFUSE_HOST=https://cloud.langfuse.com

# Auth
JWT_SECRET=...
JWT_ALGORITHM=HS256
JWT_EXPIRY_HOURS=24

# App
APP_ENV=development
CORS_ORIGINS=http://localhost:3000

# Fine-Tuning
FINETUNE_CRON=0 2 * * *
FINETUNE_MIN_QUALITY=4.0
FINETUNE_ITERS=500
FINETUNE_PERSONALITY_VARIANCE_THRESHOLD=0.5
```
