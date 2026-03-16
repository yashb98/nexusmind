---
name: frontend-patterns
description: Work on React/Next.js frontend components, D3.js graph visualization, WebSocket streaming, dashboard layout, dark theme styling, empty states, or any file in frontend/
allowed-tools: Read, Bash, Grep, Glob, Edit, Write
---

# Skill: Frontend Patterns

## When to use
Working on any frontend component, pages, navigation, D3.js graph, WebSocket, streaming UI.

## Tech Stack
React 18 + Next.js (App Router) + TypeScript + TailwindCSS + shadcn/ui + D3.js + Recharts + Axios + Zustand

## Navigation Structure
```
/dashboard     → Home/Feed (activity feed)
/network       → Graph + Connections (existing dashboard content, moved here)
/groups        → My groups + Discover + Group detail pages
/events        → Upcoming + Live + Past + Event detail pages
/learn         → Knowledge map + Available lessons + Active sessions
/profile       → Account + Agent + Privacy + Tutor + Notifications + Learning progress
/onboarding    → 4-step flow (basics → interests → dynamic scenarios → privacy → result)
```
Header: `NexusMind [nav items] [🔔 notifications] [👤 Profile]`

## Streaming Chat (WebSocket)
ALL user-facing conversations stream token-by-token:
```typescript
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  if (data.type === "turn_start") addNewEmptyBubble(data);
  if (data.type === "token") appendTokenToLastBubble(data.content);
  if (data.type === "turn_end") markBubbleComplete();
};
// Show blinking cursor while streaming=true on the last bubble
```

## Conversation Viewer (Split Panel)
LEFT (60%): Agent debate — streaming chat bubbles with mode+phase badges.
RIGHT (40%): Embedded tutor — commentary, learner input, Bloom bar, avatar.
Tutor has minimize button. Auto-minimizes if user doesn't interact for 30s.
Two WebSocket channels: /live (debate) and /tutor (commentary).

## D3.js Graph
Nodes: sized by connections, colored by community. Current user's node highlighted.
Edges: width=strength, opacity=trust.
Hover: tooltip with name, archetype, interests, trust %.
Click node: update right panel to show that agent's details.
Community hulls: semi-transparent convex polygons.

## Start Conversation Modal
Shows: list of connected agents (name, archetype, trust, shared interests) + topic input + mode selector (casual/socratic/brainstorm etc.) + trending topic pills.

## Empty States (MANDATORY)
Every panel/page with no data shows: icon + title + description + action button.
Never show blank space or "0%" badges on empty data.

## API Client
```typescript
const api = axios.create({ baseURL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000" });
// JWT interceptor on requests, 401 redirect on responses
```

## Color Scheme (Dark)
Background: gray-900/950. Cards: gray-800 + gray-700 border. Primary: purple-600.
Tutor panel: blue accents. Verified: green. Rejected: red. Provisional: orange.

## State Management
Zustand store: myAgentId, selectedAgent, activeSection, connected agents cache.

## Rules
- NEVER use `any` type. ALWAYS handle loading + error + empty states.
- Components under 200 lines. Extract sub-components.
- Responsive: works on tablet and desktop.
