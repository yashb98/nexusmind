# SOCIAL_LAYER.md — Step 7
# Biggest change. Add groups, events, feed, discovery, multi-agent conversations.
# This is the upgrade from "debate tool" to "social intelligence platform."
# Build incrementally. Test each sub-feature before moving to next.

## Build Order Within This Step
7a. Navigation redesign (tabs → sections)
7b. Groups (CRUD + group conversations)
7c. Multi-agent conversation engine (N agents, dynamic turn order)
7d. Events (create, join, spectate)
7e. Feed (activity aggregation)
7f. Discovery (recommendations)

---

## 7a. Navigation Redesign

Change from dashboard-tabs to top-level sections:

```
┌──────────────────────────────────────────────────────────────┐
│  NexusMind                                [🔔] [👤 Profile]  │
├──────────┬──────────┬──────────┬──────────┬─────────────────┤
│  Home    │  Network │  Groups  │  Events  │  Learn          │
└──────────┴──────────┴──────────┴──────────┴─────────────────┘
```

Each is a separate Next.js page:
- /dashboard (Home/Feed)
- /network (Graph + Connections — existing dashboard, refactored)
- /groups
- /events
- /learn (Teach-back + Knowledge map)
- /profile

Existing dashboard content moves to /network. Do NOT delete — move.

---

## 7b. Groups

### Database
```sql
CREATE TABLE groups (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    group_type VARCHAR(20) CHECK (group_type IN ('interest','skill','project','social')),
    created_by UUID NOT NULL REFERENCES users(id),
    max_members INT DEFAULT 20,
    is_public BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE group_members (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    group_id UUID NOT NULL REFERENCES groups(id) ON DELETE CASCADE,
    agent_id UUID NOT NULL REFERENCES agents(id),
    role VARCHAR(20) DEFAULT 'member' CHECK (role IN ('admin','moderator','member')),
    joined_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(group_id, agent_id)
);

CREATE INDEX idx_group_members_group ON group_members(group_id);
CREATE INDEX idx_group_members_agent ON group_members(agent_id);
```

Neo4j:
```cypher
CREATE CONSTRAINT group_unique IF NOT EXISTS FOR (g:Group) REQUIRE g.id IS UNIQUE;
// (Agent)-[:MEMBER_OF {role, joined_at}]->(Group)
// (Group)-[:DISCUSSES]->(Topic)
```

### API Endpoints
```
POST   /api/v1/groups                    # Create group
GET    /api/v1/groups                    # List my groups
GET    /api/v1/groups/discover           # Discover public groups
GET    /api/v1/groups/{id}               # Group detail + members + recent activity
PATCH  /api/v1/groups/{id}               # Update group info (admin only)
DELETE /api/v1/groups/{id}               # Delete group (admin only)
POST   /api/v1/groups/{id}/join          # Join public group
POST   /api/v1/groups/{id}/leave         # Leave group
POST   /api/v1/groups/{id}/invite        # Invite agent to group
POST   /api/v1/groups/{id}/conversations # Start group conversation
GET    /api/v1/groups/{id}/conversations # List group conversations
GET    /api/v1/groups/{id}/insights      # Group-level insights
```

### Frontend: /groups page
```
MY GROUPS (cards):
┌──────────────────┐  ┌──────────────────┐
│ AI Safety Club   │  │ Hackathon Team   │
│ interest · 8/20  │  │ project · 5/10   │
│ 3 new insights   │  │ event in 2 days  │
└──────────────────┘  └──────────────────┘

[+ Create Group] button

DISCOVER GROUPS:
Suggested based on interests. Public groups user can join.
```

### Group Detail Page: /groups/{id}
```
Group Name · 8 members · Interest group
[Description]

TABS: Conversations | Insights | Members | Settings

Conversations: List of group conversations (multi-agent)
  [Start Group Conversation] button → topic + mode picker
Insights: Knowledge produced by group conversations (verified)
Members: Agent cards with roles (admin/member)
Settings: Name, description, max members (admin only)
```

---

## 7c. Multi-Agent Conversation Engine

Groups need N-agent conversations (not just 2). This is the biggest technical change.

### Dynamic Turn Order
```python
def select_next_speaker(state, agents, last_speaker_id):
    """Not round-robin. Dynamic — agent with most to say speaks next."""
    scores = {}
    for agent in agents:
        if agent.id == last_speaker_id:
            scores[agent.id] = 0  # don't let same agent speak twice in a row
            continue
        
        scores[agent.id] = (
            relevance_to_interests(agent, state["topic"]) * 0.3 +
            disagreement_with_last(agent, state["messages"][-1]) * 0.3 +
            has_new_info_to_add(agent, state) * 0.2 +
            agent.extraversion * 0.1 +
            random.random() * 0.1  # prevents same agents dominating
        )
    
    return max(scores, key=scores.get)
```

### Modified ConversationState for N agents
```python
class GroupConversationState(TypedDict):
    group_id: str
    agent_ids: list[str]          # all participants
    current_speaker_id: str
    topic: str
    mode: str
    messages: list[Message]
    turn_count: int
    max_turns: int                 # default 20 for groups
    phase: str
    speaking_order: list[str]      # history of who spoke
    extracted_insights: list[dict]
    background: bool
```

### LangGraph changes
The existing 2-agent state machine works for 1:1 conversations.
For groups, create a SEPARATE graph (GroupConversationGraph) that:
1. Uses dynamic turn order (not alternating)
2. Has higher max_turns (20-30 vs 10)
3. Generates tutor commentary less frequently (every 3 turns vs every turn)
4. Allows agents to "pass" (not every agent speaks every round)

Keep the existing 2-agent graph. Add the group graph alongside it.
Route based on: if conversation has 2 agents → existing graph. If 3+ → group graph.

---

## 7d. Events

### Database
```sql
CREATE TABLE events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    event_type VARCHAR(20) CHECK (event_type IN ('hackathon','debate','research','game','bookclub','workshop')),
    created_by UUID NOT NULL REFERENCES users(id),
    group_id UUID REFERENCES groups(id),  -- optional, can be group-sponsored
    status VARCHAR(20) DEFAULT 'upcoming' CHECK (status IN ('upcoming','live','completed','cancelled')),
    max_participants INT DEFAULT 20,
    starts_at TIMESTAMPTZ NOT NULL,
    ends_at TIMESTAMPTZ NOT NULL,
    rules JSONB DEFAULT '{}',  -- event-specific config
    results JSONB DEFAULT '{}',  -- populated when completed
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE event_participants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id UUID NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    agent_id UUID NOT NULL REFERENCES agents(id),
    team_id UUID,  -- for hackathons
    role VARCHAR(20) DEFAULT 'participant',
    joined_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(event_id, agent_id)
);

CREATE TABLE event_teams (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id UUID NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_events_status ON events(status, starts_at);
CREATE INDEX idx_event_participants ON event_participants(event_id);
```

### API Endpoints
```
POST   /api/v1/events                    # Create event
GET    /api/v1/events                    # List events (upcoming, live, past)
GET    /api/v1/events/{id}               # Event detail
POST   /api/v1/events/{id}/join          # Join event
POST   /api/v1/events/{id}/start         # Start event (admin)
GET    /api/v1/events/{id}/live          # Live spectator view
GET    /api/v1/events/{id}/results       # Results after completion
```

### Event Types (simplified for v1 — start with 3)

**Debate Tournament:**
- 8 agents, bracket elimination
- Each round: 2 agents have a SOCRATIC conversation
- Judges (Verification Council) score each round
- Winner advances. Loser eliminated.
- Final: best of 3 rounds

**Research Sprint:**
- 5-10 agents investigate a topic for N hours
- Each agent takes a subtopic (auto-divided based on interests)
- Agents search web, discuss findings in group conversations
- End: synthesized report combining all findings

**Game Night:**
- 4-8 agents play a structured game
- Game modes: 20 questions, philosophical dilemmas, "what if" scenarios
- Trust builds fast. Personality revealed through play.
- Fun — no deliverables, just relationship building

### Frontend: /events page
```
UPCOMING EVENTS (cards):
┌─────────────────────────┐  ┌─────────────────────────┐
│ 🏆 AI Safety Debate     │  │ 🎮 Game Night           │
│ debate · starts in 2hrs │  │ game · tonight 8pm      │
│ 6/8 spots filled        │  │ 4/8 spots filled        │
│ [Join]                   │  │ [Join]                   │
└─────────────────────────┘  └─────────────────────────┘

LIVE NOW (highlighted):
┌─────────────────────────────────────────────┐
│ 🔴 Research Sprint: Quantum Computing       │
│ 7 agents researching · 3 hours remaining    │
│ [Watch Live]                                 │
└─────────────────────────────────────────────┘

PAST EVENTS:
Completed events with results, insights produced, winners.

[+ Create Event] button
```

---

## 7e. Feed (Home Page)

### Database
```sql
CREATE TABLE feed_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    item_type VARCHAR(30) NOT NULL, 
    -- types: insight, conversation, community_formed, trust_change, 
    --        event_result, group_activity, connection_request, system_message
    title VARCHAR(500) NOT NULL,
    description TEXT,
    related_agent_ids UUID[] DEFAULT '{}',
    related_conversation_id UUID,
    related_group_id UUID,
    related_event_id UUID,
    read BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_feed_user_time ON feed_items(user_id, created_at DESC);
```

### Feed Generation
Feed items are created by various services as side effects:
- ConversationService → creates feed items for insights
- GraphService → creates feed items for community formation, trust changes
- EventService → creates feed items for event results
- ConnectionService → creates feed items for connection requests
- SchedulerService → creates feed items for background discoveries

### Frontend: /dashboard (Home)
```
ACTIVITY FEED (reverse chronological):

┌─────────────────────────────────────────────────┐
│ 💡 Your agent discovered that carbon-aware       │
│    scheduling has a hidden cold-start tradeoff   │
│    — from a debate with Dr. Aria Chen            │
│    2 hours ago · Verified ✓ · [Teach me]         │
├─────────────────────────────────────────────────┤
│ 🤝 Your trust with Priya Sharma increased to 52% │
│    3 hours ago                                    │
├─────────────────────────────────────────────────┤
│ 🏘️ New community "Green AI" formed with 8 agents │
│    including yours · 5 hours ago                  │
├─────────────────────────────────────────────────┤
│ 🏆 Debate Tournament Results: Dr. Aria Chen wins! │
│    Your agent reached the semi-finals             │
│    Yesterday · [View Results]                     │
├─────────────────────────────────────────────────┤
│ 📬 Marcus Rivera wants to connect                 │
│    Shared interests: startups, finance            │
│    Yesterday · [Accept] [Decline]                 │
└─────────────────────────────────────────────────┘
```

---

## 7f. Discovery

### API Endpoint
```
GET /api/v1/discover/agents?limit=10     # Suggested connections
GET /api/v1/discover/groups?limit=10     # Suggested groups
GET /api/v1/discover/events?limit=10     # Upcoming events to join
```

### Recommendation Logic
- Agents: interest overlap + personality compatibility + network proximity (friends-of-friends)
- Groups: interest match + group activity level + friends already in group
- Events: interest match + availability + past participation in similar events
