"""Meeting intelligence analysis service using LLM structured extraction and multi-chunk synthesis."""

import json
import logging
import re
from typing import Any, Dict, List, Optional
from app.config import get_settings
from app.schemas.analysis import MeetingAnalysisResult
from app.services.llm_service import (
    BaseLLMProvider,
    LLMOutputParsingError,
    get_llm_provider,
)

logger = logging.getLogger(__name__)

SYSTEM_ANALYSIS_PROMPT = """You are an expert executive meeting intelligence analyst.
Analyze the provided meeting notes or transcript and extract comprehensive, strictly grounded structured intelligence.

Guidelines:
1. Executive Summary: Provide a clear, cohesive 2-4 sentence executive overview synthesizing the entire meeting context, outcomes, and direction.
2. Meeting Purpose: State the core objective and purpose of the meeting concisely.
3. Key Discussion Points: Extract the primary topics debated, reviewed, or analyzed.
4. Decisions Made: Extract ONLY explicitly confirmed, agreed-upon decisions. Strictly distinguish confirmed decisions from tentative ideas, proposals, or unresolved suggestions. If no clear decisions were made, provide an empty list.
5. Risks and Blockers: Identify operational, technical, resource, or business risks, bottlenecks, or obstacles mentioned.
6. Unresolved Questions: List any open questions, ambiguous points, or topics deferred for future clarification.
7. Topics and Themes: List high-level themes, categories, or functional areas discussed.

Strict Constraints:
- Ground every single point strictly in the provided text. Do not hallucinate or invent facts.
- Do NOT extract individual action items or assign task owners (action items are handled separately).
- You MUST respond with a valid JSON object strictly conforming to the following structure:
{
  "executive_summary": "string",
  "meeting_purpose": "string",
  "key_discussion_points": ["string"],
  "decisions_made": ["string"],
  "risks_and_blockers": ["string"],
  "unresolved_questions": ["string"],
  "topics_and_themes": ["string"]
}
"""

SYNTHESIS_REDUCE_PROMPT = """You are an expert executive meeting intelligence analyst.
You are provided with partial analyses extracted from multiple consecutive sections of a long business meeting.
Your task is to synthesize and consolidate these partial analyses into a single, cohesive, unified meeting intelligence report covering the entire meeting from start to finish.

Guidelines:
- Combine and deduplicate key discussion points, decisions, risks, open questions, and themes.
- Write a unified, high-level executive summary that reflects the full progression of the meeting.
- Formulate a clear, unified meeting purpose statement.
- Ensure only explicitly confirmed decisions across all sections are listed in 'decisions_made'.

You MUST respond with a valid JSON object strictly conforming to the structure:
{
  "executive_summary": "string",
  "meeting_purpose": "string",
  "key_discussion_points": ["string"],
  "decisions_made": ["string"],
  "risks_and_blockers": ["string"],
  "unresolved_questions": ["string"],
  "topics_and_themes": ["string"]
}
"""


class MeetingAnalysisService:
    """Service orchestrating prompt construction, chunking, LLM execution, and response validation."""

    def __init__(self, provider: Optional[BaseLLMProvider] = None) -> None:
        """Initialize service with an optional LLM provider instance."""
        self._provider = provider

    @property
    def provider(self) -> BaseLLMProvider:
        """Retrieve the active LLM provider instance."""
        if self._provider is None:
            self._provider = get_llm_provider()
        return self._provider

    @staticmethod
    def _parse_llm_json_response(raw_response: str) -> Dict[str, Any]:
        """Parse raw LLM response text into a dictionary, extracting JSON from code blocks if needed."""
        if not raw_response or not raw_response.strip():
            raise LLMOutputParsingError("Received empty response from LLM provider.")

        text = raw_response.strip()

        # Extract content from markdown ```json ``` code fences if present
        json_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
        if json_match:
            text = json_match.group(1).strip()

        try:
            parsed = json.loads(text)
            if not isinstance(parsed, dict):
                raise LLMOutputParsingError("LLM response did not parse into a JSON dictionary object.")
            return parsed
        except json.JSONDecodeError as e:
            logger.error("Failed to decode JSON from LLM response: %s", str(e))
            raise LLMOutputParsingError(
                f"LLM returned malformed JSON output that could not be parsed: {str(e)}"
            ) from e

    @staticmethod
    def chunk_text(text: str, max_chars: int = 16000, overlap_chars: int = 1000) -> List[str]:
        """Split long meeting transcripts into overlapping chunks at paragraph boundaries.

        Args:
            text: Full raw or normalized meeting transcript text.
            max_chars: Maximum character budget per chunk.
            overlap_chars: Number of overlapping characters preserved between chunks.

        Returns:
            List of text chunks.
        """
        if len(text) <= max_chars:
            return [text]

        paragraphs = text.split("\n\n")
        chunks: List[str] = []
        current_chunk: List[str] = []
        current_length = 0

        for para in paragraphs:
            para_len = len(para) + 2
            if current_length + para_len > max_chars and current_chunk:
                chunk_str = "\n\n".join(current_chunk)
                chunks.append(chunk_str)

                # Calculate overlap from the end of current chunk
                overlap_text = chunk_str[-overlap_chars:] if len(chunk_str) > overlap_chars else chunk_str
                current_chunk = [overlap_text, para]
                current_length = len(overlap_text) + para_len
            else:
                current_chunk.append(para)
                current_length += para_len

        if current_chunk:
            chunks.append("\n\n".join(current_chunk))

        return chunks

    def _analyze_single_chunk(self, chunk_text: str, provider: BaseLLMProvider) -> MeetingAnalysisResult:
        """Execute single-pass analysis on a single text chunk."""
        settings = get_settings()

        messages = [
            {"role": "system", "content": SYSTEM_ANALYSIS_PROMPT},
            {
                "role": "user",
                "content": f"Please analyze the following meeting content:\n\n---\n{chunk_text}\n---",
            },
        ]

        raw_output = provider.generate_chat_completion(
            messages=messages,
            temperature=settings.LLM_TEMPERATURE,
            max_tokens=settings.LLM_MAX_TOKENS,
            response_format={"type": "json_object"},
        )

        parsed_dict = self._parse_llm_json_response(raw_output)

        try:
            return MeetingAnalysisResult.model_validate(parsed_dict)
        except Exception as e:
            logger.error("Schema validation failed for LLM meeting analysis output: %s", str(e))
            raise LLMOutputParsingError(
                f"LLM output failed meeting analysis schema validation: {str(e)}"
            ) from e

    def _synthesize_multiple_chunks(
        self,
        intermediate_results: List[MeetingAnalysisResult],
        provider: BaseLLMProvider,
    ) -> MeetingAnalysisResult:
        """Synthesize and consolidate multiple chunk analysis results into a single final result."""
        settings = get_settings()

        serialized_sections = [
            f"Section {idx + 1}:\n{res.model_dump_json(indent=2)}"
            for idx, res in enumerate(intermediate_results)
        ]
        combined_sections_str = "\n\n===\n\n".join(serialized_sections)

        messages = [
            {"role": "system", "content": SYNTHESIS_REDUCE_PROMPT},
            {
                "role": "user",
                "content": (
                    "Please consolidate the following section analyses into a final comprehensive meeting intelligence report:\n\n"
                    f"{combined_sections_str}"
                ),
            },
        ]

        raw_output = provider.generate_chat_completion(
            messages=messages,
            temperature=settings.LLM_TEMPERATURE,
            max_tokens=settings.LLM_MAX_TOKENS,
            response_format={"type": "json_object"},
        )

        parsed_dict = self._parse_llm_json_response(raw_output)

        try:
            return MeetingAnalysisResult.model_validate(parsed_dict)
        except Exception as e:
            logger.error("Schema validation failed during multi-chunk synthesis: %s", str(e))
            raise LLMOutputParsingError(
                f"Multi-chunk synthesis failed schema validation: {str(e)}"
            ) from e

    def analyze_meeting(
        self,
        text: str,
        provider: Optional[BaseLLMProvider] = None,
    ) -> MeetingAnalysisResult:
        """Analyze meeting transcript or notes and return validated structured output.

        Args:
            text: Raw or normalized meeting text content.
            provider: Optional custom LLM provider override.

        Returns:
            Validated MeetingAnalysisResult instance.

        Raises:
            ValueError: If input text is empty or only whitespace.
            LLMProviderError: If LLM call or parsing fails.
        """
        if not text or not text.strip():
            raise ValueError("Meeting content is empty or contains only whitespace.")

        active_provider = provider or self.provider
        settings = get_settings()

        # Split long transcripts if they exceed chunk threshold
        chunks = self.chunk_text(
            text=text.strip(),
            max_chars=settings.MAX_CHUNK_CHARS,
            overlap_chars=settings.CHUNK_OVERLAP_CHARS,
        )

        logger.info(
            "Analyzing meeting content (total chars: %d, chunk count: %d)...",
            len(text),
            len(chunks),
        )

        if len(chunks) == 1:
            return self._analyze_single_chunk(chunks[0], active_provider)

        # Multi-chunk processing: Map & Reduce
        logger.info("Executing map-reduce synthesis across %d chunks...", len(chunks))
        intermediate_results = [
            self._analyze_single_chunk(chunk, active_provider) for chunk in chunks
        ]
        return self._synthesize_multiple_chunks(intermediate_results, active_provider)


# Global singleton instance holder for MeetingAnalysisService
_meeting_analysis_service_instance: Optional[MeetingAnalysisService] = None


def get_meeting_analysis_service() -> MeetingAnalysisService:
    """Retrieve or initialize the global MeetingAnalysisService singleton."""
    global _meeting_analysis_service_instance
    if _meeting_analysis_service_instance is None:
        _meeting_analysis_service_instance = MeetingAnalysisService()
    return _meeting_analysis_service_instance
