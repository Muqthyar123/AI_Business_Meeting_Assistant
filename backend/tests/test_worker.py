"""Tests for background transcription worker."""

import os
from unittest.mock import MagicMock
import pytest
from app.services.transcription_worker import process_transcription_job
from app.services.whisper_service import WhisperTranscriptionError


def test_process_transcription_job_success(tmp_path):
    """Verify worker flow on successful transcription: processing -> completed and file cleanup."""
    temp_audio = tmp_path / "temp_meeting.mp3"
    temp_audio.write_bytes(b"dummy audio content")

    mock_repo = MagicMock()
    mock_whisper = MagicMock()
    mock_whisper.model_name = "small"
    mock_whisper.transcribe.return_value = {
        "text": "Good morning team, let's review the quarter.",
        "language": "en",
        "duration": 45.2,
    }

    process_transcription_job(
        record_id="651a2b3c4d5e6f7a8b9c0d1e",
        temp_audio_path=str(temp_audio),
        requested_language="en",
        repo=mock_repo,
        whisper_service=mock_whisper,
    )

    # Verify status transition to processing
    mock_repo.mark_processing.assert_called_once_with("651a2b3c4d5e6f7a8b9c0d1e")

    # Verify whisper transcription call
    mock_whisper.transcribe.assert_called_once_with(
        audio_path=str(temp_audio),
        language="en",
        fp16=False,
    )

    # Verify completed update
    mock_repo.mark_completed.assert_called_once_with(
        record_id="651a2b3c4d5e6f7a8b9c0d1e",
        transcript_text="Good morning team, let's review the quarter.",
        detected_language="en",
        audio_duration=45.2,
        whisper_model="small",
    )

    # Verify temporary file was cleaned up
    assert not os.path.exists(str(temp_audio))


def test_process_transcription_job_whisper_failure(tmp_path):
    """Verify worker flow on Whisper failure: status transitions to failed and file is cleaned up."""
    temp_audio = tmp_path / "corrupt_audio.mp3"
    temp_audio.write_bytes(b"corrupt bytes")

    mock_repo = MagicMock()
    mock_whisper = MagicMock()
    mock_whisper.transcribe.side_effect = WhisperTranscriptionError("FFmpeg decode error")

    process_transcription_job(
        record_id="651a2b3c4d5e6f7a8b9c0d1e",
        temp_audio_path=str(temp_audio),
        repo=mock_repo,
        whisper_service=mock_whisper,
    )

    mock_repo.mark_processing.assert_called_once_with("651a2b3c4d5e6f7a8b9c0d1e")
    mock_repo.mark_failed.assert_called_once()
    args, kwargs = mock_repo.mark_failed.call_args
    assert "FFmpeg decode error" in kwargs["error_message"]

    # Verify temporary file cleanup
    assert not os.path.exists(str(temp_audio))


def test_process_transcription_job_unexpected_failure(tmp_path):
    """Verify worker handles unexpected exceptions and marks job failed."""
    temp_audio = tmp_path / "test.mp3"
    temp_audio.write_bytes(b"audio content")

    mock_repo = MagicMock()
    mock_whisper = MagicMock()
    mock_whisper.transcribe.side_effect = Exception("Out of memory")

    process_transcription_job(
        record_id="651a2b3c4d5e6f7a8b9c0d1e",
        temp_audio_path=str(temp_audio),
        repo=mock_repo,
        whisper_service=mock_whisper,
    )

    mock_repo.mark_failed.assert_called_once()
    assert not os.path.exists(str(temp_audio))
