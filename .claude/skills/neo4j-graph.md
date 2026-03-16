---
name: neo4j-graph
description: Work on Neo4j Cypher queries, graph schema, KNOWS edges, community detection, entity-relation storage, Group/Event nodes, or src/db/neo4j_client.py and src/services/graph.py
allowed-tools: Read, Bash, Grep, Glob, Edit, Write
---

# Skill: Neo4j & Graph Operations

## When to use
Use this skill when writing Cypher queries, working with the social knowledge graph, community detection, graph recommendations, or anything in `src/services/graph.py` or `src/db/neo4j_client.py`.

## Node Types
- **Agent:** id, tenant_id, display_name, interests[], openness, extraversion, community_id, is_mock
- **Topic:** id, name, description, mention_count, growth_rate
- **Conversation:** id, started_at, turn_count, summary, quality_score, background, mode
- **Insight:** id, content, importance, bloom_relevance, verification_status, skeptic_score
- **Entity:** id, name, type (concept/technology/organization/person/claim), description, confidence
- **Community:** id, name, summary, member_count, formed_at
- **Group:** id, name, group_type (interest/skill/project/social), member_count
- **Event:** id, name, event_type (hackathon/debate/research/game), status, starts_at, ends_at

## Relationship Types
- `(Agent)-[:KNOWS {strength, trust, topics_shared[], conversation_count, trust_history[], manual_permission_override}]->(Agent)`
- `(Agent)-[:PARTICIPATED_IN {role, messages_sent}]->(Conversation)`
- `(Conversation)-[:DISCUSSED]->(Topic)`
- `(Conversation)-[:PRODUCED]->(Insight)`
- `(Agent)-[:INTERESTED_IN {intensity}]->(Topic)`
- `(Agent)-[:MEMBER_OF]->(Community)`
- `(Agent)-[:BELONGS_TO {role, joined_at}]->(Group)`
- `(Agent)-[:REGISTERED_FOR {team_id}]->(Event)`
- `(Group)-[:HOSTED]->(Event)`
- `(Insight)-[:RELATES_TO]->(Topic)`
- `(Insight)-[:DISCOVERED_BY]->(Agent)`
- `(Entity)-[:CAUSES|CONTRADICTS|SUPPORTS|SUPERSEDES|RELATES_TO]->(Entity)`
- `(Entity)-[:MENTIONED_IN]->(Conversation)`

## Common Queries

### Get agent network (for D3.js graph)
```cypher
MATCH (a:Agent {id: $agentId})-[r:KNOWS]-(b:Agent)
WHERE a.tenant_id = $tenantId
RETURN a, r, b
```

### Get best unexplored pair (for scheduler EXPLORE)
```cypher
MATCH (a:Agent {tenant_id: $tenantId}), (b:Agent {tenant_id: $tenantId})
WHERE a.id <> b.id
  AND NOT (a)-[:KNOWS]-(b)
  AND any(interest IN a.interests WHERE interest IN b.interests)
RETURN a.id, b.id, 
       [x IN a.interests WHERE x IN b.interests] AS shared
ORDER BY size(shared) DESC
LIMIT 1
```

### Update trust after conversation
```cypher
MATCH (a:Agent {id: $aid})-[r:KNOWS]-(b:Agent {id: $bid})
SET r.trust = CASE 
    WHEN r.trust + $delta > 1.0 THEN 1.0
    WHEN r.trust + $delta < 0.0 THEN 0.0
    ELSE r.trust + $delta
END,
r.conversation_count = r.conversation_count + 1,
r.last_interaction = datetime(),
r.trust_history = r.trust_history[-9..] + [r.trust + $delta]
```

### Trending topics
```cypher
MATCH (c:Conversation)-[:DISCUSSED]->(t:Topic)
WHERE c.started_at > datetime() - duration({days: 7})
WITH t, count(c) AS this_week
OPTIONAL MATCH (c2:Conversation)-[:DISCUSSED]->(t)
WHERE c2.started_at > datetime() - duration({days: 14})
  AND c2.started_at <= datetime() - duration({days: 7})
WITH t, this_week, count(c2) AS last_week
RETURN t.name, this_week, last_week, 
       CASE WHEN last_week = 0 THEN this_week ELSE toFloat(this_week)/last_week END AS growth
ORDER BY growth DESC
LIMIT 10
```

### Multi-hop entity query (for GraphRAG)
```cypher
MATCH path = (e1:Entity)-[*1..3]-(e2:Entity)
WHERE e1.name CONTAINS $query OR e2.name CONTAINS $query
RETURN path
LIMIT 20
```

## Community Detection
Neo4j Aura Free doesn't have GDS plugin. Use networkx:
```python
import networkx as nx
from cdlib import algorithms

# Export graph to networkx
G = nx.Graph()
agents = await neo4j.run_query("MATCH (a:Agent {tenant_id: $tid}) RETURN a", ...)
edges = await neo4j.run_query("MATCH (a)-[r:KNOWS]-(b) RETURN a.id, b.id, r", ...)
# Add nodes and weighted edges
# Run Leiden algorithm
communities = algorithms.leiden(G, weights='weight')
# Write back to Neo4j as Community nodes + MEMBER_OF edges
```

## Rules
- EVERY query MUST filter by tenant_id (multi-tenancy)
- ALWAYS use parameterized queries (never string interpolation)
- KNOWS edges are bidirectional — use undirected pattern `(a)-[:KNOWS]-(b)`
- Trust is on the KNOWS edge, NOT on the Agent node
- When creating KNOWS edges for new connections, ALWAYS set initial trust
