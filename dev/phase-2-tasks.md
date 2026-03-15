# Phase 2: Agents + Personality + Graph + Permissions
# Engineering Layer: AGENTIC (skeleton complete)
# Estimated: 3-4 days | Prerequisite: Phase 1

## Completion Criteria
- [ ] CRUD agents with Big Five personality via API
- [ ] Agent synced to Neo4j node on create/update
- [ ] Permission system: set, check, audit — zero unauthorized access
- [ ] PersonalityService generates consistent system prompts
- [ ] Graph queries: get network, find similar agents, recommendations
- [ ] `scripts/seed_demo.py` creates 10 diverse agents with graph edges
- [ ] All tests pass

## Layer Test
"Can I create 10 agents with different personalities and see them on a graph with edges?"

## Tasks

### 2.1 Agent Models + Routes
- `src/models/agent.py` — AgentCreate, AgentResponse, AgentUpdate, PersonalityProfile
- `src/services/agent_service.py` — CRUD with Postgres + Neo4j sync
- `src/routes/agents.py` — POST/GET/PATCH/DELETE + list (all tenant-scoped)

### 2.2 Personality Service
- `src/services/personality.py`:
  - `generate_system_prompt(agent, phase, context)` → personality-grounded prompt
  - `compute_communication_style(agent)` → analytical/expressive/driver/amiable
  - `compute_compatibility(agent_a, agent_b)` → 0-1 score
  - `assign_archetype(agent)` → nearest of 6 LoRA archetypes
  - Use prompt template from ARCHITECTURE.md §5

### 2.3 Permission System
- `src/models/permission.py` — PermissionSet, PermissionCheck, AuditEntry
- `src/services/permission.py`:
  - `set_permission(agent_id, target_agent_id, level)`
  - `get_effective_level(source, target)` → int (override > default > tenant)
  - `check_access(source, target, required_level, category)` → bool + audit log
  - `filter_by_permission(items, accessor, source)` → filtered
- `src/routes/permissions.py` — POST/GET permissions, GET audit

### 2.4 Graph Service
- `src/services/graph.py`:
  - `get_agent_network(agent_id, hops=2)` → nodes + edges for D3.js
  - `find_similar_agents(agent_id, limit=5)` → by interest Jaccard overlap
  - `get_recommendations(agent_id)` → agents who SHOULD connect but haven't
  - `upsert_relationship(a, b, updates)` → create/update KNOWS edge
- `src/routes/graph.py` — GET network, GET recommendations, GET communities

### 2.5 Memory Service (Foundation)
- `src/services/memory.py`:
  - `store_memory(agent_id, content, type, privacy_level, source_conv_id)`
  - `retrieve_memories(agent_id, query, accessor_agent_id, limit=5)` → permission-filtered
  - Qdrant search with tenant_id + permission filter

### 2.6 Seed Script
- `scripts/seed_demo.py`: 1 tenant, 1 user, 10 agents (diverse Big Five), 5 KNOWS edges, 3 Topics

### 2.7 Tests
- `tests/unit/test_personality.py` — prompt generation, compatibility, archetype assignment
- `tests/unit/test_permission.py` — level checks, filtering, audit logging
- `tests/integration/test_agent_crud.py` — full CRUD + Neo4j sync
- `tests/integration/test_graph.py` — network query, recommendations

## Checkpoint
`uv run pytest tests/ -x && echo "Phase 2 DONE"`
`git commit -m "feat: Phase 2 — agents + personality + graph + permissions" && git tag v0.2.0`
