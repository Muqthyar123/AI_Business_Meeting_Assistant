"""Tests for MeetingAnalysisService extraction, chunking, and synthesis."""

import json
from unittest.mock import MagicMock, patch
import pytest
from app.schemas.analysis import MeetingAnalysisResult
from app.services.llm_service import (
    BaseLLMProvider,
    LLMOutputParsingError,
)
from app.services.meeting_analysis_service import (
    MeetingAnalysisService,
    get_meeting_analysis_service,
)


@pytest.fixture
def sample_analysis_dict():
    return {
        "executive_summary": "The engineering leadership finalized Q4 technical priorities and staffing plans.",
        "meeting_purpose": "Align on Q4 technical roadmap and budget allocations.",
        "key_discussion_points": [
            "Infrastructure scaling on MongoDB Atlas.",
            "Backend microservices latency optimization.",
        ],
        "decisions_made": [
            "Approved migration to MongoDB Atlas.",
            "Agreed to recruit 3 senior backend engineers.",
        ],
        "risks_and_blockers": [
            "Potential cutover downtime during database migration.",
        ],
        "unresolved_questions": [
            "Final cloud provider pricing tier for staging environments.",
        ],
        "topics_and_themes": [
            "Infrastructure",
            "Staffing",
            "Roadmap",
        ],
    }


def test_parse_llm_json_response_with_markdown_fence(sample_analysis_dict):
    """Verify parser extracts and parses JSON even when wrapped in markdown code blocks."""
    raw_markdown = f"Here is the analysis:\n```json\n{json.dumps(sample_analysis_dict)}\n```\nHope this helps!"
    parsed = MeetingAnalysisService._parse_llm_json_response(raw_markdown)
    assert parsed["executive_summary"] == sample_analysis_dict["executive_summary"]
    assert len(parsed["decisions_made"]) == 2


def test_parse_llm_json_response_malformed():
    """Verify malformed JSON raises LLMOutputParsingError."""
    with pytest.raises(LLMOutputParsingError, match="malformed JSON"):
        MeetingAnalysisService._parse_llm_json_response("{invalid json content, missing quotes}")


def test_parse_llm_json_response_empty():
    """Verify empty response raises LLMOutputParsingError."""
    with pytest.raises(LLMOutputParsingError, match="empty response"):
        MeetingAnalysisService._parse_llm_json_response("   ")


def test_chunk_text_short():
    """Verify short text is returned as a single chunk."""
    short = "Short meeting notes."
    chunks = MeetingAnalysisService.chunk_text(short, max_chars=1000)
    assert len(chunks) == 1
    assert chunks[0] == short


def test_chunk_text_long_splitting():
    """Verify long text is divided into overlapping chunks at paragraph boundaries."""
    paragraphs = [f"Paragraph {i}: " + ("x" * 200) for i in range(10)]
    long_text = "\n\n".join(paragraphs)

    chunks = MeetingAnalysisService.chunk_text(long_text, max_chars=600, overlap_chars=50)
    assert len(chunks) > 1
    # Verify every paragraph is represented
    for p in paragraphs:
        assert any(p[:20] in chunk for chunk in chunks)


def test_analyze_meeting_single_chunk(sample_analysis_dict):
    """Verify analyze_meeting completes and validates structured output."""
    mock_provider = MagicMock(spec=BaseLLMProvider)
    mock_provider.generate_chat_completion.return_value = json.dumps(sample_analysis_dict)
    mock_provider.provider_name = "groq"
    mock_provider.model_name = "llama-3.3-70b-versatile"

    service = MeetingAnalysisService(provider=mock_provider)
    result = service.analyze_meeting(
        text="Discussed Q4 roadmap and approved MongoDB Atlas migration."
    )

    assert isinstance(result, MeetingAnalysisResult)
    assert result.executive_summary == sample_analysis_dict["executive_summary"]
    assert len(result.decisions_made) == 2
    assert "Approved migration to MongoDB Atlas." in result.decisions_made


def test_analyze_meeting_multi_chunk_synthesis(sample_analysis_dict):
    """Verify multi-chunk analysis triggers map-reduce synthesis."""
    mock_provider = MagicMock(spec=BaseLLMProvider)
    # Return valid structured analysis on both map steps and reduce step
    mock_provider.generate_chat_completion.return_value = json.dumps(sample_analysis_dict)
    mock_provider.provider_name = "groq"
    mock_provider.model_name = "llama-3.3-70b-versatile"

    service = MeetingAnalysisService(provider=mock_provider)

    # Force chunking with very small max_chars
    paragraphs = [f"Section {i}: " + ("content " * 50) for i in range(4)]
    long_text = "\n\n".join(paragraphs)

    with patch.object(service, "chunk_text", return_value=["Chunk 1", "Chunk 2"]):
        result = service.analyze_meeting(text=long_text)

    assert isinstance(result, MeetingAnalysisResult)
    # Ensure provider was called at least 3 times (2 chunk analyses + 1 final synthesis)
    assert mock_provider.generate_chat_completion.call_count >= 3


def test_analyze_meeting_empty_text_raises():
    """Verify empty meeting text raises ValueError."""
    service = MeetingAnalysisService()
    with pytest.raises(ValueError, match="empty"):
        service.analyze_meeting(text="   \n\n\t  ")


def test_get_meeting_analysis_service_singleton():
    """Verify get_meeting_analysis_service returns singleton instance."""
    s1 = get_meeting_analysis_service()
    s2 = get_meeting_analysis_service()
    assert s1 is s2
