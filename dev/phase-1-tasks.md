# Phase 1: Foundation — Project Setup + DB + Auth
# Engineering Layer: AGENTIC (skeleton setup)
# Estimated: 2-3 days | Prerequisite: None

## Completion Criteria
- [ ] `docker compose up -d` starts Neo4j, Qdrant, Redis, Postgres, SearXNG
- [ ] FastAPI runs at GET /health → `{"status": "ok"}`
- [ ] All Postgres tables created via Alembic migration (including verification_decisions, finetune_runs, evolution_proposals, scheduler_metrics)
- [ ] Neo4j constraints created on startup
- [ ] All 3 Qdrant collections created on startup (hot, knowledge_base, cold)
- [ ] JWT auth: register → login → access protected route
- [ ] All tests pass

## Tasks

### 1.1 Scaffolding
- `uv init nexusmind` with all deps from CLAUDE.md
- Create full directory structure per CLAUDE.md
- docker-compose.yml: Neo4j (7687/7474), Qdrant (6333/6334), Redis (6379), Postgres (5432), SearXNG (8080)
- .env.example from ARCHITECTURE.md §8

### 1.2 Configuration
- `src/config.py` — pydantic-settings loading ALL env vars with validation (including scheduler, finetune, verification, evolution sections)
- `src/utils/logging.py` — structlog config (JSON prod, pretty dev)

### 1.3 Database Setup
- Alembic migration for ALL Postgres tables (ARCHITECTURE.md §3.1 — all 11 tables)
- `src/db/postgres.py` — async pool via asyncpg
- `src/db/neo4j_client.py` — driver + all constraint creation on startup
- `src/db/qdrant_client.py` — create all 3 collections on startup (hot, knowledge_base, cold)
- `src/db/redis_client.py` — connection pool

### 1.4 Auth
- `src/models/auth.py` — RegisterRequest, LoginRequest, TokenResponse
- `src/services/auth_service.py` — register, login, verify_token
- `src/routes/auth.py` — POST /register, POST /login
- `src/utils/auth.py` — JWT create/verify, `get_current_user` dependency

### 1.5 App Entrypoint
- `src/main.py` — FastAPI with lifespan (connect/close ALL DBs), CORS, auth router, /health

### 1.6 Tests
- `tests/unit/test_config.py` — all config sections load correctly
- `tests/unit/test_auth.py` — JWT + password hashing
- `tests/integration/test_auth_flow.py` — register → login → protected route

## Checkpoint
```bash
uv run pytest tests/ -x && echo "Phase 1 DONE"
git commit -m "feat: Phase 1 — foundation + auth" && git tag v0.1.0
```
