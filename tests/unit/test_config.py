"""Tests for configuration loading."""

import os

from src.config import (
    AppSettings,
    AuthSettings,
    DatabaseSettings,
    EvolutionSettings,
    FullFinetuneSettings,
    MicroFinetuneSettings,
    Neo4jSettings,
    QdrantSettings,
    RedisSettings,
    SchedulerSettings,
    Settings,
    VerificationSettings,
)


class TestDatabaseSettings:
    def test_defaults(self) -> None:
        s = DatabaseSettings()
        assert "nexusmind" in s.database_url

    def test_from_env(self, monkeypatch: object) -> None:
        os.environ["DATABASE_URL"] = "postgresql://test:test@db:5432/test"
        s = DatabaseSettings()
        assert s.database_url == "postgresql://test:test@db:5432/test"
        del os.environ["DATABASE_URL"]


class TestNeo4jSettings:
    def test_defaults(self) -> None:
        s = Neo4jSettings()
        assert s.uri == "bolt://localhost:7687"
        assert s.user == "neo4j"


class TestQdrantSettings:
    def test_defaults(self) -> None:
        s = QdrantSettings()
        assert s.url == "http://localhost:6333"


class TestRedisSettings:
    def test_defaults(self) -> None:
        s = RedisSettings()
        assert s.redis_url == "redis://localhost:6379"


class TestAuthSettings:
    def test_defaults(self) -> None:
        s = AuthSettings()
        assert s.algorithm == "HS256"
        assert s.expiry_hours == 24


class TestAppSettings:
    def test_defaults(self) -> None:
        s = AppSettings()
        assert s.env == "development"
        assert s.port == 8000


class TestSchedulerSettings:
    def test_defaults(self) -> None:
        s = SchedulerSettings()
        assert s.enabled is True
        assert s.cycle_seconds == 300
        assert s.max_hourly == 12
        assert s.explore_weight == 0.4


class TestMicroFinetuneSettings:
    def test_defaults(self) -> None:
        s = MicroFinetuneSettings()
        assert s.enabled is True
        assert s.rank == 4
        assert s.iters == 100


class TestFullFinetuneSettings:
    def test_defaults(self) -> None:
        s = FullFinetuneSettings()
        assert s.rank == 16
        assert s.iters == 500
        assert s.min_quality == 4.0
        assert s.personality_variance_threshold == 0.5


class TestVerificationSettings:
    def test_defaults(self) -> None:
        s = VerificationSettings()
        assert s.enabled is True
        assert s.skeptic_accept_threshold == 0.8
        assert s.skeptic_reject_threshold == 0.3


class TestEvolutionSettings:
    def test_defaults(self) -> None:
        s = EvolutionSettings()
        assert s.research_scout_cron == "0 0 * * 0"


class TestAggregatedSettings:
    def test_all_sections_load(self) -> None:
        s = Settings()
        assert s.database is not None
        assert s.neo4j is not None
        assert s.qdrant is not None
        assert s.redis is not None
        assert s.llm is not None
        assert s.search is not None
        assert s.avatar is not None
        assert s.langfuse is not None
        assert s.auth is not None
        assert s.app is not None
        assert s.cors is not None
        assert s.scheduler is not None
        assert s.micro_finetune is not None
        assert s.full_finetune is not None
        assert s.verification is not None
        assert s.evolution is not None
