"""Application configuration via pydantic-settings."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    """PostgreSQL connection settings."""

    model_config = SettingsConfigDict(env_prefix="", env_file=".env", extra="ignore")

    database_url: str = Field(
        default="postgresql://nexusmind:nexusmind_dev@localhost:5432/nexusmind"
    )


class Neo4jSettings(BaseSettings):
    """Neo4j connection settings."""

    model_config = SettingsConfigDict(env_prefix="NEO4J_", env_file=".env", extra="ignore")

    uri: str = Field(default="bolt://localhost:7687")
    user: str = Field(default="neo4j")
    password: str = Field(default="nexusmind_dev")


class QdrantSettings(BaseSettings):
    """Qdrant connection settings."""

    model_config = SettingsConfigDict(env_prefix="QDRANT_", env_file=".env", extra="ignore")

    url: str = Field(default="http://localhost:6333")
    api_key: str = Field(default="")


class RedisSettings(BaseSettings):
    """Redis connection settings."""

    model_config = SettingsConfigDict(env_prefix="", env_file=".env", extra="ignore")

    redis_url: str = Field(default="redis://localhost:6379")


class LLMSettings(BaseSettings):
    """LLM provider settings."""

    model_config = SettingsConfigDict(env_prefix="", env_file=".env", extra="ignore")

    runpod_api_key: str = Field(default="")
    runpod_llm_endpoint: str = Field(default="")
    runpod_llm_model: str = Field(default="openai/Qwen/Qwen2.5-7B-Instruct")
    anthropic_api_key: str = Field(default="")
    litellm_fallback_model: str = Field(default="anthropic/claude-sonnet-4-20250514")
    mlx_model_path: str = Field(default="mlx-community/Qwen2.5-7B-Instruct-4bit")
    mlx_adapter_dir: str = Field(default="./adapters")
    embedding_model: str = Field(default="sentence-transformers/all-MiniLM-L6-v2")


class SearchSettings(BaseSettings):
    """Search engine settings."""

    model_config = SettingsConfigDict(env_prefix="", env_file=".env", extra="ignore")

    searxng_url: str = Field(default="http://localhost:8080")


class AvatarSettings(BaseSettings):
    """Avatar pipeline settings."""

    model_config = SettingsConfigDict(env_prefix="", env_file=".env", extra="ignore")

    runpod_avatar_endpoint: str = Field(default="")
    edge_tts_voice: str = Field(default="en-GB-SoniaNeural")


class LangfuseSettings(BaseSettings):
    """Observability settings."""

    model_config = SettingsConfigDict(env_prefix="LANGFUSE_", env_file=".env", extra="ignore")

    public_key: str = Field(default="")
    secret_key: str = Field(default="")
    host: str = Field(default="https://cloud.langfuse.com")


class AuthSettings(BaseSettings):
    """JWT auth settings."""

    model_config = SettingsConfigDict(env_prefix="JWT_", env_file=".env", extra="ignore")

    secret: str = Field(default="change-me-in-production")
    algorithm: str = Field(default="HS256")
    expiry_hours: int = Field(default=24)


class AppSettings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(env_prefix="APP_", env_file=".env", extra="ignore")

    env: str = Field(default="development")
    port: int = Field(default=8000)


class CORSSettings(BaseSettings):
    """CORS settings."""

    model_config = SettingsConfigDict(env_prefix="", env_file=".env", extra="ignore")

    cors_origins: str = Field(default="http://localhost:3000")
    log_level: str = Field(default="INFO")


class SchedulerSettings(BaseSettings):
    """Background scheduler settings."""

    model_config = SettingsConfigDict(env_prefix="SCHEDULER_", env_file=".env", extra="ignore")

    enabled: bool = Field(default=True)
    cycle_seconds: int = Field(default=300)
    max_hourly: int = Field(default=12)
    explore_weight: float = Field(default=0.4)
    research_weight: float = Field(default=0.3)
    refine_weight: float = Field(default=0.3)


class MicroFinetuneSettings(BaseSettings):
    """Micro fine-tuning settings (hourly)."""

    model_config = SettingsConfigDict(env_prefix="MICRO_FINETUNE_", env_file=".env", extra="ignore")

    enabled: bool = Field(default=True)
    interval_hours: int = Field(default=1)
    rank: int = Field(default=4)
    iters: int = Field(default=100)
    batch_size: int = Field(default=4)


class FullFinetuneSettings(BaseSettings):
    """Full fine-tuning settings (nightly)."""

    model_config = SettingsConfigDict(env_prefix="FULL_FINETUNE_", env_file=".env", extra="ignore")

    cron: str = Field(default="0 2 * * *")
    rank: int = Field(default=16)
    iters: int = Field(default=500)
    batch_size: int = Field(default=4)
    min_quality: float = Field(default=4.0)
    personality_variance_threshold: float = Field(default=0.5)
    min_examples: int = Field(default=50)


class VerificationSettings(BaseSettings):
    """Verification council settings."""

    model_config = SettingsConfigDict(env_prefix="VERIFICATION_", env_file=".env", extra="ignore")

    enabled: bool = Field(default=True)
    skeptic_accept_threshold: float = Field(default=0.8)
    skeptic_reject_threshold: float = Field(default=0.3)


class EvolutionSettings(BaseSettings):
    """Self-evolution settings."""

    model_config = SettingsConfigDict(env_prefix="", env_file=".env", extra="ignore")

    research_scout_cron: str = Field(default="0 0 * * 0")
    code_improvement_cron: str = Field(default="0 0 * * 1")


class Settings:
    """Aggregated application settings."""

    def __init__(self) -> None:
        self.database = DatabaseSettings()
        self.neo4j = Neo4jSettings()
        self.qdrant = QdrantSettings()
        self.redis = RedisSettings()
        self.llm = LLMSettings()
        self.search = SearchSettings()
        self.avatar = AvatarSettings()
        self.langfuse = LangfuseSettings()
        self.auth = AuthSettings()
        self.app = AppSettings()
        self.cors = CORSSettings()
        self.scheduler = SchedulerSettings()
        self.micro_finetune = MicroFinetuneSettings()
        self.full_finetune = FullFinetuneSettings()
        self.verification = VerificationSettings()
        self.evolution = EvolutionSettings()


settings = Settings()
