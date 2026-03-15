"""Integration tests for graph service endpoints."""

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
    token = create_access_token(str(uuid.uuid4()), str(uuid.uuid4()))
    return {"Authorization": f"Bearer {token}"}


class TestGraphEndpoints:
    async def test_get_network(self, client: AsyncClient, auth_headers: dict) -> None:
        with patch("src.services.graph.neo4j_client") as mock_neo4j:
            mock_neo4j.execute_read = AsyncMock(return_value=[{"nodes": [], "edges": []}])
            resp = await client.get(
                f"/api/v1/graph/agents/{uuid.uuid4()}/network",
                headers=auth_headers,
            )
            assert resp.status_code == 200
            data = resp.json()
            assert "nodes" in data
            assert "edges" in data

    async def test_get_network_empty(self, client: AsyncClient, auth_headers: dict) -> None:
        with patch("src.services.graph.neo4j_client") as mock_neo4j:
            mock_neo4j.execute_read = AsyncMock(return_value=[])
            resp = await client.get(
                f"/api/v1/graph/agents/{uuid.uuid4()}/network",
                headers=auth_headers,
            )
            assert resp.status_code == 200
            assert resp.json() == {"nodes": [], "edges": []}

    async def test_get_recommendations(self, client: AsyncClient, auth_headers: dict) -> None:
        with patch("src.services.graph.neo4j_client") as mock_neo4j:
            mock_neo4j.execute_read = AsyncMock(
                return_value=[
                    {
                        "id": str(uuid.uuid4()),
                        "display_name": "Agent1",
                        "interests": ["AI"],
                        "shared": ["AI"],
                        "shared_count": 1,
                    }
                ]
            )
            resp = await client.get(
                f"/api/v1/graph/agents/{uuid.uuid4()}/recommendations",
                headers=auth_headers,
            )
            assert resp.status_code == 200
            data = resp.json()
            assert len(data) == 1

    async def test_requires_auth(self, client: AsyncClient) -> None:
        resp = await client.get(f"/api/v1/graph/agents/{uuid.uuid4()}/network")
        assert resp.status_code in (401, 403)
