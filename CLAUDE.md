# CLAUDE.md — NexusMind v2 ("The Living System")

## Project Overview
NexusMind is a self-learning collective intelligence platform. Personality-driven AI agents debate autonomously on a knowledge graph using Socratic protocol, verify discoveries through a 3-agent council, teach users via adaptive avatar tutors, and improve themselves every hour through progressive model distillation. The system evolves its knowledge, models, research awareness, and even its own code — mostly autonomously.

**One-liner:** "AI agents that never sleep — they debate, discover, verify, teach you, and get smarter every hour."

## Tech Stack
- **Language:** Python 3.12+ (backend), TypeScript (frontend)
- **Framework:** FastAPI (async, Pydantic v2 for all models)
- **LLM Inference:** LiteLLM gateway → RunPod Serverless vLLM (primary) → Anthropic API (fallback)
- **LLM Model:** Qwen 2.5 7B Instruct (4-bit) via RunPod Serverless (OpenAI-compatible)
- **Fine-Tuning:** MLX LoRA/QLoRA on Mac Studio (later) OR RunPod A10G burst (now)
- **Agent Orchestration:** LangGraph (stateful multi-agent conversations, Socratic protocol, verification)
- **Background Scheduler:** APScheduler + asyncio (always-on agent work loops)
- **Graph DB:** Neo4j (social graph, communities, knowledge entities, verification trail)
- **Vector DB:** Qdrant (3 collections: hot memory, knowledge base, cold archive)
- **SQL DB:** PostgreSQL via Supabase (users, agents, learner models, audit, fine-tune runs)
- **Cache:** Redis (session state, conversation buffers, adapter swap signals, rate limiting)
- **Search:** SearXNG self-hosted (real-time web search for teach-back + research agents)
- **Avatar:** SadTalker via RunPod T4 burst (lip-synced talking head from single image)
- **TTS:** Edge TTS (free, 300+ voices, 75+ languages)
- **STT:** Whisper v3 (CPU or MLX local)
- **Embedding:** sentence-transformers/all-MiniLM-L6-v2 (768d, runs on CPU)
- **Observability:** Langfuse (LLM tracing + cost), structlog (app logging)
- **Frontend:** React 18 + Next.js + TypeScript + D3.js + TailwindCSS + shadcn/ui + Recharts
- **Testing:** pytest + pytest-asyncio + httpx + DeepEval (LLM behavioral)
- **Linting:** ruff (Python), eslint + prettier (TypeScript)

## Five-Layer Architecture (The Living System)
Each layer produces qualitatively different intelligence:
1. **Agentic Layer** (Phase 1-2): Agents exist with personality, permissions, graph
2. **Process Layer** (Phase 3): Socratic conversations, knowledge extraction, internal routing
3. **Environment Layer** (Phase 4): Communities, teach-back, verification council, 3-tier memory
4. **Evolution Layer** (Phase 5): Always-on agents, progressive distillation, self-evolution engine
5. **Interface Layer** (Phase 6): Graph viz, avatar tutor, demo

Read `SPEC.md` for product behavior. Read `docs/ARCHITECTURE.md` for system design.
Read `docs/LAYERS.md` for engineering layers. Read `docs/EVOLUTION.md` for self-improvement loops.

## Directory Structure
```
nexusmind/
├── CLAUDE.md
├── SPEC.md
├── docs/
│   ├── ARCHITECTURE.md    # System design, DB schemas, API contracts
│   ├── LAYERS.md          # Five engineering layers explained
│   ├── EVOLUTION.md       # Self-improvement loops + verification council
│   └── DECISIONS.md       # Architecture decision log (append-only)
├── dev/                   # Phase task files
│   ├── phase-1-tasks.md   # Foundation: Docker, DB, auth
│   ├── phase-2-tasks.md   # Agentic: agents, personality onboarding, graph, permissions
│   ├── phase-3-tasks.md   # Process: Socratic conversations, internal routing, knowledge extraction
│   ├── phase-4-tasks.md   # Environment: communities, teach-back, verification council, 3-tier memory
│   ├── phase-5-tasks.md   # Evolution: always-on agents, progressive distillation, self-evolution
│   └── phase-6-tasks.md   # Interface: D3.js graph, avatar, deployment, demo
├── src/
│   ├── main.py
│   ├── config.py          # pydantic-settings (env vars)
│   ├── models/            # Pydantic schemas
│   ├── db/                # Database clients (neo4j, qdrant, postgres, redis)
│   ├── routes/            # FastAPI routers
│   ├── services/
│   │   ├── personality.py     # Big Five scoring, prompt generation, archetypes
│   │   ├── conversation.py    # LangGraph Socratic state machine
│   │   ├── memory.py          # 3-tier: hot (Qdrant) + graph (Neo4j) + cold (Qdrant)
│   │   ├── permission.py      # 6-level privacy + audit
│   │   ├── graph.py           # Neo4j queries, communities, GraphRAG entity extraction
│   │   ├── knowledge.py       # Extract + store insights from conversations
│   │   ├── verification.py    # Verification Council: Skeptic + Connector + Judge
│   │   ├── teachback.py       # Bloom assessment + Socratic teaching + adaptive difficulty
│   │   ├── avatar.py          # Edge TTS + SadTalker pipeline
│   │   ├── search.py          # SearXNG web search integration
│   │   ├── finetune.py        # Progressive distillation: micro (hourly) + full (nightly)
│   │   ├── scheduler.py       # Always-on background agent scheduler (EXPLORE/RESEARCH/REFINE)
│   │   └── evolution.py       # Self-evolution: research scout + code improvement proposals
│   ├── llm/               # LLM gateway, prompt templates, personality injection
│   └── utils/             # Auth, logging, permissions middleware
├── frontend/              # React + Next.js app
├── training/              # Fine-tuning pipeline
│   ├── prepare_data.py    # Conversations → JSONL (filtered by verification council)
│   ├── train_micro.py     # Hourly micro-adapter (rank=4, 2-3 min)
│   ├── train_full.py      # Nightly full adapter (rank=16, 25 min)
│   ├── merge_adapters.py  # Merge micro-adapters into base
│   └── evaluate.py        # Personality consistency evaluation
├── proposals/             # Auto-generated improvement proposals (Loop 3 + 4)
├── tests/
│   ├── unit/
│   ├── integration/
│   └── llm_eval/          # Personality, Socratic, emergence, verification tests
├── scripts/
│   ├── seed_demo.py
│   ├── run_scheduler.py   # Start always-on background agent loop
│   └── run_evolution.py   # Start weekly self-evolution cycle
├── docker-compose.yml     # Neo4j + Qdrant + Redis + Postgres + SearXNG
├── pyproject.toml
└── .env.example
```

## Code Style Rules
- `async def` for all route handlers and service functions
- All request/response bodies: Pydantic BaseModel (never raw dicts)
- Dependency injection: `db: Neo4jClient = Depends(get_neo4j)`
- DB queries in `src/db/` only — routes never touch DB directly
- Business logic in `src/services/` — routes → services → db
- Services call each other via DIRECT Python imports (not HTTP) — we are a monolith
- Independent I/O operations MUST use `asyncio.gather()` for parallel execution
- Graph/memory updates after LLM response: use `asyncio.create_task()` (fire-and-forget)
- structlog for ALL logging (never print)
- Every LLM call MUST log via Langfuse (trace_id in response)
- Type hints on every function. mypy strict. Google-style docstrings.
- Max function: 50 lines. Extract helpers.

## Performance Rules
- Internal service calls: DIRECT Python (0ms overhead, not HTTP)
- Parallel I/O: `asyncio.gather(memory, graph, permission)` — never sequential
- Fire-and-forget: graph updates + memory stores run AFTER response returns
- LLM streaming: `stream=True` for all user-facing LLM responses
- Prefix caching: system prompt reused across conversation turns (vLLM handles this)
- Result: conversation turn latency = LLM inference time only (~2-3s), not infra overhead

## Testing Rules
- Every feature MUST have tests before PR
- Fast: `pytest tests/unit/ -x --tb=short`
- Full: `pytest tests/integration/ -x`
- LLM: `pytest tests/llm_eval/ -x` (personality, Socratic, emergence, verification)
- Min coverage: 80% on `src/services/`

## Git & Commands
```bash
# Local dev
docker compose up -d                     # Neo4j, Qdrant, Redis, Postgres, SearXNG
uv run uvicorn src.main:app --reload     # FastAPI
uv run python scripts/run_scheduler.py   # Start always-on background agents

# Tests
uv run pytest tests/unit/ -x --tb=short
uv run ruff check src/ --fix && uv run ruff format src/

# Fine-tuning (RunPod burst or Mac Studio)
python training/train_micro.py --archetype analytical --iters 100
python training/train_full.py --all-archetypes --iters 500

# Seed demo
uv run python scripts/seed_demo.py
```

## Critical Constraints
- NEVER call LLM without Langfuse tracing wrapper
- NEVER access data without permission level check → audit_log
- NEVER store knowledge without Verification Council approval
- NEVER deploy adapter without personality consistency evaluation (variance < 0.5)
- NEVER auto-deploy code changes — proposals only, human approves
- NEVER store PII in logs — use IDs only
- NEVER hardcode API keys — config.py env vars only
- ALL DB queries MUST filter by tenant_id
- Socratic engine MUST NOT give direct answers — always guide via questions
- Facts go to MEMORY (searchable). Patterns go to WEIGHTS (LoRA). Always separated.
- When unsure: read SPEC.md, ARCHITECTURE.md, LAYERS.md, EVOLUTION.md
- When making decisions: append to DECISIONS.md

## Build Order
Complete ALL tasks in current phase before moving to next.
After each phase: run ALL tests, commit, tag.
Phase 1 → 2 → 3 → 4 → 5 → 6. No skipping.
