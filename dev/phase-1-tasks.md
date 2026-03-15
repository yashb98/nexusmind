# Phase 1: Foundation — Project Setup + DB + Auth
# Engineering Layer: AGENTIC (skeleton)
# Estimated: 2-3 days | Prerequisite: None

## Completion Criteria
- [ ] `docker compose up -d` starts Neo4j, Qdrant, Redis, Postgres, SearXNG
- [ ] FastAPI app runs at GET /health → `{"status": "ok"}`
- [ ] Postgres tables created via Alembic migration
- [ ] Neo4j constraints created on startup
- [ ] Qdrant collections created on startup
- [ ] JWT auth: register → login → access protected route
- [ ] All tests pass: `pytest tests/unit/test_auth.py tests/unit/test_config.py`

## Tasks

### 1.1 Scaffolding
- `uv init nexusmind` with all deps from CLAUDE.md tech stack
- Create full directory structure per CLAUDE.md
- Create docker-compose.yml: Neo4j (7687/7474), Qdrant (6333), Redis (6379), Postgres (5432), SearXNG (8080)
- Create .env.example from ARCHITECTURE.md §7

### 1.2 Configuration
- `src/config.py` — pydantic-settings loading all env vars with validation
- `src/utils/logging.py` — structlog config (JSON in prod, pretty in dev)

### 1.3 Database Setup
- Alembic migration for ALL Postgres tables (see ARCHITECTURE.md §2.1)
- `src/db/postgres.py` — async pool via asyncpg
- `src/db/neo4j_client.py` — driver + constraint creation on startup
- `src/db/qdrant_client.py` — collection creation on startup (both collections)
- `src/db/redis_client.py` — connection pool

### 1.4 Auth
- `src/models/auth.py` — RegisterRequest, LoginRequest, TokenResponse
- `src/services/auth_service.py` — register, login, verify_token
- `src/routes/auth.py` — POST /register, POST /login
- `src/utils/auth.py` — JWT create/verify, `get_current_user` dependency

### 1.5 App Entrypoint
- `src/main.py` — FastAPI with lifespan (connect/close DBs), CORS, auth router, /health

### 1.6 Tests
- `tests/unit/test_config.py`
- `tests/unit/test_auth.py` — JWT + password hashing
- `tests/integration/test_auth_flow.py` — full register → login → protected route

## Checkpoint
`uv run pytest tests/ -x && echo "Phase 1 DONE"`
`git commit -m "feat: Phase 1 — foundation + auth" && git tag v0.1.0`
