# CLAUDE.md — NexusMind

## Project Overview
NexusMind is a collective intelligence platform where personality-driven AI agents learn through Socratic debate on a knowledge graph, then teach their discoveries back to users adapted to their comprehension level. Built in four engineering layers: agentic (skeleton), process (nervous system), environment (soul), interface (face).

**One-liner:** "Agents that learn like humans — through social interaction — and bring the knowledge back to you."

## Tech Stack
- **Language:** Python 3.12+ (backend), TypeScript (frontend)
- **Framework:** FastAPI (async, Pydantic v2 for all models)
- **LLM Inference:** MLX + mlx-lm (Apple Silicon native) for local serving
- **LLM Gateway:** LiteLLM (fallback routing to RunPod/Anthropic API)
- **Fine-Tuning:** MLX LoRA/QLoRA (nightly personality adapter training)
- **Agent Orchestration:** LangGraph (stateful multi-agent conversations with Socratic protocol)
- **Graph DB:** Neo4j (social graph, community detection, knowledge flow tracking)
- **Vector DB:** Qdrant (semantic memory, hybrid dense+BM25 search)
- **SQL DB:** PostgreSQL via Supabase (users, tenants, agents, learner models, audit)
- **Cache:** Redis (session state, conversation buffers, adapter hot-swap)
- **Search:** SearXNG self-hosted (real-time web search for teach-back)
- **Avatar:** SadTalker (lip-synced talking head from single image) — CUDA burst via RunPod
- **TTS:** Edge TTS (free, 300+ voices, 75+ languages)
- **STT:** Whisper v3 via MLX (local, on Mac Studio)
- **Observability:** Langfuse (LLM tracing), structlog (app logging)
- **Frontend:** React 18 + TypeScript + D3.js (graph) + TailwindCSS + shadcn/ui
- **Testing:** pytest + pytest-asyncio + httpx + DeepEval (LLM behavioral)
- **Linting:** ruff (Python), eslint + prettier (TypeScript)

## Four-Layer Architecture
This system is built in layers. Each layer builds on the previous:
1. **Agentic Layer** (Phase 1-2): Agents exist, have personality, permissions, graph
2. **Process Layer** (Phase 3): Conversations flow via Socratic state machine, knowledge extracts
3. **Environment Layer** (Phase 4): Communities emerge, agents self-improve, teach-back works
4. **Interface Layer** (Phase 5): Graph viz, avatar tutor, demo

Read `SPEC.md` for product behavior. Read `docs/ARCHITECTURE.md` for system design.
Read `docs/LAYERS.md` for detailed explanation of each engineering layer.

## Directory Structure
```
nexusmind/
├── CLAUDE.md              # You are here
├── SPEC.md                # Full product specification
├── docs/
│   ├── ARCHITECTURE.md    # System design, DB schemas, API contracts
│   ├── LAYERS.md          # Four engineering layers explained
│   └── DECISIONS.md       # Architecture decision log (append-only)
├── dev/                   # Phase task files
│   ├── phase-1-tasks.md   # Agentic: project setup + DB + auth
│   ├── phase-2-tasks.md   # Agentic: agents + personality + graph + permissions
│   ├── phase-3-tasks.md   # Process: Socratic conversations + knowledge extraction
│   ├── phase-4-tasks.md   # Environment: communities + teach-back + fine-tuning loop
│   └── phase-5-tasks.md   # Interface: D3.js graph + avatar + demo
├── src/
│   ├── main.py            # FastAPI app entrypoint
│   ├── config.py          # pydantic-settings (env vars)
│   ├── models/            # Pydantic schemas (request/response)
│   ├── db/                # Database clients (neo4j, qdrant, postgres, redis)
│   ├── routes/            # FastAPI routers
│   ├── services/          # Business logic
│   │   ├── personality.py     # Big Five → prompts, compatibility, style
│   │   ├── conversation.py    # LangGraph Socratic state machine
│   │   ├── memory.py          # Qdrant + Neo4j dual memory
│   │   ├── permission.py      # 6-level privacy + audit
│   │   ├── graph.py           # Neo4j queries, community detection, recommendations
│   │   ├── knowledge.py       # Extract insights from conversations
│   │   ├── teachback.py       # Bloom assessment + Socratic teaching + adaptive difficulty
│   │   ├── avatar.py          # TTS + SadTalker pipeline
│   │   ├── search.py          # SearXNG web search integration
│   │   └── finetune.py        # Nightly QLoRA training pipeline (MLX)
│   ├── llm/               # LLM gateway, prompt templates, personality injection
│   └── utils/             # Auth, logging, permissions middleware
├── frontend/              # React app
├── training/              # Fine-tuning configs, data prep scripts
│   ├── prepare_data.py    # Convert conversations → JSONL training format
│   ├── train_adapters.py  # MLX QLoRA training script (runs nightly)
│   └── evaluate.py        # Personality consistency evaluation
├── tests/
│   ├── unit/
│   ├── integration/
│   └── llm_eval/          # Personality consistency, Socratic behavior, emergence tests
├── scripts/               # Seed data, graph maintenance, cron jobs
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
- structlog for ALL logging (never print)
- Every LLM call MUST log via Langfuse (trace_id in response)
- Type hints on every function. mypy strict. Google-style docstrings.
- Max function: 50 lines. Extract helpers.

## Testing Rules
- Every feature MUST have tests before PR
- Fast: `pytest tests/unit/ -x --tb=short`
- Full: `pytest tests/integration/ -x`
- LLM: `pytest tests/llm_eval/ -x` (on-demand — tests personality, Socratic, emergence)
- Min coverage: 80% on `src/services/`

## Git & Commands
```bash
# Local dev
docker compose up -d                     # Neo4j, Qdrant, Redis, Postgres, SearXNG
uv run uvicorn src.main:app --reload     # FastAPI

# Tests
uv run pytest tests/unit/ -x --tb=short
uv run ruff check src/ --fix && uv run ruff format src/

# Fine-tuning (runs on Mac Studio MLX)
python training/train_adapters.py --archetype analytical --iters 500

# Seed demo
uv run python scripts/seed_demo.py
```

## Critical Constraints
- NEVER call LLM without Langfuse tracing wrapper
- NEVER access data without permission level check → audit_log
- NEVER store PII in logs — use IDs only
- NEVER hardcode API keys — config.py env vars only
- ALL DB queries MUST filter by tenant_id
- Socratic engine MUST NOT give direct answers — always guide via questions
- Fine-tuning pipeline MUST validate personality consistency before deploying adapters
- When unsure: read SPEC.md (product), ARCHITECTURE.md (system), LAYERS.md (philosophy)
- When making decisions: append to DECISIONS.md

## Build Order
Complete ALL tasks in current phase before moving to next. Each phase = one engineering layer.
After each phase: run ALL tests, commit, tag.
