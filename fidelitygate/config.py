from pathlib import Path
from typing import Any, List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration for FidelityGate Layer 1."""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    APP_NAME: str = "FidelityGate Backend & Ingestion Engine"
    APP_VERSION: str = "1.0.0"
    APP_ENV: str = "development"
    DEBUG: Any = False

    # Server Bindings
    BACKEND_HOST: str = "127.0.0.1"
    BACKEND_PORT: int = 8000
    CORS_ORIGINS: List[str] = Field(
        default_factory=lambda: [
            "http://localhost:3000",
            "http://localhost:5173",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:5173",
        ]
    )

    # Persistence & Filesystem Boundaries
    DATABASE_PATH: str = "fidelitygate.db"
    DATA_ROOT: str = "data"
    MAX_FILE_SIZE_MB: int = 100

    # Layer 3: LLM & Investigation Agent Configuration
    LLM_PROVIDER: str = "openai"
    LLM_API_KEY: Optional[str] = None
    LLM_BASE_URL: str = "https://api.openai.com/v1"
    LLM_MODEL: str = "gpt-4o-mini"
    LLM_MAX_CALLS_PER_RUN: int = 6
    LLM_MAX_OUTPUT_TOKENS: int = 700
    LLM_TIMEOUT_SECONDS: float = 20.0
    LLM_MAX_RETRIES: int = 1
    LLM_MAX_DAILY_CALLS: int = 30
    MAX_TOOL_CALLS_PER_INVESTIGATION: int = 10
    MAX_DIAGNOSTIC_CALLS_PER_RUN: int = 3
    DIAGNOSTIC_BUDGET_USD: float = 0.05

    @property
    def data_root_path(self) -> Path:
        return Path(self.DATA_ROOT).resolve()

    @property
    def raw_data_path(self) -> Path:
        p = self.data_root_path / "raw"
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def processed_data_path(self) -> Path:
        p = self.data_root_path / "processed"
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def manifests_path(self) -> Path:
        p = self.data_root_path / "manifests"
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def reports_path(self) -> Path:
        p = self.data_root_path / "reports"
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def quarantine_path(self) -> Path:
        p = self.data_root_path / "quarantine"
        p.mkdir(parents=True, exist_ok=True)
        return p


settings = Settings()
