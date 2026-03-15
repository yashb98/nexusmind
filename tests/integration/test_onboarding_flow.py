"""Integration tests for onboarding flow: scenarios → answers → personality result."""

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


class TestOnboardingFlow:
    async def test_get_scenarios(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/onboarding/scenarios")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 10
        for q in data:
            assert "scenario" in q
            assert len(q["options"]) == 4

    async def test_score_personality(self, client: AsyncClient) -> None:
        answers = [{"question_id": i, "option_index": 1} for i in range(1, 11)]
        resp = await client.post(
            "/api/v1/onboarding/personality",
            json={"answers": answers},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "scores" in data
        assert "archetype" in data
        assert "communication_style" in data
        assert "description" in data

        scores = data["scores"]
        traits = ["openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism"]
        for trait in traits:
            assert 0 <= scores[trait] <= 1

    async def test_too_few_answers_rejected(self, client: AsyncClient) -> None:
        answers = [{"question_id": 1, "option_index": 0}]
        resp = await client.post(
            "/api/v1/onboarding/personality",
            json={"answers": answers},
        )
        assert resp.status_code == 422

    async def test_invalid_option_index_rejected(self, client: AsyncClient) -> None:
        answers = [{"question_id": i, "option_index": 5} for i in range(1, 11)]
        resp = await client.post(
            "/api/v1/onboarding/personality",
            json={"answers": answers},
        )
        assert resp.status_code == 422

    async def test_different_answers_yield_different_results(self, client: AsyncClient) -> None:
        # All option 0
        answers_a = [{"question_id": i, "option_index": 0} for i in range(1, 11)]
        resp_a = await client.post("/api/v1/onboarding/personality", json={"answers": answers_a})
        # All option 2
        answers_b = [{"question_id": i, "option_index": 2} for i in range(1, 11)]
        resp_b = await client.post("/api/v1/onboarding/personality", json={"answers": answers_b})
        scores_a = resp_a.json()["scores"]
        scores_b = resp_b.json()["scores"]
        # At least some traits should differ
        diffs = [abs(scores_a[t] - scores_b[t]) for t in scores_a]
        assert max(diffs) > 0.1
