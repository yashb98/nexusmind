"""Integration tests for agent CRUD endpoints."""

import uuid
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from src.main import app
from src.utils.auth import create_access_token


@pytest.fixture
async def client():
    """Create test client with mocked databases."""
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
    user_id = str(uuid.uuid4())
    tenant_id = str(uuid.uuid4())
    token = create_access_token(user_id, tenant_id)
    return {
        "Authorization": f"Bearer {token}",
        "_user_id": user_id,
        "_tenant_id": tenant_id,
    }


AGENT_DATA = {
    "display_name": "TestAgent",
    "openness": 0.8,
    "conscientiousness": 0.6,
    "extraversion": 0.4,
    "agreeableness": 0.5,
    "neuroticism": 0.3,
    "interests": ["AI", "testing"],
    "communication_style": "analytical",
}


class TestAgentCRUD:
    async def test_create_agent(self, client: AsyncClient, auth_headers: dict) -> None:
        agent_id = uuid.uuid4()
        user_id = uuid.UUID(auth_headers["_user_id"])
        tenant_id = uuid.UUID(auth_headers["_tenant_id"])

        mock_row = {
            "id": agent_id,
            "user_id": user_id,
            "tenant_id": tenant_id,
            "display_name": "TestAgent",
            "openness": 0.8,
            "conscientiousness": 0.6,
            "extraversion": 0.4,
            "agreeableness": 0.5,
            "neuroticism": 0.3,
            "interests": ["AI", "testing"],
            "communication_style": "analytical",
            "lora_archetype": None,
            "default_privacy_level": 2,
            "avatar_image_url": None,
            "default_trust_for_strangers": 0.2,
            "is_mock": False,
            "tagline": None,
            "domain_modifiers": {},
            "personality_confidence": 0.7,
            "questions_answered": 0,
            "tutor_voice": "en-GB-SoniaNeural",
            "tutor_avatar_url": None,
            "tutor_mode_preference": "active",
            "status": "active",
        }

        with (
            patch("src.services.agent_service.postgres") as mock_pg,
            patch("src.services.agent_service.neo4j_client") as mock_neo4j,
        ):
            mock_pg.fetchrow = AsyncMock(return_value=mock_row)
            mock_pg.fetch = AsyncMock(return_value=[])  # no mock agents to auto-connect
            mock_neo4j.execute_write = AsyncMock()

            headers = {"Authorization": auth_headers["Authorization"]}
            resp = await client.post("/api/v1/agents", json=AGENT_DATA, headers=headers)
            assert resp.status_code == 201
            data = resp.json()
            assert data["display_name"] == "TestAgent"
            assert data["openness"] == 0.8

    async def test_list_agents(self, client: AsyncClient, auth_headers: dict) -> None:
        with patch("src.services.agent_service.postgres") as mock_pg:
            mock_pg.fetch = AsyncMock(return_value=[])
            headers = {"Authorization": auth_headers["Authorization"]}
            resp = await client.get("/api/v1/agents", headers=headers)
            assert resp.status_code == 200
            assert resp.json() == []

    async def test_get_agent_not_found(self, client: AsyncClient, auth_headers: dict) -> None:
        with patch("src.services.agent_service.postgres") as mock_pg:
            mock_pg.fetchrow = AsyncMock(return_value=None)
            headers = {"Authorization": auth_headers["Authorization"]}
            resp = await client.get(f"/api/v1/agents/{uuid.uuid4()}", headers=headers)
            assert resp.status_code == 404

    async def test_create_requires_auth(self, client: AsyncClient) -> None:
        resp = await client.post("/api/v1/agents", json=AGENT_DATA)
        assert resp.status_code in (401, 403)
