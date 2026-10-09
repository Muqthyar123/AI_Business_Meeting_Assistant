"""Tests for application configuration."""

import os
from app.config import Settings, get_settings


def test_default_settings():
    """Verify default configuration settings."""
    settings = Settings()
    assert settings.PROJECT_NAME == "AI Business Meeting Assistant"
    assert settings.API_V1_PREFIX == "/api"
    assert settings.MONGODB_DATABASE == "meeting_assistant"
    assert settings.MAX_UPLOAD_SIZE_MB == 100
    assert settings.WHISPER_MODEL == "small"
    assert "http://localhost:5173" in settings.CORS_ORIGINS


def test_cors_origins_parsing():
    """Verify comma-separated string parses into a list of origins."""
    settings = Settings(CORS_ORIGINS="http://localhost:3000, http://localhost:5173")
    assert settings.CORS_ORIGINS == ["http://localhost:3000", "http://localhost:5173"]


def test_get_settings_caching():
    """Verify get_settings returns a cached instance."""
    s1 = get_settings()
    s2 = get_settings()
    assert s1 is s2
