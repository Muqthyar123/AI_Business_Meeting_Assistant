from functools import lru_cache
from typing import List, Optional, Union
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables and .env file."""

    # Project Information
    PROJECT_NAME: str = "AI Business Meeting Assistant"
    API_V1_PREFIX: str = "/api"
    VERSION: str = "0.1.0"
    DEBUG: bool = False
    APP_ENV: str = "development"

    # MongoDB Settings
    MONGODB_URI: str = Field(
        default="mongodb://localhost:27017",
        description="MongoDB connection string (local or Atlas)",
    )
    MONGODB_DATABASE: str = Field(
        default="meeting_assistant",
        description="Target MongoDB database name",
    )

    # Upload Settings
    UPLOAD_DIR: str = Field(
        default="uploads",
        description="Directory for temporary uploaded audio and document files",
    )
    MAX_UPLOAD_SIZE_MB: Union[int, float] = Field(
        default=100,
        description="Maximum allowed upload size in megabytes",
    )

    # Whisper Settings
    WHISPER_MODEL: str = Field(
        default="small",
        description="OpenAI Whisper model name (tiny, base, small, medium, large)",
    )

    # LLM / Groq Settings
    GROQ_API_KEY: Optional[str] = Field(
        default=None,
        description="API key for Groq Cloud LLM inference",
    )
    GROQ_MODEL: str = Field(
        default="qwen/qwen3.8-27b",
        description="Groq model name for meeting intelligence extraction",
    )
    LLM_PROVIDER: str = Field(
        default="groq",
        description="Active LLM provider interface (default: groq)",
    )
    LLM_TEMPERATURE: float = Field(
        default=0.1,
        description="Sampling temperature for deterministic structured extraction",
    )
    LLM_MAX_TOKENS: int = Field(
        default=4096,
        description="Maximum token budget for LLM response generation",
    )
    LLM_TIMEOUT_SECONDS: float = Field(
        default=60.0,
        description="HTTP request timeout in seconds for LLM provider API calls",
    )

    # Transcript Chunking Settings
    MAX_CHUNK_CHARS: int = Field(
        default=16000,
        description="Character threshold above which long transcripts are chunked for analysis",
    )
    CHUNK_OVERLAP_CHARS: int = Field(
        default=1000,
        description="Character overlap preserved between consecutive transcript chunks",
    )

    # CORS Settings
    CORS_ORIGINS: Union[List[str], str] = Field(
        default=["http://localhost:5173", "http://127.0.0.1:5173"],
        description="Allowed CORS origins for the frontend",
    )

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, list):
            return v
        return ["http://localhost:5173", "http://127.0.0.1:5173"]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


@lru_cache()
def get_settings() -> Settings:
    """Return a cached instance of application settings."""
    return Settings()
