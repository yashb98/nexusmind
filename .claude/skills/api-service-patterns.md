---
name: api-service-patterns
description: Work on FastAPI routes, service patterns, Pydantic models, dependency injection, error handling, middleware, multi-tenancy, audit logging, or creating new API endpoints
allowed-tools: Read, Bash, Grep, Glob, Edit, Write
---

# Skill: API & Service Patterns

## When to use
Use this skill when creating new routes, services, models, middleware, error handling, or writing tests.

## FastAPI Route Pattern
Routes are THIN. Validate input, call service, return response. NO business logic.

```python
@router.post("/api/v1/agents", response_model=AgentResponse)
async def create_agent(
    data: AgentCreate,
    user: UserInDB = Depends(get_current_user),
    agent_service: AgentService = Depends(get_agent_service),
):
    return await agent_service.create(data, user.id, user.tenant_id)
```

## Service Pattern
Services contain ALL business logic. They receive dependencies via constructor injection.

```python
class AgentService:
    def __init__(self, db: PostgresClient, neo4j: Neo4jClient, qdrant: QdrantClient):
        self.db = db
        self.neo4j = neo4j
        self.qdrant = qdrant

    async def create(self, data: AgentCreate, user_id: str, tenant_id: str) -> AgentResponse:
        # 1. Validate business rules
        # 2. Persist to database(s)
        # 3. Return response model
```

## Dependency Injection
```python
# Every service is a singleton created in lifespan and injected via Depends
def get_agent_service() -> AgentService:
    return app.state.agent_service
```

## Multi-Tenancy (CRITICAL)
EVERY database query MUST include tenant_id filter. No exceptions.
```python
# CORRECT:
await db.fetch("SELECT * FROM agents WHERE tenant_id = $1 AND id = $2", tenant_id, agent_id)

# WRONG (data leak):
await db.fetch("SELECT * FROM agents WHERE id = $1", agent_id)
```

Tenant ID comes from the JWT token via middleware. Never from request body.

## Error Handling
```python
from fastapi import HTTPException

class ServiceError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code

# In routes:
@app.exception_handler(ServiceError)
async def service_error_handler(request, exc):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})

# In services:
if not permission_ok:
    raise ServiceError("Insufficient permission", 403)
```

## Audit Logging
Every data access MUST be logged:
```python
await db.execute("""
    INSERT INTO audit_log (tenant_id, agent_id, action, target_agent_id, 
                          permission_level_used, data_category, langfuse_trace_id)
    VALUES ($1, $2, $3, $4, $5, $6, $7)
""", tenant_id, agent_id, "memory_access", target_id, level, "conversation", trace_id)
```

## Pydantic Model Conventions
```python
# Request models: only fields the client sends
class AgentCreate(BaseModel):
    display_name: str = Field(min_length=1, max_length=255)
    openness: float = Field(ge=0, le=1)
    # ... etc

# Response models: include computed fields + timestamps
class AgentResponse(BaseModel):
    id: str
    display_name: str
    archetype: str  # computed, not stored
    created_at: datetime

# NEVER use raw dicts. Always Pydantic models.
```

## Testing Pattern
```python
# Unit test: mock dependencies
async def test_personality_scoring():
    service = PersonalityService()
    result = service.score_personality([0, 1, 2, 3, 0, 1, 2, 3, 0, 1])
    assert 0 <= result.openness <= 1
    assert result.archetype in VALID_ARCHETYPES

# Integration test: real DB (use test database)
async def test_create_agent(test_client, test_db):
    response = await test_client.post("/api/v1/agents", json={...}, headers=auth_headers)
    assert response.status_code == 200
    # Verify in Postgres
    agent = await test_db.fetch_one("SELECT * FROM agents WHERE id = $1", response.json()["id"])
    assert agent is not None
    # Verify in Neo4j
    node = await test_neo4j.run_query("MATCH (a:Agent {id: $id}) RETURN a", {"id": response.json()["id"]})
    assert node is not None

# LLM eval test: test behavior
async def test_personality_consistency():
    # Run 5 conversations with same agent
    # LLM-as-judge scores Big Five expression
    # Assert variance < 0.5
```

## DSPy Module Integration Pattern
When a service uses a DSPy module, the integration follows this pattern:
```python
class VerificationService:
    def __init__(self, ..., skeptic_module: SkepticModule):
        self.skeptic = skeptic_module

    async def run_skeptic(self, insight, context) -> SkepticResult:
        result = self.skeptic(claim=insight.content, source=context.source_description, ...)
        return SkepticResult(
            score=max(0.0, min(1.0, result.reliability_score)),
            reasoning=result.reasoning,
        )
```
Rules:
- DSPy modules injected via dependency injection (testable, swappable)
- Service return types NEVER change when swapping to DSPy
- ALWAYS validate/clamp DSPy outputs before returning
- DSPy modules are synchronous — use `asyncio.to_thread()` if blocking

## Code Style
- async def for ALL handlers and service methods
- Type hints on every function (mypy strict)
- Google-style docstrings
- Max 50 lines per function — extract helpers
- structlog for all logging (never print)
- ruff for linting + formatting
