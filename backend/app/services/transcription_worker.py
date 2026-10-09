"""Background worker for asynchronous Whisper audio transcription processing."""

import logging
import os
import threading
from typing import Optional
from app.repositories.transcription_repo import TranscriptionRepository, get_transcription_repository
from app.services.whisper_service import (
    WhisperService,
    WhisperTranscriptionError,
    get_whisper_service,
)

logger = logging.getLogger(__name__)

# Concurrency semaphore: Limits simultaneous CPU-intensive Whisper transcription tasks to 1
# This prevents excessive CPU/RAM contention and memory exhaustion on local machines
_transcription_semaphore = threading.BoundedSemaphore(1)


def process_transcription_job(
    record_id: str,
    temp_audio_path: str,
    requested_language: Optional[str] = None,
    whisper_model: Optional[str] = None,
    repo: Optional[TranscriptionRepository] = None,
    whisper_service: Optional[WhisperService] = None,
) -> None:
    """Execute background transcription for an uploaded audio file.

    Note:
        In-process background tasks run within the FastAPI application process.
        They are not durable across server restarts or crashes.

    Args:
        record_id: MongoDB transcription record ID string.
        temp_audio_path: Absolute or relative path to the temporary audio file.
        requested_language: Optional ISO language code to guide transcription.
        whisper_model: Configured Whisper model name.
        repo: Optional TranscriptionRepository instance (defaults to shared repo).
        whisper_service: Optional WhisperService instance (defaults to shared service).
    """
    repository = repo or get_transcription_repository()
    whisper_svc = whisper_service or get_whisper_service(model_name=whisper_model)

    logger.info("Acquiring concurrency lock for transcription job '%s'...", record_id)
    with _transcription_semaphore:
        logger.info("Lock acquired. Beginning transcription for record '%s'...", record_id)
        try:
            # 1. Update status to processing
            repository.mark_processing(record_id)

            # 2. Run Whisper transcription (CPU execution uses fp16=False)
            result = whisper_svc.transcribe(
                audio_path=temp_audio_path,
                language=requested_language,
                fp16=False,
            )

            # 3. Save results and mark completed
            transcript_text = result.get("text", "")
            detected_language = result.get("language")
            duration = result.get("duration")

            repository.mark_completed(
                record_id=record_id,
                transcript_text=transcript_text,
                detected_language=detected_language,
                audio_duration=duration,
                whisper_model=whisper_svc.model_name,
            )
            logger.info("Successfully completed transcription for job '%s'.", record_id)

        except WhisperTranscriptionError as e:
            logger.error("Whisper transcription error on job '%s': %s", record_id, str(e))
            try:
                repository.mark_failed(
                    record_id=record_id,
                    error_message=f"Audio transcription failed: {str(e)}",
                )
            except Exception as repo_err:
                logger.error("Failed to update status to failed for job '%s': %s", record_id, str(repo_err))

        except Exception as e:
            logger.error("Unexpected error processing transcription job '%s': %s", record_id, str(e))
            try:
                repository.mark_failed(
                    record_id=record_id,
                    error_message=f"An unexpected error occurred during audio processing: {str(e)}",
                )
            except Exception as repo_err:
                logger.error("Failed to update status to failed for job '%s': %s", record_id, str(repo_err))

        finally:
            # 4. Clean up temporary audio file regardless of outcome
            if temp_audio_path and os.path.exists(temp_audio_path):
                try:
                    os.remove(temp_audio_path)
                    logger.info("Cleaned up temporary audio file '%s'.", temp_audio_path)
                except Exception as e:
                    logger.warning(
                        "Failed to remove temporary audio file '%s': %s",
                        temp_audio_path,
                        str(e),
                    )
