# Phase 5: Frontend + Avatar + Demo + Deployment
# Engineering Layer: INTERFACE (face — making emergence visible)
# Estimated: 4-5 days | Prerequisite: Phase 4

## Completion Criteria
- [ ] Interactive D3.js force-directed graph with communities, agent nodes, edges
- [ ] Click agent → personality radar chart + conversation history
- [ ] Click edge → Socratic debate transcript viewer
- [ ] Trigger conversation from UI → watch graph update
- [ ] Teach-back UI: click insight → avatar appears → Socratic tutoring
- [ ] Privacy dashboard: permission controls + audit log
- [ ] Insights feed panel with "Teach me" buttons
- [ ] Deployed: backend (Railway), frontend (Vercel), databases (free tiers)
- [ ] Demo video recorded (3 minutes)
- [ ] README.md recruiter-optimized

## Layer Test
"Can a stranger watch a 3-minute demo and understand: (1) agents debate on a graph, (2) communities emerge, (3) they get taught by a talking avatar what their agent discovered?"

## Tasks

### 5.1 React App Setup
- `npx create-next-app@latest frontend --typescript --tailwind --app`
- Add: d3, @radix-ui/react-*, lucide-react, recharts, axios, zustand
- Layout: sidebar (nav) + main (graph/panels split 60/40)
- `frontend/src/lib/api.ts` — axios client + JWT interceptor

### 5.2 Graph Visualization
- `frontend/src/components/graph/GraphView.tsx`:
  - D3.js force-directed layout
  - Nodes: sized by connections, colored by community (Leiden clusters)
  - Edges: width = strength, opacity = trust
  - Click node → dispatch to AgentPanel
  - Click edge → dispatch to ConversationViewer
  - Hover → tooltip (name + interests)
  - Zoom + pan + drag
  - Community hulls: convex hull around each community (semi-transparent)
  - Animation: new edges appear with fade-in when conversation completes
  - Fetch: GET /api/v1/graph/agents/{id}/network?hops=3

### 5.3 Agent Panel
- `frontend/src/components/panels/AgentPanel.tsx`:
  - Personality radar chart (recharts RadarChart — 5 axes for Big Five)
  - Interests as tags
  - Communication style badge
  - Community membership
  - Recent conversations list (click to view)
  - "Start conversation with..." button → trigger modal
  - Compatibility score with selected agent

### 5.4 Conversation Viewer
- `frontend/src/components/panels/ConversationViewer.tsx`:
  - Chat-style bubbles (left = Agent A, right = Agent B)
  - Phase indicator at each turn (OPEN, PROBE, DEEPEN, etc.)
  - Extracted insights highlighted in colored cards at bottom
  - Audit section (expandable): data accessed, permission levels used
  - Quality score badge

### 5.5 Insights Feed
- `frontend/src/components/panels/InsightsFeed.tsx`:
  - Card list: "Your agent discovered [X] from [Agent_Name]"
  - Each card: topic tag, importance score, "Teach me" button
  - Click "Teach me" → opens TeachBack panel

### 5.6 Teach-Back Panel
- `frontend/src/components/panels/TeachBackPanel.tsx`:
  - Top: Avatar video player (plays SadTalker output)
  - Middle: Chat transcript (tutor questions + learner responses)
  - Bottom: Text input for learner responses
  - Bloom level indicator: visual progress bar (1-6)
  - "Loading avatar..." state while SadTalker renders (show text immediately)
  - Session complete → Bloom level update animation

### 5.7 Conversation Trigger
- `frontend/src/components/modals/TriggerConversation.tsx`:
  - Select target agent (dropdown or click on graph)
  - Enter topic (or pick from trending)
  - "Debate" button → POST /api/v1/conversations
  - "Broadcast" button → POST /api/v1/conversations/broadcast
  - Loading state → redirect to conversation viewer

### 5.8 Privacy Dashboard
- `frontend/src/components/panels/PrivacyDashboard.tsx`:
  - Table: agents you've interacted with, current permission level, dropdown to change
  - Audit log table: timestamp, action, data category, permission level
  - Visual: pie chart of data access by category

### 5.9 Dashboard Page
- `frontend/src/app/dashboard/page.tsx`:
  - Graph (60%) | Panel area (40%)
  - Tab switching: Agent Detail | Conversation | Insights | Teach-Back | Privacy
  - Top bar: trending topics, community count, agent count

### 5.10 Deployment
- Backend → Railway (connect GitHub, auto-deploy)
  - Set all env vars
  - Connect to: Neo4j Aura Free, Qdrant Cloud Free, Supabase Free, Redis (Upstash Free)
- Frontend → Vercel (connect GitHub)
  - NEXT_PUBLIC_API_URL = Railway backend URL
- SearXNG → Railway (separate service, Dockerfile)
- Test full flow on deployed URLs

### 5.11 Demo Video (3 minutes)
Record with screen recorder showing:
1. **(0:00-0:30)** Graph with 10 agents. Point out communities, edges, colors. "These communities FORMED THEMSELVES."
2. **(0:30-1:00)** Trigger a conversation. Watch two agents have a Socratic debate about sustainability. Show the phases.
3. **(1:00-1:30)** Show extracted insights. "The system discovered that carbon-aware scheduling has a hidden overhead cost — neither agent knew this individually."
4. **(1:30-2:00)** Click "Teach me." Avatar appears, assesses your level, teaches you via Socratic questions. Show Bloom level updating.
5. **(2:00-2:30)** Privacy dashboard. "Every data access is logged. I can see exactly what my agent shared with each connection."
6. **(2:30-3:00)** Show the fine-tuning dashboard. "Every night, the system trains on the best conversations. Agents are measurably better every morning."

### 5.12 README.md
Structure:
- Banner: screenshot of graph with communities
- One paragraph: what NexusMind is
- Tech stack badges
- Architecture diagram (simplified)
- Quick start: `docker compose up && uv run uvicorn src.main:app`
- Demo video embed
- Key features (6 bullet points mapping to engineering layers)
- Research papers referenced
- Self-improving loop explanation
- License: MIT

## Checkpoint
`uv run pytest tests/ -x && echo "ALL PHASES COMPLETE — NEXUSMIND IS ALIVE"`
`git commit -m "feat: Phase 5 — interface + demo + deployment" && git tag v1.0.0`
