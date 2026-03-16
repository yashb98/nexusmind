# MOCK_AGENTS_CONNECTIONS.md — Step 8
# 5 rich mock agents + social connection flow.
# Mock agents auto-connect to every new user.

## The 5 Mock Agents

```python
MOCK_AGENTS = [
    {
        "display_name": "Dr. Aria Chen",
        "tagline": "The Scientist",
        "openness": 0.92, "conscientiousness": 0.85,
        "extraversion": 0.45, "agreeableness": 0.60, "neuroticism": 0.30,
        "interests": ["Artificial Intelligence", "Neuroscience", "Ethics", "Computer Science", "Psychology"],
        "communication_style": "analytical",
        "lora_archetype": "investigator",
        "default_trust_for_strangers": 0.4,
        "domain_modifiers": {
            "Artificial Intelligence": {"conscientiousness": 0.1, "agreeableness": -0.1},
            "Ethics": {"agreeableness": 0.15, "openness": 0.05},
        },
    },
    {
        "display_name": "Marcus Rivera",
        "tagline": "The Entrepreneur",
        "openness": 0.65, "conscientiousness": 0.70,
        "extraversion": 0.88, "agreeableness": 0.50, "neuroticism": 0.35,
        "interests": ["Finance", "Economics", "Artificial Intelligence", "Political Science", "Sociology"],
        "communication_style": "driver",
        "lora_archetype": "catalyst",
        "default_trust_for_strangers": 0.3,
        "domain_modifiers": {
            "Finance": {"neuroticism": 0.1, "conscientiousness": 0.1},
            "Political Science": {"agreeableness": -0.15},
        },
    },
    {
        "display_name": "Priya Sharma",
        "tagline": "The Teacher",
        "openness": 0.80, "conscientiousness": 0.65,
        "extraversion": 0.72, "agreeableness": 0.90, "neuroticism": 0.25,
        "interests": ["Psychology", "Philosophy", "Cognitive Science", "Ethics", "Linguistics"],
        "communication_style": "amiable",
        "lora_archetype": "diplomat",
        "default_trust_for_strangers": 0.5,
        "domain_modifiers": {
            "Philosophy": {"openness": 0.1, "agreeableness": 0.05},
            "Psychology": {"conscientiousness": 0.1},
        },
    },
    {
        "display_name": "James Okafor",
        "tagline": "The Skeptic",
        "openness": 0.60, "conscientiousness": 0.90,
        "extraversion": 0.55, "agreeableness": 0.30, "neuroticism": 0.45,
        "interests": ["Economics", "Mathematics", "Political Science", "History", "Environmental Science"],
        "communication_style": "analytical",
        "lora_archetype": "strategist",
        "default_trust_for_strangers": 0.2,
        "domain_modifiers": {
            "Economics": {"agreeableness": -0.15, "conscientiousness": 0.1},
            "Mathematics": {"openness": -0.1, "conscientiousness": 0.15},
        },
    },
    {
        "display_name": "Luna Petrov",
        "tagline": "The Creative",
        "openness": 0.95, "conscientiousness": 0.40,
        "extraversion": 0.75, "agreeableness": 0.70, "neuroticism": 0.50,
        "interests": ["Environmental Science", "Music Theory", "Literature", "Astronomy", "Philosophy"],
        "communication_style": "expressive",
        "lora_archetype": "innovator",
        "default_trust_for_strangers": 0.4,
        "domain_modifiers": {
            "Environmental Science": {"extraversion": 0.1, "agreeableness": 0.1},
            "Literature": {"openness": 0.05, "neuroticism": 0.05},
        },
    },
]
```

## Database Changes
```sql
ALTER TABLE agents ADD COLUMN is_mock BOOLEAN DEFAULT false;
ALTER TABLE agents ADD COLUMN tagline VARCHAR(255);
```

## Seed Script
Update scripts/seed_demo.py to create these 5 mock agents.
Mock agents belong to a special system user/tenant but are visible to all.

## Auto-Connect on Signup
In agent creation service, after creating user's agent:
```python
if not data.is_mock:
    mock_agents = await self.db.fetch("SELECT * FROM agents WHERE is_mock = true")
    for mock in mock_agents:
        initial_trust = mock["default_trust_for_strangers"]
        await self.graph.upsert_relationship(
            new_agent_id, mock["id"],
            {"strength": 0.3, "trust": initial_trust,
             "topics_shared": find_shared_interests(new_agent, mock),
             "conversation_count": 0, "trust_history": [initial_trust]}
        )
```

## Connection Request System

### New File: src/services/connection_service.py
```python
class ConnectionService:
    async def generate_invite_link(self, agent_id) -> str:
        """Generate shareable invite URL."""
        token = secrets.token_urlsafe(32)
        await self.db.execute(
            "INSERT INTO invite_links (agent_id, token, expires_at) VALUES ($1, $2, $3)",
            agent_id, token, datetime.utcnow() + timedelta(days=7)
        )
        return f"{BASE_URL}/invite/{token}"
    
    async def send_request(self, from_agent_id, to_agent_id, message=None):
        """Send connection request."""
        await self.db.execute(
            "INSERT INTO connection_requests (from_agent_id, to_agent_id, message) VALUES ($1,$2,$3)",
            from_agent_id, to_agent_id, message
        )
        # Create feed item for target user
        await self.feed.create_item(to_user_id, "connection_request", ...)
    
    async def respond(self, request_id, accept: bool):
        """Accept or reject. If accept, create KNOWS edge with trust=0.2."""
        request = await self.db.fetch_one("SELECT * FROM connection_requests WHERE id=$1", request_id)
        status = "accepted" if accept else "rejected"
        await self.db.execute(
            "UPDATE connection_requests SET status=$1, responded_at=NOW() WHERE id=$2",
            status, request_id
        )
        if accept:
            await self.graph.upsert_relationship(
                request["from_agent_id"], request["to_agent_id"],
                {"strength": 0.2, "trust": 0.2, "topics_shared": [],
                 "conversation_count": 0, "trust_history": [0.2]}
            )
```

### New Table
```sql
CREATE TABLE invite_links (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id UUID NOT NULL REFERENCES agents(id),
    token VARCHAR(255) UNIQUE NOT NULL,
    used_by UUID REFERENCES users(id),
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### New Routes: src/routes/connections.py
```
POST   /api/v1/connections/invite              # Generate invite link
POST   /api/v1/connections/request             # Send connection request
GET    /api/v1/connections/requests            # List pending incoming
PATCH  /api/v1/connections/requests/{id}       # Accept/reject
GET    /api/v1/connections                     # List all my connections
```

## Frontend
- Network page: [Invite Friend] button generates link, shows copy-to-clipboard
- Feed: connection requests appear as actionable cards with [Accept] [Decline]
- Network page: "Find People" section showing recommended connections
