# Backend Context (src/)

## Architecture
FastAPI monolith. Services call each other via direct Python imports (not HTTP).

## Pattern: Route → Service → DB
Routes validate input + call services. Services contain ALL logic + call DB clients. DB clients execute queries.
NEVER put business logic in routes. NEVER call DB directly from routes.

## Async Rules
- `async def` for ALL route handlers and service methods
- `asyncio.gather()` for independent I/O (memory + graph + permission = parallel)
- `asyncio.create_task()` for fire-and-forget (graph updates after response)
- NEVER use blocking calls (requests.get, time.sleep) in async functions

## Multi-Tenancy
EVERY query MUST filter by tenant_id. Missing filter = security vulnerability.

## LLM Calls
EVERY LLM call MUST be wrapped in Langfuse trace. No exceptions.
Use LiteLLM for routing: RunPod primary → Anthropic fallback.
Stream for user-facing. Non-stream for background.

## Testing
Mirror source paths: `src/services/X.py` → `tests/unit/test_X.py`
Run: `uv run pytest tests/ -x --tb=short`
