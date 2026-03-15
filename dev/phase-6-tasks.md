# Phase 6: Frontend + Avatar UI + Deployment + Demo
# Engineering Layer: INTERFACE (face — making the living system visible)
# Estimated: 5-6 days | Prerequisite: Phase 5

## Completion Criteria
- [ ] 4-step personality onboarding UI (scenarios, radar chart result)
- [ ] Interactive D3.js graph with communities, agent nodes, edges, hulls
- [ ] Click agent → personality radar chart + stats + conversations
- [ ] Click edge → Socratic debate transcript with phase indicators
- [ ] Insights feed with verification badges (✓ Accepted, ⚠ Provisional, ✗ Rejected)
- [ ] "Teach me" button → teach-back panel with avatar video + Bloom progress
- [ ] Privacy dashboard: permissions + audit log
- [ ] Evolution dashboard: proposals, fine-tune history, scheduler stats
- [ ] Trigger conversation from UI
- [ ] Deployed: backend (Railway), frontend (Vercel), DBs (free tiers)
- [ ] Demo video (3 minutes)
- [ ] README.md with screenshot, demo video, architecture diagram

## Layer Test
"Can a stranger watch a 3-minute demo and understand: (1) agents debate autonomously, (2) knowledge is verified by a council, (3) communities emerge, (4) they can be taught by an avatar, (5) the system improves itself?"

## Tasks

### 6.1 React App Setup
- `npx create-next-app@latest frontend --typescript --tailwind --app`
- Add: d3, @radix-ui/react-*, lucide-react, recharts, axios, zustand
- Layout: sidebar nav + main content (graph 60% | panels 40%)
- `frontend/src/lib/api.ts` — axios client + JWT interceptor

### 6.2 Onboarding Flow
- `frontend/src/app/onboarding/page.tsx`:
  - Step 1: Agent name + avatar (upload or 6 presets, click to select)
  - Step 2: Interest selection (visual cards, click to toggle, 3-10 required)
  - Step 3: 10 scenario questions (one per page, progress bar, animated transitions)
  - Step 4: Privacy level (3 options with plain-language descriptions)
  - Result: animated radar chart + personality summary + archetype badge + "Launch" button
  - POST /onboarding/personality → POST /agents → redirect to dashboard

### 6.3 Graph Visualization
- `frontend/src/components/graph/GraphView.tsx`:
  - D3.js force-directed layout
  - Nodes: sized by connections, colored by community (distinct colors per community)
  - Edges: width = strength, opacity = trust
  - Community hulls: convex hull (semi-transparent) around each community
  - Hover node → tooltip (name, interests, archetype)
  - Click node → dispatch to AgentPanel
  - Click edge → dispatch to ConversationViewer
  - Zoom + pan + drag
  - Animation: new edges fade-in after background conversations complete
  - Auto-refresh: poll every 30s (or manual refresh button)
  - Fetch: GET /graph/agents/{id}/network?hops=3

### 6.4 Agent Panel
- `frontend/src/components/panels/AgentPanel.tsx`:
  - Personality radar chart (Recharts RadarChart — 5 axes)
  - Interests as colored tag pills
  - Communication style badge
  - Community membership
  - Archetype name + description
  - Recent conversations list (click to view)
  - Compatibility score with selected agent
  - "Start conversation with..." button

### 6.5 Conversation Viewer
- `frontend/src/components/panels/ConversationViewer.tsx`:
  - Chat bubbles (left = Agent A, right = Agent B)
  - Phase indicator at each turn (colored badge: OPEN/PROBE/DEEPEN/CHALLENGE/SYNTHESIZE)
  - Background conversation badge (if triggered by scheduler)
  - Extracted insights as colored cards at bottom
  - Extracted entities as a mini knowledge graph (D3.js force layout, small)
  - Verification badge per insight (✓ / ⚠ / ✗ with tooltip showing council reasoning)
  - Quality score badge
  - Audit expandable section

### 6.6 Insights Feed
- `frontend/src/components/panels/InsightsFeed.tsx`:
  - Card list: "Your agent discovered [X] from [Agent_Name]"
  - Verification status badge per card (✓ Accepted / ⚠ Provisional / ✗ Rejected)
  - Topic tag, importance score
  - "Teach me" button (only for ACCEPTED + PROVISIONAL)
  - Filter: all / verified only / unverified

### 6.7 Teach-Back Panel
- `frontend/src/components/panels/TeachBackPanel.tsx`:
  - Top: Avatar video player (SadTalker output, loading state while rendering)
  - Middle: Chat transcript (tutor Q + learner A, styled differently)
  - Bottom: Text input + send button (+ microphone icon for future STT)
  - Bloom level indicator: visual 6-segment progress bar with labels
  - Level-up animation when Bloom increases
  - Session complete → summary + "Bloom level updated" celebration

### 6.8 Privacy Dashboard
- `frontend/src/components/panels/PrivacyDashboard.tsx`:
  - Table: agents you've interacted with, current permission level, dropdown to change
  - Audit log table: timestamp, action, data category, permission level, langfuse trace link
  - Pie chart: data access by category

### 6.9 Evolution Dashboard
- `frontend/src/components/panels/EvolutionDashboard.tsx`:
  - **Scheduler tab:** Status (running/paused), cycle count, mode distribution pie chart, conversations/hour
  - **Fine-tune tab:** History table (date, type, archetype, val_loss, personality_variance, deployed Y/N)
  - **Proposals tab:** List of research + code proposals (status, scores, expand for detail)
  - **Metrics tab:** Line charts: conversation quality over time, Bloom progression rates, verification acceptance rate
  - Pause/Resume scheduler button (admin only)

### 6.10 Conversation Trigger
- `frontend/src/components/modals/TriggerConversation.tsx`:
  - Select target agent (dropdown or click graph node)
  - Enter topic or pick from trending (pills)
  - "Debate" button → POST /conversations
  - "Broadcast" → POST /conversations/broadcast
  - Loading → redirect to conversation viewer

### 6.11 Dashboard Page
- `frontend/src/app/dashboard/page.tsx`:
  - Graph (60%) | Panels (40%)
  - Tab switching: Agent | Conversation | Insights | Teach-Back | Privacy | Evolution
  - Top bar: agent count, community count, trending topics (3), scheduler status indicator

### 6.12 Deployment
- Backend → Railway:
  - Connect GitHub repo, auto-deploy on push
  - Set ALL env vars from .env
  - Connect: Neo4j Aura Free, Qdrant Cloud Free, Supabase Free, Upstash Redis Free
  - SearXNG → separate Railway service (Dockerfile)
  - Background scheduler: runs as part of FastAPI lifespan (or separate worker)
- Frontend → Vercel:
  - Connect GitHub, NEXT_PUBLIC_API_URL = Railway URL
- Test full flow on deployed URLs

### 6.13 Demo Video (3 minutes)
Record with screen recorder:
1. **(0:00-0:20)** Onboarding: complete 4 steps, see radar chart. "This took 5 minutes."
2. **(0:20-0:50)** Graph: 10 agents, 2 communities with colored hulls. "These communities FORMED THEMSELVES from 100 autonomous conversations."
3. **(0:50-1:10)** Click a conversation. Show Socratic phases. "Agent A challenged Agent B's assumption about carbon scheduling."
4. **(1:10-1:30)** Insights feed. Show verification badges. "The Verification Council caught a claim with insufficient evidence."
5. **(1:30-2:00)** "Teach me" → avatar appears, asks Socratic questions, Bloom level increases. "The system adapted to my level."
6. **(2:00-2:20)** Privacy dashboard. "Every data access is logged."
7. **(2:20-2:50)** Evolution dashboard. "Agents run 24/7 in the background. The model trains every hour. Quality scores are up 12% since Day 1."
8. **(2:50-3:00)** "NexusMind: AI agents that never sleep — they debate, discover, verify, teach, and get smarter every hour."

### 6.14 README.md
- Banner: screenshot of graph with community hulls
- One paragraph: what NexusMind is
- Tech stack badges
- Architecture diagram (simplified — show 5 layers)
- Quick start: `docker compose up && uv run uvicorn src.main:app && uv run python scripts/run_scheduler.py`
- Demo video embed
- Key features (6 bullets mapping to layers):
  1. Personality-driven AI agents (Agentic)
  2. Socratic debate protocol (Process)
  3. Verification Council — knowledge immune system (Environment)
  4. Always-on agents + self-improving model (Evolution)
  5. Bloom-adapted avatar tutor (Environment/Interface)
  6. Emergent community intelligence (Environment)
- Self-improving loop diagram
- Research papers referenced (10 papers)
- Cost: "£35-55 total to build + 1-week demo"
- License: MIT

## Checkpoint
```bash
uv run pytest tests/ -x && echo "ALL PHASES COMPLETE — NEXUSMIND IS ALIVE"
git commit -m "feat: Phase 6 — interface + deployment + demo" && git tag v1.0.0
git push origin main --tags
```
