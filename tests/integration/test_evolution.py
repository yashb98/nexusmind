"""Integration tests for evolution service — proposals and metrics."""

from unittest.mock import AsyncMock, patch

from src.services import evolution


class TestEvolutionMetrics:
    async def test_collect_metrics(self) -> None:
        with patch("src.services.evolution.postgres") as mock_pg:
            mock_pg.fetchval = AsyncMock(side_effect=[5.0, 100, 0.75])
            metrics = await evolution._collect_system_metrics()
            assert metrics["avg_quality"] == 5.0
            assert metrics["total_conversations"] == 100
            assert metrics["acceptance_rate"] == 0.75


class TestIdentifyIssues:
    def test_flags_low_quality(self) -> None:
        issues = evolution._identify_issues({"avg_quality": 3.0, "acceptance_rate": 0.8})
        assert len(issues) == 1
        assert "quality" in issues[0]["title"].lower()

    def test_flags_low_acceptance(self) -> None:
        issues = evolution._identify_issues({"avg_quality": 6.0, "acceptance_rate": 0.3})
        assert len(issues) == 1
        assert "acceptance" in issues[0]["title"].lower()

    def test_no_issues_when_healthy(self) -> None:
        issues = evolution._identify_issues({"avg_quality": 7.0, "acceptance_rate": 0.8})
        assert len(issues) == 0

    def test_both_issues(self) -> None:
        issues = evolution._identify_issues({"avg_quality": 3.0, "acceptance_rate": 0.3})
        assert len(issues) == 2
