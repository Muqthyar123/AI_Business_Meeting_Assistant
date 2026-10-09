import pytest
import numpy as np
import time
from desktop.audio_capture import AudioCaptureEngine

def test_audio_capture_initialization():
    engine = AudioCaptureEngine(
        rate=16000,
        dictation_pause_sec=1.4,
        meeting_pause_sec=2.0
    )
    assert engine.rate == 16000
    assert engine.dictation_pause_sec == 1.4
    assert engine.meeting_pause_sec == 2.0
    assert engine.capture_mode == "dictation"
    assert not engine.is_capturing

def test_audio_capture_pause_tuning():
    engine = AudioCaptureEngine()
    engine.set_pause_threshold(2.5)
    assert engine.meeting_pause_sec == 2.5
    engine.set_silence_threshold(0.005)
    assert engine.meeting_silence_threshold == 0.005

def test_meeting_mode_segmentation_on_synthetic_audio():
    segments_received = []
    
    def on_segment(audio, vol):
        segments_received.append((audio, vol))

    engine = AudioCaptureEngine(
        rate=16000,
        block_size=512,
        meeting_silence_threshold=0.01,
        meeting_pause_sec=0.1,  # Short pause for test speed
        meeting_min_segment_sec=0.05,
        on_speech_segment=on_segment
    )
    engine.capture_mode = "meeting"
    engine.is_capturing = True

    # 1. Feed 10 blocks of speech (vol ~ 0.05)
    speech_block = np.ones(512, dtype=np.float32) * 0.05
    for _ in range(10):
        engine._process_audio_chunk(speech_block)

    # 2. Feed 5 blocks of silence (vol ~ 0.0001) to trigger pause threshold
    silence_block = np.ones(512, dtype=np.float32) * 0.0001
    for _ in range(5):
        engine._process_audio_chunk(silence_block)

    assert len(segments_received) == 1
    audio_data, vol = segments_received[0]
    assert isinstance(audio_data, np.ndarray)
    assert audio_data.dtype == np.int16
    assert len(audio_data) > 0
    assert vol > 0.01

def test_meeting_mode_flush_pending_audio():
    segments_received = []
    def on_segment(audio, vol):
        segments_received.append((audio, vol))

    engine = AudioCaptureEngine(
        rate=16000,
        meeting_min_segment_sec=0.05,
        on_speech_segment=on_segment
    )
    engine.capture_mode = "meeting"
    engine.is_capturing = True

    # Feed speech without pause
    speech_block = np.ones(1024, dtype=np.float32) * 0.05
    engine._process_audio_chunk(speech_block)

    # No segment emitted yet since no pause occurred
    assert len(segments_received) == 0

    # Explicitly flush
    engine.flush_pending_segment()

    # Now the pending speech segment should be emitted
    assert len(segments_received) == 1
    assert len(segments_received[0][0]) == 1024

def test_dictation_mode_silence_detection():
    engine = AudioCaptureEngine(
        rate=16000,
        dictation_silence_threshold=0.01,
        dictation_pause_sec=0.1
    )
    engine.capture_mode = "dictation"
    engine.is_capturing = True

    # Speech
    speech_block = np.ones(512, dtype=np.float32) * 0.05
    for _ in range(5):
        engine._process_audio_chunk(speech_block)
    assert engine.is_capturing

    # Silence exceeding threshold
    silence_block = np.zeros(512, dtype=np.float32)
    for _ in range(5):
        engine._process_audio_chunk(silence_block)

    # Should have triggered auto-stop
    assert not engine.is_capturing
