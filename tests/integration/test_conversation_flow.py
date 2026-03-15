"""Integration tests for conversation flow — full Socratic debate."""

import uuid
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from src.main import app
from src.utils.auth import create_access_token


@pytest.fixture
async def client():
    with (
        patch("src.db.postgres.connect", new_callable=AsyncMock),
        patch("src.db.postgres.disconnect", new_callable=AsyncMock),
        patch("src.db.neo4j_client.connect", new_callable=AsyncMock),
        patch("src.db.neo4j_client.disconnect", new_callable=AsyncMock),
        patch("src.db.qdrant_client.connect", new_callable=AsyncMock),
        patch("src.db.qdrant_client.disconnect", new_callable=AsyncMock),
        patch("src.db.redis_client.connect", new_callable=AsyncMock),
        patch("src.db.redis_client.disconnect", new_callable=AsyncMock),
    ):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac


@pytest.fixture
def auth_headers() -> dict:
    token = create_access_token(str(uuid.uuid4()), str(uuid.uuid4()))
    return {"Authorization": f"Bearer {token}"}


class TestConversationEndpoints:
    async def test_trigger_debate(self, client: AsyncClient, auth_headers: dict) -> None:
        """Test full conversation flow with mocked services."""
        agent_a = str(uuid.uuid4())
        agent_b = str(uuid.uuid4())

        mock_agent_row = {
            "id": uuid.uuid4(),
            "display_name": "TestAgent",
            "openness": 0.7,
            "conscientiousness": 0.6,
            "extraversion": 0.5,
            "agreeableness": 0.4,
            "neuroticism": 0.3,
            "interests": ["AI"],
            "communication_style": "analytical",
        }

        with (
            patch("src.services.conversation.permission_service") as mock_perm,
            patch("src.services.conversation.memory_service") as mock_mem,
            patch("src.services.conversation.graph_service") as mock_graph,
            patch("src.services.conversation.llm_service") as mock_llm,
            patch("src.services.conversation.postgres") as mock_pg,
            patch("src.services.conversation.neo4j_client") as mock_neo4j,
            patch("src.services.conversation.embed") as mock_embed,
            patch("src.services.conversation.knowledge_service") as mock_know,
        ):
            mock_perm.check_access = AsyncMock(return_value=True)
            mock_mem.retrieve_memories = AsyncMock(return_value=[])
            mock_graph.get_relationship = AsyncMock(return_value=None)
            mock_graph.upsert_relationship = AsyncMock()
            mock_llm.generate = AsyncMock(return_value="This is an interesting perspective.")
            mock_pg.fetchrow = AsyncMock(return_value=mock_agent_row)
            mock_neo4j.execute_write = AsyncMock()
            mock_embed.return_value = [0.0] * 768
            mock_know.extract_knowledge = AsyncMock(return_value=([], [], []))

            resp = await client.post(
                "/api/v1/conversations",
                json={
                    "agent_a_id": agent_a,
                    "agent_b_id": agent_b,
                    "topic": "AI Safety",
                },
                headers=auth_headers,
            )

            assert resp.status_code == 201
            data = resp.json()
            assert data["topic"] == "AI Safety"
            assert data["turn_count"] == 10
            assert len(data["messages"]) == 10
            assert data["messages"][0]["phase"] == "OPEN"
            assert data["messages"][-1]["phase"] == "EXTRACT"

    async def test_requires_auth(self, client: AsyncClient) -> None:
        resp = await client.post(
            "/api/v1/conversations",
            json={
                "agent_a_id": str(uuid.uuid4()),
                "agent_b_id": str(uuid.uuid4()),
                "topic": "test",
            },
        )
        assert resp.status_code in (401, 403)
