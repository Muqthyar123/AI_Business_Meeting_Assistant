import pytest
import numpy as np
import time
from unittest.mock import MagicMock, patch
from desktop.meeting_manager import MeetingManager, MeetingTranscriptSegment
from desktop.config import DesktopConfig
from desktop.api_client import WorkflowAnalysisResult

def test_meeting_transcript_segment():
    seg = MeetingTranscriptSegment(
        segment_id=1,
        timestamp="10:00:00",
        text="Hello world",
        duration_sec=2.5
    )
    d = seg.to_dict()
    assert d["id"] == 1
    assert d["timestamp"] == "10:00:00"
    assert d["text"] == "Hello world"
    assert d["duration"] == 2.5

def test_meeting_manager_text_cleaning_and_deduplication():
    mgr = MeetingManager()
    
    # 1. Deduplicate consecutive repetitive hallucination loops
    raw = "Let's deploy the application. Let's deploy the application. We should test it."
    cleaned = mgr._clean_and_deduplicate_text(raw)
    assert cleaned == "Let's deploy the application. We should test it."

    # 2. Capitalization and extra whitespace
    raw2 = "  welcome to the quarterly sync.   we need updates.  "
    cleaned2 = mgr._clean_and_deduplicate_text(raw2)
    assert cleaned2 == "Welcome to the quarterly sync. We need updates."

def test_meeting_manager_ordered_segment_assembly():
    segments_logged = []
    def on_seg(seg_dict, full_text):
        segments_logged.append((seg_dict, full_text))

    mgr = MeetingManager(on_segment_added=on_seg)
    mgr._append_segment("10:00:01", "Welcome everyone to the launch review.", 3.0)
    mgr._append_segment("10:00:08", "David will deploy the production database.", 2.5)
    mgr._append_segment("10:00:15", "Sarah will finalize QA smoke tests.", 2.8)

    assert len(mgr.segments) == 3
    assert mgr.segments[0].text == "Welcome everyone to the launch review."
    assert mgr.segments[1].text == "David will deploy the production database."
    assert mgr.segments[2].text == "Sarah will finalize QA smoke tests."
    
    full = mgr.get_cumulative_transcript()
    assert "Welcome everyone to the launch review." in full
    assert "David will deploy the production database." in full
    assert "Sarah will finalize QA smoke tests." in full

def test_meeting_manager_state_lifecycle():
    states = []
    def on_state(st, det):
        states.append(st)

    mgr = MeetingManager(on_state_changed=on_state)
    mgr.initialize()
    assert mgr.current_state == "idle"

    mgr.start_live_meeting(title="Sprint Retro", source="mic")
    assert mgr.current_state == "listening"
    assert mgr.meeting_title == "Sprint Retro"

    mgr.pause_live_meeting()
    assert mgr.current_state == "idle"

    mgr.resume_live_meeting(source="mic")
    assert mgr.current_state == "listening"

    mgr.shutdown()

def test_finish_meeting_empty_transcript_handling():
    errors = []
    def on_err(err):
        errors.append(err)

    mgr = MeetingManager(on_error=on_err)
    mgr.initialize()
    mgr.start_live_meeting(title="Empty Meeting")
    
    # Finish without any speech
    mgr.finish_meeting_and_submit()
    time.sleep(0.2)
    
    assert len(errors) >= 1
    assert "empty" in errors[0].lower()
    mgr.shutdown()
