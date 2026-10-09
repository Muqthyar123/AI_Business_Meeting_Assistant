import pytest
import os
from desktop.config import DesktopConfig

def test_desktop_config_defaults():
    cfg = DesktopConfig()
    assert cfg.AUDIO_RATE == 16000
    assert cfg.AUDIO_CHANNELS == 1
    assert cfg.DICTATION_PAUSE_SEC == 1.4
    assert cfg.MEETING_PAUSE_SEC == 2.0
    assert cfg.MEETING_MIN_SEGMENT_SEC == 0.4
    assert cfg.BACKEND_URL == "http://127.0.0.1:8000"
    assert cfg.workflow_sync_url == "http://127.0.0.1:8000/api/workflows/run-sync"
    assert cfg.health_url == "http://127.0.0.1:8000/api/health"

def test_desktop_config_env_overrides(monkeypatch):
    monkeypatch.setenv("BACKEND_URL", "http://meeting-server.internal:9000/")
    monkeypatch.setenv("WHISPER_MODEL", "small")
    monkeypatch.setenv("AUDIO_SOURCE", "system")
    
    cfg = DesktopConfig(
        BACKEND_URL=os.environ.get("BACKEND_URL"),
        WHISPER_MODEL=os.environ.get("WHISPER_MODEL"),
        DEFAULT_AUDIO_SOURCE=os.environ.get("AUDIO_SOURCE")
    )
    assert cfg.BACKEND_URL == "http://meeting-server.internal:9000/"
    assert cfg.workflow_sync_url == "http://meeting-server.internal:9000/api/workflows/run-sync"
    assert cfg.WHISPER_MODEL == "small"
    assert cfg.DEFAULT_AUDIO_SOURCE == "system"
