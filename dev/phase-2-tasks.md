# Phase 2: Agents + Personality Onboarding + Graph + Permissions
# Engineering Layer: AGENTIC (skeleton complete)
# Estimated: 3-4 days | Prerequisite: Phase 1

## Completion Criteria
- [ ] GET /api/v1/onboarding/scenarios returns 10 scenario-based personality questions
- [ ] POST /api/v1/onboarding/personality accepts answers → returns Big Five scores + archetype + description
- [ ] CRUD agents with Big Five personality via API
- [ ] Agent synced to Neo4j node on create/update
- [ ] Permission system: set, check, audit — zero unauthorized access
- [ ] PersonalityService generates consistent system prompts from Big Five
- [ ] Graph queries: network, similar agents, recommendations
- [ ] `scripts/seed_demo.py` creates 10 diverse agents with graph edges
- [ ] All tests pass

## Layer Test
"Can I complete the 4-step onboarding, see my personality radar chart, and see my agent on a graph with 10 agents and edges?"

## Tasks

### 2.1 Personality Onboarding
- `src/models/onboarding.py` — ScenarioQuestion, ScenarioAnswer, PersonalityResult
- `src/services/personality.py`:
  - `get_scenarios()` → 10 scenario-based questions (ARCHITECTURE.md §7)
  - `score_personality(answers)` → Big Five scores (0-1 each), normalized
  - `compute_communication_style(big_five)` → analytical/expressive/driver/amiable
  - `assign_archetype(big_five)` → nearest of 6 pre-defined clusters
  - `generate_description(big_five, archetype)` → LLM generates natural language summary
  - `generate_system_prompt(agent, phase, context)` → personality-grounded conversation prompt
  - `compute_compatibility(agent_a, agent_b)` → 0-1 score
- `src/routes/onboarding.py` — GET /scenarios, POST /personality

### 2.2 Agent CRUD
- `src/models/agent.py` — AgentCreate, AgentResponse, AgentUpdate
- `src/services/agent_service.py` — CRUD with Postgres + Neo4j sync
- `src/routes/agents.py` — POST/GET/PATCH/DELETE + list (all tenant-scoped)

### 2.3 Permission System
- `src/models/permission.py` — PermissionSet, PermissionCheck, AuditEntry
- `src/services/permission.py`:
  - `set_permission(agent_id, target_agent_id, level)`
  - `get_effective_level(source, target)` → int (override > default)
  - `check_access(source, target, required_level, category)` → bool + audit log
  - `filter_by_permission(items, accessor, source)` → filtered
- `src/routes/permissions.py` — POST/GET permissions, GET audit

### 2.4 Graph Service
- `src/services/graph.py`:
  - `get_agent_network(agent_id, hops=2)` → nodes + edges for D3.js
  - `find_similar_agents(agent_id, limit=5)` → Jaccard interest overlap
  - `get_recommendations(agent_id)` → agents who SHOULD connect but haven't
  - `upsert_relationship(a, b, updates)` → create/update KNOWS edge
- `src/routes/graph.py` — GET network, GET recommendations

### 2.5 Memory Service (Foundation — Hot Tier Only)
- `src/services/memory.py`:
  - `store_memory(agent_id, content, type, privacy_level, importance, source_conv_id)`
  - `retrieve_memories(agent_id, query, accessor_agent_id, limit=5)` → permission-filtered Qdrant search on hot collection
  - Always filter by tenant_id + permission level

### 2.6 Seed Script
- `scripts/seed_demo.py`: 1 tenant, 1 user, 10 agents (diverse Big Five, varied archetypes), 5 KNOWS edges, 3 Topic nodes
- **Note:** 5 of the 10 agents must be mock agents with `is_mock=True`. Mock agents are auto-connected to every new user at trust=0.2. They have diverse archetypes (one per archetype category) and predefined interests spanning common topics.

### 2.8 Connection Service
- `src/models/connection.py` — ConnectionInvite, ConnectionRequest, ConnectionResponse, ConnectionList
- `src/services/connection.py`:
  - `generate_invite(agent_id)` → invite token + shareable link
  - `send_request(from_agent_id, to_agent_id, invite_token, message)` → pending request
  - `respond_to_request(request_id, action: 'accept'|'reject')` → on accept: create KNOWS edge (trust=0.2), auto-derive permission
  - `list_requests(agent_id, status='pending')` → list of pending requests
  - `list_connections(agent_id)` → connections with trust levels and permission info
  - `auto_connect_mock_agents(agent_id)` → connect new agent to all 5 mock agents (trust=0.2)
- `src/routes/connections.py`:
  - POST /api/v1/connections/invite
  - POST /api/v1/connections/request
  - GET /api/v1/connections/requests
  - PATCH /api/v1/connections/requests/{id}
  - GET /api/v1/agents/{id}/connections

### 2.7 Tests
- `tests/unit/test_personality.py` — scoring, archetype assignment, compatibility, prompt generation
- `tests/unit/test_onboarding.py` — scenario scoring, normalization
- `tests/unit/test_permission.py` — level checks, filtering, audit logging
- `tests/integration/test_agent_crud.py` — full CRUD + Neo4j sync
- `tests/integration/test_onboarding_flow.py` — scenarios → answers → agent creation
- `tests/integration/test_graph.py` — network query, recommendations

## Checkpoint
```bash
uv run pytest tests/ -x && echo "Phase 2 DONE"
git commit -m "feat: Phase 2 — agents + onboarding + graph + permissions" && git tag v0.2.0
```
