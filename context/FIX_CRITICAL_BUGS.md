# FIX_CRITICAL_BUGS.md — Step 1
# Fix these BEFORE adding any new features.
# Each fix is independent. Test after each.

## BUG 1: Axios Network Error (blocks everything)

The frontend gets `AxiosError: Network Error` on every API call.

### Diagnosis checklist (check in order):

1. Is backend running? `curl http://localhost:8000/health`
2. Is CORS configured in src/main.py?
```python
# This MUST exist in main.py BEFORE any router is included:
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```
3. Is the frontend API base URL correct?
   Find the axios config file (likely frontend/src/lib/api.ts).
   baseURL must be `http://localhost:8000` (not https, not empty, no trailing slash).
   Check for NEXT_PUBLIC_API_URL in .env.local or next.config.js.

4. Is the JWT token being sent?
```typescript
// In the axios instance, add request interceptor:
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});
```

5. Check backend terminal for Python errors (import errors, DB connection failures, migration not run).

### Test: 
Open browser console (F12 → Network tab), refresh dashboard. 
API calls should return 200, not ERR_NETWORK.

---

## BUG 2: Graph shows "No graph data available"

Header says "7 agents" but graph is empty.

### Root cause: 
KNOWS edges not created in Neo4j when new agent is created.

### Fix:
In the agent creation service, AFTER creating the agent node in Neo4j, 
add this logic:

```python
# After creating agent in Postgres AND syncing to Neo4j:
# Find all other agents in this tenant and create KNOWS edges
other_agents = await self.db.fetch(
    "SELECT id FROM agents WHERE tenant_id = $1 AND id != $2",
    tenant_id, new_agent_id
)
for other in other_agents:
    await self.neo4j.run_query("""
        MATCH (a:Agent {id: $aid}), (b:Agent {id: $bid})
        MERGE (a)-[r:KNOWS]->(b)
        ON CREATE SET r.strength = 0.3, r.trust = 0.3,
                      r.topics_shared = [], r.conversation_count = 0,
                      r.last_interaction = datetime()
    """, {"aid": new_agent_id, "bid": other["id"]})
```

Also verify the graph API endpoint returns the correct format:
```python
# GET /api/v1/graph/agents/{id}/network must return:
{
    "nodes": [
        {"id": "...", "display_name": "...", "archetype": "...", 
         "interests": [...], "is_current_user": true/false},
        ...
    ],
    "edges": [
        {"source": "id1", "target": "id2", "strength": 0.3, "trust": 0.3},
        ...
    ]
}
```

Check the frontend GraphView component: is it calling the API with the 
correct agent_id? Add console.log to debug what the API returns.

### Test:
After fix, refresh dashboard. Graph should show your agent + other agents with edge lines.

---

## BUG 3: Dashboard shows wrong agent

Onboarding result shows "Yash / The Commander" but dashboard shows "Maverick / The Diplomat".

### Root cause:
Dashboard loads a random agent instead of the current user's agent.

### Fix:
1. After onboarding creates the agent, store the ID:
```typescript
// In onboarding completion handler:
const response = await api.post("/api/v1/agents", agentData);
localStorage.setItem("my_agent_id", response.data.id);
```

2. Add a /api/v1/users/me endpoint:
```python
@router.get("/api/v1/users/me")
async def get_me(user = Depends(get_current_user)):
    agent = await agent_service.get_by_user_id(user.id)
    return {"user": user, "agent": agent}
```

3. Dashboard loads MY agent:
```typescript
// On dashboard mount:
const { data } = await api.get("/api/v1/users/me");
setMyAgent(data.agent);
```

### Test:
After fix, dashboard Agent tab shows YOUR agent name and archetype.

---

## BUG 4: Graph nodes need hover tooltips

Nodes exist on graph but show no info on hover.

### Fix:
In the D3.js GraphView component, add mouseover handler to node circles:
```tsx
// On each node group, add:
.on("mouseenter", (event, d) => {
  setTooltip({
    visible: true,
    x: event.pageX + 12,
    y: event.pageY - 12,
    agent: d,
  });
})
.on("mouseleave", () => {
  setTooltip({ visible: false, x: 0, y: 0, agent: null });
});

// Render tooltip as absolute-positioned div:
{tooltip.visible && tooltip.agent && (
  <div className="absolute z-50 bg-gray-800 border border-gray-600 rounded-lg p-3 shadow-xl pointer-events-none"
       style={{ left: tooltip.x, top: tooltip.y }}>
    <div className="font-bold">{tooltip.agent.display_name}</div>
    <div className="text-sm text-gray-400">{tooltip.agent.archetype}</div>
    <div className="flex flex-wrap gap-1 mt-1">
      {tooltip.agent.interests?.slice(0, 4).map(i => (
        <span key={i} className="text-xs bg-gray-700 px-2 py-0.5 rounded-full">{i}</span>
      ))}
    </div>
  </div>
)}
```

Also: clicking a node should update the right panel to show that agent's details.

---

## BUG 5: Empty states everywhere

All tabs show blank content with no guidance.

### Fix:
Add helpful empty states to EVERY tab:

```tsx
// Reusable component:
function EmptyState({ icon, title, description, actionLabel, onAction }) {
  return (
    <div className="text-center py-16">
      <div className="text-4xl mb-4">{icon}</div>
      <h3 className="text-lg font-medium text-gray-200">{title}</h3>
      <p className="text-gray-400 mt-2 max-w-sm mx-auto">{description}</p>
      {actionLabel && (
        <button onClick={onAction} className="mt-4 px-4 py-2 bg-purple-600 rounded-lg">
          {actionLabel}
        </button>
      )}
    </div>
  );
}

// Usage per tab:
// Conversation: "No conversations yet. Start a debate to see transcripts here."
// Insights: "Insights appear after conversations. Each debate produces discoveries."
// Teach-Back: "Complete a conversation first. Your tutor teaches what your agent discovers."
// Privacy: "Permission data appears after you interact with other agents."
// Evolution: "The evolution engine starts after conversations generate training data."
```

---

## BUG 6: "Start Conversation" needs agent picker

The button exists but doesn't let you choose who to debate.

### Fix:
When clicked, show a modal with connected agents:

```tsx
// Agent picker modal content:
<Dialog>
  <h2>Start a Conversation</h2>
  
  <div className="space-y-2 mt-4">
    <label className="text-sm text-gray-400">Choose who to debate with:</label>
    {connectedAgents.map(agent => (
      <button
        key={agent.id}
        onClick={() => setSelected(agent)}
        className={`w-full p-3 rounded-lg border flex items-center gap-3 text-left
          ${selected?.id === agent.id ? 'border-purple-500 bg-purple-900/20' : 'border-gray-700'}`}
      >
        <div className="w-10 h-10 rounded-full bg-purple-600 flex items-center justify-center font-bold">
          {agent.display_name[0]}
        </div>
        <div>
          <div className="font-medium">{agent.display_name}</div>
          <div className="text-xs text-gray-400">{agent.archetype}</div>
        </div>
      </button>
    ))}
  </div>
  
  <input
    className="w-full mt-4 p-2 bg-gray-800 border border-gray-600 rounded"
    placeholder="Topic to debate..."
    value={topic}
    onChange={e => setTopic(e.target.value)}
  />
  
  <button
    onClick={() => startConversation(selected.id, topic)}
    disabled={!selected || !topic}
    className="w-full mt-4 py-3 bg-purple-600 rounded-lg disabled:opacity-50"
  >
    Start Debate
  </button>
</Dialog>
```

After triggering, switch to Conversation tab and show the transcript.

### Test:
Click "Start Conversation" → modal with agents → pick one → enter topic → debate runs → transcript shows.
