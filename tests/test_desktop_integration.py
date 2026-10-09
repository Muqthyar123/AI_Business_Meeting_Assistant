import pytest
import numpy as np
import time
from unittest.mock import MagicMock, patch
from desktop.meeting_manager import MeetingManager
from desktop.config import DesktopConfig
from desktop.api_client import WorkflowAnalysisResult

def test_live_meeting_end_to_end_simulated_flow():
    received_segments = []
    state_history = []
    received_analysis = []
    
    def on_seg(seg_dict, full_text):
        received_segments.append((seg_dict, full_text))
        
    def on_st(st, det):
        state_history.append((st, det))
        
    def on_analysis(result):
        received_analysis.append(result)

    mgr = MeetingManager(
        on_segment_added=on_seg,
        on_state_changed=on_st,
        on_analysis_complete=on_analysis
    )
    mgr.initialize()

    # Start live meeting
    mgr.start_live_meeting(title="Q4 Architecture & Launch Sync", source="both")
    assert mgr.active_mode == "meeting"
    assert mgr.current_state == "listening"

    # Simulate 3 incoming speech segments
    with patch.object(mgr, '_transcribe_audio_array') as mock_transcribe:
        mock_transcribe.side_effect = [
            "We are reviewing the Q4 architecture and timeline.",
            "David will lead the database migration by November 15.",
            "Sarah will conduct security audits on the staging environment."
        ]

        # Feed segment 1
        dummy_audio_1 = np.ones(16000, dtype=np.int16) * 1000
        mgr._handle_incoming_speech_segment(dummy_audio_1, vol=0.05)
        time.sleep(0.3)

        # Feed segment 2
        dummy_audio_2 = np.ones(16000, dtype=np.int16) * 1200
        mgr._handle_incoming_speech_segment(dummy_audio_2, vol=0.06)
        time.sleep(0.3)

        # Feed segment 3
        dummy_audio_3 = np.ones(16000, dtype=np.int16) * 1100
        mgr._handle_incoming_speech_segment(dummy_audio_3, vol=0.055)
        time.sleep(0.3)

    assert len(mgr.segments) == 3
    assert mgr.segments[0].text == "We are reviewing the Q4 architecture and timeline."
    assert mgr.segments[1].text == "David will lead the database migration by November 15."
    assert mgr.segments[2].text == "Sarah will conduct security audits on the staging environment."

    full_transcript = mgr.get_cumulative_transcript()
    assert "David will lead the database migration by November 15." in full_transcript
    assert "Sarah will conduct security audits on the staging environment." in full_transcript

    # Finish meeting and submit to mocked backend
    mock_workflow_result = WorkflowAnalysisResult(
        success=True,
        status="completed",
        workflow_id="wf_live_777",
        title="Q4 Architecture & Launch Sync",
        executive_summary="Team finalized Q4 migration and security audit plan.",
        discussion_points=["Database Migration", "Security Audits"],
        decisions=["Migrate DB by Nov 15"],
        risks=["Downtime during schema upgrade"],
        unresolved_questions=["Staging server capacity"],
        tasks=[
            {"id": "t1", "title": "DB Migration", "owner": "David", "priority": "high", "deadline": "2026-11-15"},
            {"id": "t2", "title": "Security Audits", "owner": "Sarah", "priority": "medium", "deadline": "2026-11-20"}
        ],
        follow_up_plan={"immediate_actions": ["Send architecture RFC"]}
    )

    with patch.object(mgr.api_client, 'submit_meeting_workflow_sync', return_value=mock_workflow_result) as mock_submit:
        mgr.finish_meeting_and_submit()
        time.sleep(0.5)

        mock_submit.assert_called_once()
        call_args = mock_submit.call_args[1]
        assert "David will lead" in call_args["transcript_text"]
        assert call_args["title"] == "Q4 Architecture & Launch Sync"

    assert len(received_analysis) == 1
    analysis_res = received_analysis[0]
    assert analysis_res.workflow_id == "wf_live_777"
    assert len(analysis_res.tasks) == 2
    assert analysis_res.tasks[0]["owner"] == "David"

    mgr.shutdown()

def test_dictation_mode_independent_execution():
    dictation_results = []
    def on_dict(text):
        dictation_results.append(text)

    mgr = MeetingManager(on_dictation_ready=on_dict)
    mgr.initialize()

    with patch.object(mgr, '_transcribe_audio_array', return_value="Please schedule a follow up call tomorrow."):
        dummy_audio = np.ones(8000, dtype=np.int16) * 2000
        mgr._handle_dictation_complete(dummy_audio)
        time.sleep(0.3)

    assert len(dictation_results) == 1
    assert dictation_results[0] == "Please schedule a follow up call tomorrow."

    mgr.shutdown()
