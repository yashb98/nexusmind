---
name: memory-system
description: Work on memory storage/retrieval, 3-tier hot/graph/cold architecture, Qdrant collections, GraphRAG entity extraction, contradiction handling, memory lifecycle, or src/services/memory.py
allowed-tools: Read, Bash, Grep, Glob, Edit, Write
---

# Skill: Three-Tier Memory System

## When to use
Use this skill when working on memory storage, retrieval, lifecycle management, GraphRAG entity extraction, or anything in `src/services/memory.py`, `src/services/knowledge.py`, or Qdrant/Neo4j queries.

## Architecture

### Tier 1: Hot Memory (Qdrant `agent_memories_hot`)
- Content: Last 30 days of conversation insights, high-importance facts (>0.7)
- Vector size: 768 (all-MiniLM-L6-v2)
- Always searched FIRST
- Payload filter: tenant_id + permission_level_required <= accessor's level
- expires_at: 30 days from creation (extended if importance >= 0.7)

### Tier 2: Knowledge Graph (Neo4j entities + relations)
- Content: Extracted entities with typed relations (CAUSES, CONTRADICTS, SUPPORTS, SUPERSEDES)
- Each entity has: name, type, description, confidence, verification_status
- Searched SECOND (when hot returns < 3 results)
- Enables multi-hop reasoning: "How does X connect to Z through Y?"

### Tier 3: Cold Archive (Qdrant `agent_memories_cold`)
- Content: Memories older than 90 days with importance < 0.3
- Only searched as FALLBACK (when hot + graph return < 3 results)
- Cleanup: delete if never retrieved in 6 months (last_retrieved = null)

### Retrieval Cascade
```python
async def retrieve_memories(self, agent_id, query, accessor_agent_id, limit=5):
    results = []
    
    # 1. Search hot (fast, recent, high-importance)
    hot_results = await self.qdrant.search("agent_memories_hot", 
        vector=embed(query),
        filter={"tenant_id": tenant_id, "privacy_level_required": {"$lte": accessor_level}},
        limit=limit)
    results.extend(hot_results)
    
    # 2. If insufficient, search Neo4j graph (multi-hop)
    if len(results) < 3:
        graph_results = await self.graph.multi_hop_query(query, max_hops=3)
        results.extend(graph_results)
    
    # 3. If still insufficient, search cold archive
    if len(results) < 3:
        cold_results = await self.qdrant.search("agent_memories_cold", ...)
        results.extend(cold_results)
    
    return results[:limit]
```

### Contradiction Handling
When a new entity contradicts an existing one:
1. DO NOT delete the old entity
2. Mark old entity with `superseded_at` timestamp in Neo4j
3. Create SUPERSEDES relation: (new_entity)-[:SUPERSEDES]->(old_entity)
4. Retrieval always prefers newest version (sort by discovered_at DESC)
5. Old version available for provenance queries

### Lifecycle (runs daily)
1. Hot memories > 30 days old + importance < 0.3 → move to cold
2. Hot memories > 30 days old + importance >= 0.3 → extend expiry 30 more days
3. Cold memories with last_retrieved = null AND archived > 6 months → delete

### GraphRAG Entity Extraction
After each conversation, extract:
- Entities: concepts, technologies, organizations, claims
- Relations: CAUSES, CONTRADICTS, SUPPORTS, RELATES_TO
- Each relation has: confidence, source_conversation_id, discovered_at
- Store in Neo4j, embed in Qdrant hot collection

### Rules
- EVERY retrieval MUST filter by tenant_id
- EVERY retrieval MUST check permission_level
- Update last_retrieved timestamp on every access (for lifecycle cleanup)
- Facts go to MEMORY (searchable, updatable). Patterns go to WEIGHTS (LoRA).
- NEVER store unverified knowledge with high confidence
