"""Integration tests for verification council pipeline."""

import uuid
from unittest.mock import AsyncMock, patch

from src.services import verification


class TestVerificationPipeline:
    async def test_high_score_accepted(self) -> None:
        """Skeptic score >= 0.8 → ACCEPTED (fast path)."""
        with (
            patch("src.services.verification.neo4j_client") as mock_neo4j,
            patch("src.services.verification.llm_service") as mock_llm,
            patch("src.services.verification.postgres") as mock_pg,
        ):
            mock_neo4j.execute_read = AsyncMock(return_value=[])
            mock_llm.generate = AsyncMock(
                return_value='{"score": 0.9, "reasoning": "Very reliable"}'
            )
            mock_pg.execute = AsyncMock()

            result = await verification.verify(
                insight_content="AI improves healthcare",
                source_description="peer-reviewed study",
                conversation_id=str(uuid.uuid4()),
                tenant_id=str(uuid.uuid4()),
            )
            assert result["decision"] == "accepted"
            assert result["skeptic_score"] == 0.9

    async def test_low_score_rejected(self) -> None:
        """Skeptic score < 0.3 → REJECTED (fast path)."""
        with (
            patch("src.services.verification.neo4j_client") as mock_neo4j,
            patch("src.services.verification.llm_service") as mock_llm,
            patch("src.services.verification.postgres") as mock_pg,
        ):
            mock_neo4j.execute_read = AsyncMock(return_value=[])
            mock_llm.generate = AsyncMock(return_value='{"score": 0.1, "reasoning": "No evidence"}')
            mock_pg.execute = AsyncMock()

            result = await verification.verify(
                insight_content="Unverifiable claim",
                source_description="unknown",
                conversation_id=str(uuid.uuid4()),
                tenant_id=str(uuid.uuid4()),
            )
            assert result["decision"] == "rejected"

    async def test_mid_score_uses_judge(self) -> None:
        """Skeptic score 0.3-0.8 → runs Judge LLM."""
        with (
            patch("src.services.verification.neo4j_client") as mock_neo4j,
            patch("src.services.verification.llm_service") as mock_llm,
            patch("src.services.verification.postgres") as mock_pg,
        ):
            mock_neo4j.execute_read = AsyncMock(return_value=[])
            # Skeptic returns 0.6, connector returns 0.5, judge decides
            mock_llm.generate = AsyncMock(
                side_effect=[
                    '{"score": 0.6, "reasoning": "Moderate confidence"}',
                    '{"score": 0.5, "connections": ["related to X"]}',
                    '{"decision": "provisional", "reasoning": "Needs more"}',
                ]
            )
            mock_pg.execute = AsyncMock()

            result = await verification.verify(
                insight_content="Moderate claim",
                source_description="blog post",
                conversation_id=str(uuid.uuid4()),
                tenant_id=str(uuid.uuid4()),
            )
            assert result["decision"] == "provisional"

    async def test_disabled_verification_auto_accepts(self) -> None:
        """When verification is disabled, auto-accept."""
        with patch("src.services.verification.settings") as mock_settings:
            mock_settings.verification.enabled = False
            result = await verification.verify("test", "test", None, str(uuid.uuid4()))
            assert result["decision"] == "accepted"
