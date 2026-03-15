"""Seed demo data: 1 tenant, 1 user, 10 diverse agents, 5 KNOWS edges, 3 Topics."""

import asyncio
import uuid

from src.db import neo4j_client, postgres
from src.utils.auth import hash_password

TENANT_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")
USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000002")

DEMO_AGENTS = [
    {
        "display_name": "Atlas",
        "openness": 0.85,
        "conscientiousness": 0.7,
        "extraversion": 0.3,
        "agreeableness": 0.4,
        "neuroticism": 0.35,
        "interests": ["AI", "philosophy", "sustainability"],
        "communication_style": "analytical",
        "lora_archetype": "The Investigator",
    },
    {
        "display_name": "Nova",
        "openness": 0.9,
        "conscientiousness": 0.4,
        "extraversion": 0.65,
        "agreeableness": 0.5,
        "neuroticism": 0.55,
        "interests": ["AI", "creativity", "music"],
        "communication_style": "expressive",
        "lora_archetype": "The Innovator",
    },
    {
        "display_name": "Sage",
        "openness": 0.6,
        "conscientiousness": 0.5,
        "extraversion": 0.6,
        "agreeableness": 0.9,
        "neuroticism": 0.25,
        "interests": ["education", "psychology", "sustainability"],
        "communication_style": "amiable",
        "lora_archetype": "The Diplomat",
    },
    {
        "display_name": "Rex",
        "openness": 0.5,
        "conscientiousness": 0.85,
        "extraversion": 0.8,
        "agreeableness": 0.3,
        "neuroticism": 0.2,
        "interests": ["finance", "strategy", "AI"],
        "communication_style": "driver",
        "lora_archetype": "The Commander",
    },
    {
        "display_name": "Ivy",
        "openness": 0.3,
        "conscientiousness": 0.9,
        "extraversion": 0.4,
        "agreeableness": 0.7,
        "neuroticism": 0.5,
        "interests": ["healthcare", "education", "ethics"],
        "communication_style": "analytical",
        "lora_archetype": "The Guardian",
    },
    {
        "display_name": "Blaze",
        "openness": 0.75,
        "conscientiousness": 0.3,
        "extraversion": 0.75,
        "agreeableness": 0.35,
        "neuroticism": 0.6,
        "interests": ["startups", "AI", "philosophy"],
        "communication_style": "expressive",
        "lora_archetype": "The Maverick",
    },
    {
        "display_name": "Luna",
        "openness": 0.8,
        "conscientiousness": 0.6,
        "extraversion": 0.45,
        "agreeableness": 0.65,
        "neuroticism": 0.4,
        "interests": ["sustainability", "biology", "art"],
        "communication_style": "amiable",
        "lora_archetype": "The Diplomat",
    },
    {
        "display_name": "Cipher",
        "openness": 0.7,
        "conscientiousness": 0.8,
        "extraversion": 0.35,
        "agreeableness": 0.45,
        "neuroticism": 0.3,
        "interests": ["cybersecurity", "AI", "mathematics"],
        "communication_style": "analytical",
        "lora_archetype": "The Investigator",
    },
    {
        "display_name": "Aria",
        "openness": 0.65,
        "conscientiousness": 0.55,
        "extraversion": 0.7,
        "agreeableness": 0.8,
        "neuroticism": 0.45,
        "interests": ["music", "psychology", "creativity"],
        "communication_style": "expressive",
        "lora_archetype": "The Innovator",
    },
    {
        "display_name": "Titan",
        "openness": 0.4,
        "conscientiousness": 0.9,
        "extraversion": 0.55,
        "agreeableness": 0.5,
        "neuroticism": 0.15,
        "interests": ["finance", "healthcare", "strategy"],
        "communication_style": "driver",
        "lora_archetype": "The Commander",
    },
]

MOCK_AGENTS = [
    {
        "display_name": "Dr. Aria Chen",
        "openness": 0.8,
        "conscientiousness": 0.7,
        "extraversion": 0.3,
        "agreeableness": 0.4,
        "neuroticism": 0.4,
        "interests": ["AI", "neuroscience", "philosophy"],
        "communication_style": "analytical",
        "lora_archetype": "The Investigator",
        "is_mock": True,
        "default_trust_for_strangers": 0.3,
    },
    {
        "display_name": "Marcus Rivera",
        "openness": 0.5,
        "conscientiousness": 0.85,
        "extraversion": 0.8,
        "agreeableness": 0.3,
        "neuroticism": 0.2,
        "interests": ["startups", "strategy", "leadership"],
        "communication_style": "driver",
        "lora_archetype": "The Commander",
        "is_mock": True,
        "default_trust_for_strangers": 0.15,
    },
    {
        "display_name": "Priya Sharma",
        "openness": 0.6,
        "conscientiousness": 0.5,
        "extraversion": 0.6,
        "agreeableness": 0.9,
        "neuroticism": 0.3,
        "interests": ["education", "psychology", "sustainability"],
        "communication_style": "amiable",
        "lora_archetype": "The Diplomat",
        "is_mock": True,
        "default_trust_for_strangers": 0.4,
    },
    {
        "display_name": "James Okafor",
        "openness": 0.7,
        "conscientiousness": 0.8,
        "extraversion": 0.35,
        "agreeableness": 0.45,
        "neuroticism": 0.3,
        "interests": ["finance", "mathematics", "AI"],
        "communication_style": "analytical",
        "lora_archetype": "The Investigator",
        "is_mock": True,
        "default_trust_for_strangers": 0.2,
    },
    {
        "display_name": "Luna Petrov",
        "openness": 0.9,
        "conscientiousness": 0.4,
        "extraversion": 0.65,
        "agreeableness": 0.5,
        "neuroticism": 0.55,
        "interests": ["art", "creativity", "music"],
        "communication_style": "expressive",
        "lora_archetype": "The Innovator",
        "is_mock": True,
        "default_trust_for_strangers": 0.35,
    },
]

KNOWS_EDGES = [
    (0, 1, 0.6, ["AI"]),  # Atlas - Nova
    (0, 2, 0.4, ["sustainability"]),  # Atlas - Sage
    (3, 4, 0.5, ["healthcare"]),  # Rex - Ivy
    (5, 6, 0.3, ["philosophy"]),  # Blaze - Luna
    (7, 8, 0.7, ["AI"]),  # Cipher - Aria
]

TOPICS = ["Artificial Intelligence", "Sustainability", "Human Psychology"]


async def seed() -> None:
    """Run the seed script."""
    await postgres.connect()
    await neo4j_client.connect()

    # Create tenant
    await postgres.execute(
        "INSERT INTO tenants (id, name) VALUES ($1, $2) ON CONFLICT DO NOTHING",
        TENANT_ID,
        "Demo Workspace",
    )

    # Create user
    await postgres.execute(
        """INSERT INTO users (id, tenant_id, email, display_name, hashed_password)
           VALUES ($1, $2, $3, $4, $5) ON CONFLICT DO NOTHING""",
        USER_ID,
        TENANT_ID,
        "demo@nexusmind.ai",
        "Demo User",
        hash_password("demo_password_123"),
    )

    # Create agents
    agent_ids = []
    for agent_data in DEMO_AGENTS:
        agent_id = uuid.uuid4()
        agent_ids.append(agent_id)

        await postgres.execute(
            """INSERT INTO agents
               (id, user_id, tenant_id, display_name,
                openness, conscientiousness, extraversion, agreeableness, neuroticism,
                interests, communication_style, lora_archetype)
               VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12)""",
            agent_id,
            USER_ID,
            TENANT_ID,
            agent_data["display_name"],
            agent_data["openness"],
            agent_data["conscientiousness"],
            agent_data["extraversion"],
            agent_data["agreeableness"],
            agent_data["neuroticism"],
            agent_data["interests"],
            agent_data["communication_style"],
            agent_data["lora_archetype"],
        )

        # Sync to Neo4j
        await neo4j_client.execute_write(
            """MERGE (a:Agent {id: $id})
               SET a.tenant_id = $tid,
                   a.display_name = $name,
                   a.interests = $interests,
                   a.openness = $openness,
                   a.extraversion = $extraversion""",
            id=str(agent_id),
            tid=str(TENANT_ID),
            name=agent_data["display_name"],
            interests=agent_data["interests"],
            openness=agent_data["openness"],
            extraversion=agent_data["extraversion"],
        )

        print(f"  Created agent: {agent_data['display_name']} ({agent_id})")

    # Create mock agents
    mock_agent_ids = []
    for mock_data in MOCK_AGENTS:
        mock_id = uuid.uuid4()
        mock_agent_ids.append(mock_id)

        await postgres.execute(
            """INSERT INTO agents
               (id, user_id, tenant_id, display_name,
                openness, conscientiousness, extraversion, agreeableness, neuroticism,
                interests, communication_style, lora_archetype,
                is_mock, default_trust_for_strangers)
               VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14)""",
            mock_id,
            USER_ID,
            TENANT_ID,
            mock_data["display_name"],
            mock_data["openness"],
            mock_data["conscientiousness"],
            mock_data["extraversion"],
            mock_data["agreeableness"],
            mock_data["neuroticism"],
            mock_data["interests"],
            mock_data["communication_style"],
            mock_data["lora_archetype"],
            mock_data["is_mock"],
            mock_data["default_trust_for_strangers"],
        )

        # Sync to Neo4j
        await neo4j_client.execute_write(
            """MERGE (a:Agent {id: $id})
               SET a.tenant_id = $tid,
                   a.display_name = $name,
                   a.interests = $interests,
                   a.openness = $openness,
                   a.extraversion = $extraversion,
                   a.is_mock = true""",
            id=str(mock_id),
            tid=str(TENANT_ID),
            name=mock_data["display_name"],
            interests=mock_data["interests"],
            openness=mock_data["openness"],
            extraversion=mock_data["extraversion"],
        )

        # Auto-connect mock agent to all existing (non-mock) demo agents
        for demo_agent_id in agent_ids:
            await neo4j_client.execute_write(
                """MATCH (a:Agent {id: $aid}), (b:Agent {id: $bid})
                   MERGE (a)-[r:KNOWS]-(b)
                   ON CREATE SET r.strength = 0.3,
                                 r.trust = $trust,
                                 r.topics_shared = [],
                                 r.conversation_count = 0,
                                 r.trust_history = [$trust]""",
                aid=str(demo_agent_id),
                bid=str(mock_id),
                trust=mock_data["default_trust_for_strangers"],
            )

        print(f"  Created mock agent: {mock_data['display_name']} ({mock_id})")

    # Create KNOWS edges
    for a_idx, b_idx, strength, topics in KNOWS_EDGES:
        a_id = str(agent_ids[a_idx])
        b_id = str(agent_ids[b_idx])
        await neo4j_client.execute_write(
            """MATCH (a:Agent {id: $a_id}), (b:Agent {id: $b_id})
               MERGE (a)-[r:KNOWS]->(b)
               SET r.strength = $strength,
                   r.trust = 0.5,
                   r.conversation_count = 0,
                   r.topics_shared = $topics,
                   r.last_interaction = datetime()""",
            a_id=a_id,
            b_id=b_id,
            strength=strength,
            topics=topics,
        )
        a_name = DEMO_AGENTS[a_idx]["display_name"]
        b_name = DEMO_AGENTS[b_idx]["display_name"]
        print(f"  Edge: {a_name} -> {b_name}")

    # Create Topic nodes
    for topic_name in TOPICS:
        await neo4j_client.execute_write(
            """MERGE (t:Topic {name: $name})
               SET t.id = $id, t.mention_count = 0, t.growth_rate = 0.0""",
            id=str(uuid.uuid4()),
            name=topic_name,
        )
        print(f"  Topic: {topic_name}")

    await postgres.disconnect()
    await neo4j_client.disconnect()

    print("\nSeed complete! 1 tenant, 1 user, 10 agents + 5 mock agents, 5 edges, 3 topics.")


if __name__ == "__main__":
    asyncio.run(seed())
