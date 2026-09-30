"""Application configuration via environment variables."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://civicpulse:civicpulse@postgres:5432/civicpulse"

    # Redis
    REDIS_URL: str = "redis://redis:6379/0"

    # Triage
    TRIAGE_PROVIDER: str = "simulated"
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.1-8b-instant"
    OLLAMA_BASE_URL: str = "http://ollama:11434"
    OLLAMA_MODEL: str = "llama3.2:1b"

    # Rate Limiting
    RATE_LIMIT_MAX_REQUESTS: int = 10
    RATE_LIMIT_WINDOW_SECONDS: int = 60

    # App
    LOG_LEVEL: str = "INFO"
    ENVIRONMENT: str = "development"

    # Tracing (OpenTelemetry). Empty = tracing disabled (the default, and what
    # CI uses, so tests stay deterministic). Base URL of an OTLP/HTTP receiver,
    # e.g. http://jaeger.observability.svc.cluster.local:4318
    OTEL_EXPORTER_OTLP_ENDPOINT: str = ""
    OTEL_SERVICE_NAME: str = "civicpulse-backend"


settings = Settings()
