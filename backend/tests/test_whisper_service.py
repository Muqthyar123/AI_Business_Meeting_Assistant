"""Tests for Whisper service lifecycle management, inference, and error handling."""

import os
from unittest.mock import MagicMock, patch
import pytest
from app.schemas.transcription import WhisperModelStatus
from app.services.whisper_service import (
    WhisperService,
    WhisperTranscriptionError,
    get_whisper_service,
)


def test_whisper_service_initialization():
    """Verify WhisperService initializes with correct defaults."""
    service = WhisperService(model_name="small", device="cpu")
    assert service.model_name == "small"
    assert service.device == "cpu"
    assert service.status == WhisperModelStatus.NOT_LOADED
    assert service.is_loaded is False
    assert service.load_error is None


def test_whisper_service_transcribe_missing_file_raises(tmp_path):
    """Verify transcribe raises FileNotFoundError when audio file does not exist."""
    service = WhisperService(model_name="small", device="cpu")
    non_existent = str(tmp_path / "non_existent.mp3")
    with pytest.raises(FileNotFoundError, match="does not exist"):
        service.transcribe(audio_path=non_existent)


def test_whisper_service_transcribe_successful_mocked(tmp_path):
    """Verify successful transcription execution and metadata parsing."""
    audio_file = tmp_path / "sample.mp3"
    audio_file.write_bytes(b"mock audio bytes")

    service = WhisperService(model_name="small", device="cpu")
    mock_model = MagicMock()
    mock_model.transcribe.return_value = {
        "text": "  Welcome to the board meeting.  ",
        "language": "en",
        "segments": [{"id": 0, "start": 0.0, "end": 12.5, "text": "Welcome to the board meeting."}],
    }
    service._model = mock_model
    service._status = WhisperModelStatus.LOADED

    result = service.transcribe(audio_path=str(audio_file), language="en", fp16=True)

    assert result["text"] == "Welcome to the board meeting."
    assert result["language"] == "en"
    assert result["duration"] == 12.5
    assert len(result["segments"]) == 1
    # On CPU, fp16 must always be forced to False
    mock_model.transcribe.assert_called_once_with(
        str(audio_file),
        fp16=False,
        language="en",
    )


def test_whisper_service_transcribe_error_raises_whisper_transcription_error(tmp_path):
    """Verify that internal Whisper inference errors are caught and raised as WhisperTranscriptionError."""
    audio_file = tmp_path / "corrupt.mp3"
    audio_file.write_bytes(b"corrupt audio")

    service = WhisperService(model_name="small", device="cpu")
    mock_model = MagicMock()
    mock_model.transcribe.side_effect = RuntimeError("FFmpeg error: Invalid audio header")
    service._model = mock_model
    service._status = WhisperModelStatus.LOADED

    with pytest.raises(WhisperTranscriptionError, match="Audio transcription failed"):
        service.transcribe(audio_path=str(audio_file))


def test_whisper_service_load_failure_handling():
    """Verify handling when Whisper model loading throws an exception."""
    service = WhisperService(model_name="nonexistent_model")
    with patch("builtins.__import__", side_effect=ImportError("No module named 'whisper'")):
        success = service.load_model()
        assert success is False
        assert service.status == WhisperModelStatus.UNAVAILABLE
        assert service.is_loaded is False
        assert service.load_error is not None


def test_whisper_service_unload():
    """Verify unload resets model state."""
    service = WhisperService(model_name="small")
    service._model = MagicMock()
    service._status = WhisperModelStatus.LOADED
    service.unload_model()
    assert service.is_loaded is False
    assert service.status == WhisperModelStatus.NOT_LOADED


def test_whisper_model_normalization():
    """Verify model names with prefixes or accidental text are cleanly sanitized."""
    from app.services.whisper_service import normalize_whisper_model_name

    assert normalize_whisper_model_name("whisper-base") == "base"
    assert normalize_whisper_model_name("whisper-small") == "small"
    assert normalize_whisper_model_name("smallLet his work by 1030.") == "small"
    assert normalize_whisper_model_name("base.en") == "base.en"
    assert normalize_whisper_model_name("unknown_garbage") == "base"
    assert normalize_whisper_model_name(None) == "base"
    assert normalize_whisper_model_name("") == "base"
