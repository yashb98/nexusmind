"""Integration tests for auth flow: register → login → protected route.

Run with: uv run pytest tests/integration/ -x
"""

import uuid
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from src.main import app


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


class TestHealthEndpoint:
    async def test_health(self, client: AsyncClient) -> None:
        resp = await client.get("/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}


class TestAuthFlow:
    async def test_register(self, client: AsyncClient) -> None:
        with patch("src.services.auth_service.postgres") as mock_pg:
            mock_pg.fetchrow = AsyncMock(return_value=None)
            mock_pg.execute = AsyncMock()

            resp = await client.post(
                "/api/v1/auth/register",
                json={
                    "email": "test@example.com",
                    "display_name": "Test User",
                    "password": "securepassword123",
                },
            )
            assert resp.status_code == 201
            data = resp.json()
            assert "access_token" in data
            assert data["token_type"] == "bearer"

    async def test_register_duplicate(self, client: AsyncClient) -> None:
        with patch("src.services.auth_service.postgres") as mock_pg:
            mock_pg.fetchrow = AsyncMock(return_value={"id": "existing"})

            resp = await client.post(
                "/api/v1/auth/register",
                json={
                    "email": "test@example.com",
                    "display_name": "Test User",
                    "password": "securepassword123",
                },
            )
            assert resp.status_code == 409

    async def test_login_success(self, client: AsyncClient) -> None:
        from src.utils.auth import hash_password

        user_id = uuid.uuid4()
        tenant_id = uuid.uuid4()
        hashed = hash_password("securepassword123")

        with patch("src.services.auth_service.postgres") as mock_pg:
            mock_pg.fetchrow = AsyncMock(
                return_value={"id": user_id, "tenant_id": tenant_id, "hashed_password": hashed}
            )

            resp = await client.post(
                "/api/v1/auth/login",
                json={"email": "test@example.com", "password": "securepassword123"},
            )
            assert resp.status_code == 200
            assert "access_token" in resp.json()

    async def test_login_wrong_password(self, client: AsyncClient) -> None:
        from src.utils.auth import hash_password

        with patch("src.services.auth_service.postgres") as mock_pg:
            mock_pg.fetchrow = AsyncMock(
                return_value={
                    "id": uuid.uuid4(),
                    "tenant_id": uuid.uuid4(),
                    "hashed_password": hash_password("correct_password"),
                }
            )

            resp = await client.post(
                "/api/v1/auth/login",
                json={"email": "test@example.com", "password": "wrong_password"},
            )
            assert resp.status_code == 401

    async def test_protected_route_without_token(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/auth/me")
        assert resp.status_code in (401, 403)

    async def test_protected_route_with_token(self, client: AsyncClient) -> None:
        from src.utils.auth import create_access_token

        user_id = str(uuid.uuid4())
        tenant_id = str(uuid.uuid4())
        token = create_access_token(user_id, tenant_id)

        with patch("src.services.auth_service.postgres") as mock_pg:
            mock_pg.fetchrow = AsyncMock(
                return_value={
                    "id": uuid.UUID(user_id),
                    "tenant_id": uuid.UUID(tenant_id),
                    "email": "test@example.com",
                    "display_name": "Test User",
                    "role": "member",
                }
            )

            resp = await client.get(
                "/api/v1/auth/me",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["id"] == user_id
            assert data["email"] == "test@example.com"
