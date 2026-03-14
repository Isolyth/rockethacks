"""Tests for services/gemini.py — Gemini agent and podcast script generation."""

import json
import pytest
from unittest.mock import patch, MagicMock, AsyncMock

from services.gemini import (
    _language_instruction,
    LANGUAGE_NAMES,
    AGENT_PROMPT,
    PODCAST_PROMPT,
    REPORT_SCHEMA,
    MAX_DOCUMENT_REQUESTS,
    analyze_with_gemini_agent,
    generate_podcast_script,
)
from services.session import Session


# ── _language_instruction ────────────────────────────────────────────────────

class TestLanguageInstruction:
    def test_english_returns_empty(self):
        result = _language_instruction("en")
        assert result == ""

    def test_spanish(self):
        result = _language_instruction("es")
        assert "Spanish" in result
        assert "IMPORTANT" in result

    def test_japanese(self):
        result = _language_instruction("ja")
        assert "Japanese" in result

    def test_all_supported_languages(self):
        for code, name in LANGUAGE_NAMES.items():
            if code == "en":
                continue
            result = _language_instruction(code)
            assert name in result

    def test_unknown_language_uses_code(self):
        result = _language_instruction("xx")
        assert "xx" in result
        assert "IMPORTANT" in result


# ── LANGUAGE_NAMES ───────────────────────────────────────────────────────────

class TestLanguageNames:
    def test_has_all_expected_languages(self):
        expected = {"en", "es", "fr", "de", "pt", "it", "ja", "ko", "zh", "hi", "ar", "nl", "pl", "ru"}
        assert set(LANGUAGE_NAMES.keys()) == expected

    def test_english_is_english(self):
        assert LANGUAGE_NAMES["en"] == "English"

    def test_all_values_are_strings(self):
        for code, name in LANGUAGE_NAMES.items():
            assert isinstance(code, str)
            assert isinstance(name, str)
            assert len(name) > 0


# ── REPORT_SCHEMA ────────────────────────────────────────────────────────────

class TestReportSchema:
    def test_is_dict(self):
        assert isinstance(REPORT_SCHEMA, dict)

    def test_has_required_top_level_fields(self):
        assert "summary" in REPORT_SCHEMA["properties"]
        assert "categories" in REPORT_SCHEMA["properties"]
        assert "top_merchants" in REPORT_SCHEMA["properties"]
        assert "insights" in REPORT_SCHEMA["properties"]
        assert "monthly_trend" in REPORT_SCHEMA["properties"]

    def test_all_fields_required(self):
        assert set(REPORT_SCHEMA["required"]) == {
            "summary", "categories", "top_merchants", "insights", "monthly_trend"
        }

    def test_summary_fields(self):
        summary = REPORT_SCHEMA["properties"]["summary"]
        assert "total_income" in summary["properties"]
        assert "total_expenses" in summary["properties"]
        assert "net_savings" in summary["properties"]
        assert "date_range" in summary["properties"]

    def test_category_item_fields(self):
        cat_item = REPORT_SCHEMA["properties"]["categories"]["items"]
        assert "name" in cat_item["properties"]
        assert "total" in cat_item["properties"]
        assert "percentage" in cat_item["properties"]
        assert "transactions" in cat_item["properties"]

    def test_merchant_item_fields(self):
        merchant_item = REPORT_SCHEMA["properties"]["top_merchants"]["items"]
        assert "name" in merchant_item["properties"]
        assert "total" in merchant_item["properties"]
        assert "count" in merchant_item["properties"]


# ── PROMPTS ──────────────────────────────────────────────────────────────────

class TestPrompts:
    def test_agent_prompt_has_placeholders(self):
        assert "$statement_text" in AGENT_PROMPT
        assert "$max_requests" in AGENT_PROMPT
        assert "$language_instruction" in AGENT_PROMPT

    def test_podcast_prompt_has_placeholders(self):
        assert "$report_json" in PODCAST_PROMPT
        assert "$language_instruction" in PODCAST_PROMPT

    def test_agent_prompt_mentions_tools(self):
        assert "request_documents" in AGENT_PROMPT
        assert "ask_question" in AGENT_PROMPT
        assert "finish" in AGENT_PROMPT

    def test_podcast_prompt_mentions_tts(self):
        assert "text-to-speech" in PODCAST_PROMPT


# ── MAX_DOCUMENT_REQUESTS ───────────────────────────────────────────────────

class TestMaxDocumentRequests:
    def test_default_value(self):
        assert isinstance(MAX_DOCUMENT_REQUESTS, int)
        assert MAX_DOCUMENT_REQUESTS > 0


# ── analyze_with_gemini_agent ────────────────────────────────────────────────

class TestAnalyzeWithGeminiAgent:
    @pytest.mark.asyncio
    async def test_yields_result_on_finish(self):
        """Agent calls finish() → yields ("result", report_data)."""
        from google.genai import types

        report_data = {
            "summary": {"total_income": 1000, "total_expenses": 500, "net_savings": 500, "date_range": "Jan"},
            "categories": [],
            "top_merchants": [],
            "insights": ["test"],
            "monthly_trend": [],
        }

        # Create a mock function call for finish
        mock_fc = MagicMock()
        mock_fc.name = "finish"
        mock_fc.args = {"report": report_data}

        mock_part = MagicMock()
        mock_part.function_call = mock_fc
        mock_part.text = None
        mock_part.thought = False

        mock_content = MagicMock()
        mock_content.parts = [mock_part]

        async def fake_stream(contents, config):
            yield ("_response", mock_content)

        session = Session(session_id="test")

        with patch("services.gemini._stream_via_thread", side_effect=fake_stream):
            events = []
            async for event_type, event_data in analyze_with_gemini_agent(
                "some statement text", file_count=1, session=session, max_requests=3
            ):
                events.append((event_type, event_data))

        result_events = [(t, d) for t, d in events if t == "result"]
        assert len(result_events) == 1
        assert result_events[0][1] == report_data

    @pytest.mark.asyncio
    async def test_yields_error_on_empty_response(self):
        """Empty response from Gemini → yields ("error", ...)."""
        async def fake_stream(contents, config):
            # No _response yielded
            return
            yield  # make this a generator

        session = Session(session_id="test")

        with patch("services.gemini._stream_via_thread", side_effect=fake_stream):
            events = []
            async for event_type, event_data in analyze_with_gemini_agent(
                "text", file_count=1, session=session
            ):
                events.append((event_type, event_data))

        assert any(t == "error" for t, d in events)

    @pytest.mark.asyncio
    async def test_yields_thinking_events(self):
        """Thinking chunks are forwarded as ("thinking", text)."""
        mock_fc = MagicMock()
        mock_fc.name = "finish"
        mock_fc.args = {"report": {"summary": {"total_income": 0, "total_expenses": 0, "net_savings": 0, "date_range": ""}, "categories": [], "top_merchants": [], "insights": [], "monthly_trend": []}}

        mock_part = MagicMock()
        mock_part.function_call = mock_fc
        mock_part.text = None
        mock_part.thought = False

        mock_content = MagicMock()
        mock_content.parts = [mock_part]

        async def fake_stream(contents, config):
            yield ("thinking", "Let me analyze this...")
            yield ("thinking", "Looking at the data...")
            yield ("_response", mock_content)

        session = Session(session_id="test")

        with patch("services.gemini._stream_via_thread", side_effect=fake_stream):
            events = []
            async for event_type, event_data in analyze_with_gemini_agent(
                "text", file_count=1, session=session
            ):
                events.append((event_type, event_data))

        thinking_events = [(t, d) for t, d in events if t == "thinking"]
        assert len(thinking_events) == 2
        assert thinking_events[0][1] == "Let me analyze this..."

    @pytest.mark.asyncio
    async def test_yields_request_documents(self):
        """Agent calls request_documents → yields event and reads session response."""
        mock_fc_req = MagicMock()
        mock_fc_req.name = "request_documents"
        mock_fc_req.args = {"document_type": "pay stub", "reason": "need income"}

        mock_part_req = MagicMock()
        mock_part_req.function_call = mock_fc_req
        mock_part_req.text = None
        mock_part_req.thought = False

        mock_content_req = MagicMock()
        mock_content_req.parts = [mock_part_req]

        mock_fc_finish = MagicMock()
        mock_fc_finish.name = "finish"
        mock_fc_finish.args = {"report": {"summary": {"total_income": 0, "total_expenses": 0, "net_savings": 0, "date_range": ""}, "categories": [], "top_merchants": [], "insights": [], "monthly_trend": []}}

        mock_part_finish = MagicMock()
        mock_part_finish.function_call = mock_fc_finish
        mock_part_finish.text = None
        mock_part_finish.thought = False

        mock_content_finish = MagicMock()
        mock_content_finish.parts = [mock_part_finish]

        call_count = 0

        async def fake_stream(contents, config):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                yield ("_response", mock_content_req)
            else:
                yield ("_response", mock_content_finish)

        session = Session(session_id="test")
        session.user_response = {"action": "skip"}

        with patch("services.gemini._stream_via_thread", side_effect=fake_stream):
            events = []
            async for event_type, event_data in analyze_with_gemini_agent(
                "text", file_count=1, session=session, max_requests=3
            ):
                events.append((event_type, event_data))
                if event_type == "request_documents":
                    # Simulate route handler setting the response
                    session.user_response = {"action": "skip"}

        doc_events = [(t, d) for t, d in events if t == "request_documents"]
        assert len(doc_events) == 1
        assert doc_events[0][1]["document_type"] == "pay stub"

    @pytest.mark.asyncio
    async def test_yields_ask_question(self):
        """Agent calls ask_question → yields event and reads session response."""
        mock_fc_ask = MagicMock()
        mock_fc_ask.name = "ask_question"
        mock_fc_ask.args = {"question": "What is your goal?", "options": ["Save more", "Reduce debt"]}

        mock_part_ask = MagicMock()
        mock_part_ask.function_call = mock_fc_ask
        mock_part_ask.text = None
        mock_part_ask.thought = False

        mock_content_ask = MagicMock()
        mock_content_ask.parts = [mock_part_ask]

        mock_fc_finish = MagicMock()
        mock_fc_finish.name = "finish"
        mock_fc_finish.args = {"report": {"summary": {"total_income": 0, "total_expenses": 0, "net_savings": 0, "date_range": ""}, "categories": [], "top_merchants": [], "insights": [], "monthly_trend": []}}

        mock_part_finish = MagicMock()
        mock_part_finish.function_call = mock_fc_finish
        mock_part_finish.text = None
        mock_part_finish.thought = False

        mock_content_finish = MagicMock()
        mock_content_finish.parts = [mock_part_finish]

        call_count = 0

        async def fake_stream(contents, config):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                yield ("_response", mock_content_ask)
            else:
                yield ("_response", mock_content_finish)

        session = Session(session_id="test")

        with patch("services.gemini._stream_via_thread", side_effect=fake_stream):
            events = []
            async for event_type, event_data in analyze_with_gemini_agent(
                "text", file_count=1, session=session, max_requests=3
            ):
                events.append((event_type, event_data))
                if event_type == "ask_question":
                    session.user_response = {"answer": "Save more"}

        ask_events = [(t, d) for t, d in events if t == "ask_question"]
        assert len(ask_events) == 1
        assert ask_events[0][1]["question"] == "What is your goal?"
        assert ask_events[0][1]["options"] == ["Save more", "Reduce debt"]

    @pytest.mark.asyncio
    async def test_multi_file_prompt_includes_reminder(self):
        """When file_count > 1, the MULTI_DOC_REMINDER is included."""
        mock_fc = MagicMock()
        mock_fc.name = "finish"
        mock_fc.args = {"report": {"summary": {"total_income": 0, "total_expenses": 0, "net_savings": 0, "date_range": ""}, "categories": [], "top_merchants": [], "insights": [], "monthly_trend": []}}

        mock_part = MagicMock()
        mock_part.function_call = mock_fc
        mock_part.text = None
        mock_part.thought = False

        mock_content = MagicMock()
        mock_content.parts = [mock_part]

        captured_contents = []

        async def fake_stream(contents, config):
            captured_contents.append(contents)
            yield ("_response", mock_content)

        session = Session(session_id="test")

        with patch("services.gemini._stream_via_thread", side_effect=fake_stream):
            async for _ in analyze_with_gemini_agent(
                "text", file_count=3, session=session
            ):
                pass

        # The first content should contain the multi-doc reminder
        first_content = captured_contents[0][0]
        prompt_text = first_content.parts[0].text
        assert "3 separate bank statement documents" in prompt_text

    @pytest.mark.asyncio
    async def test_text_fallback_valid_json(self):
        """Model returns text (no tool calls) with valid JSON → treated as result."""
        mock_part = MagicMock()
        mock_part.function_call = None
        mock_part.text = json.dumps({"summary": {"total_income": 100, "total_expenses": 50, "net_savings": 50, "date_range": "Jan"}, "categories": [], "top_merchants": [], "insights": [], "monthly_trend": []})
        mock_part.thought = False

        mock_content = MagicMock()
        mock_content.parts = [mock_part]

        async def fake_stream(contents, config):
            yield ("_response", mock_content)

        session = Session(session_id="test")

        with patch("services.gemini._stream_via_thread", side_effect=fake_stream):
            events = []
            async for event_type, event_data in analyze_with_gemini_agent(
                "text", file_count=1, session=session
            ):
                events.append((event_type, event_data))

        result_events = [e for e in events if e[0] == "result"]
        assert len(result_events) == 1

    @pytest.mark.asyncio
    async def test_text_fallback_invalid_json(self):
        """Model returns text (no tool calls) with invalid JSON → error."""
        mock_part = MagicMock()
        mock_part.function_call = None
        mock_part.text = "I cannot parse this data properly"
        mock_part.thought = False

        mock_content = MagicMock()
        mock_content.parts = [mock_part]

        async def fake_stream(contents, config):
            yield ("_response", mock_content)

        session = Session(session_id="test")

        with patch("services.gemini._stream_via_thread", side_effect=fake_stream):
            events = []
            async for event_type, event_data in analyze_with_gemini_agent(
                "text", file_count=1, session=session
            ):
                events.append((event_type, event_data))

        error_events = [e for e in events if e[0] == "error"]
        assert len(error_events) == 1

    @pytest.mark.asyncio
    async def test_max_iterations_safety(self):
        """Agent exceeds max iterations → error."""
        # Always return ask_question to loop forever
        mock_fc = MagicMock()
        mock_fc.name = "ask_question"
        mock_fc.args = {"question": "Q?", "options": ["A"]}

        mock_part = MagicMock()
        mock_part.function_call = mock_fc
        mock_part.text = None
        mock_part.thought = False

        mock_content = MagicMock()
        mock_content.parts = [mock_part]

        async def fake_stream(contents, config):
            yield ("_response", mock_content)

        session = Session(session_id="test")

        with patch("services.gemini._stream_via_thread", side_effect=fake_stream):
            events = []
            async for event_type, event_data in analyze_with_gemini_agent(
                "text", file_count=1, session=session, max_requests=1
            ):
                events.append((event_type, event_data))
                if event_type == "ask_question":
                    session.user_response = {"answer": "A"}

        # Should eventually hit "exceeded maximum iterations" error
        error_events = [e for e in events if e[0] == "error"]
        assert len(error_events) == 1
        assert "maximum iterations" in error_events[0][1].lower() or "exceeded" in error_events[0][1].lower()


# ── generate_podcast_script ──────────────────────────────────────────────────

class TestGeneratePodcastScript:
    @pytest.mark.asyncio
    async def test_returns_text(self):
        mock_response = MagicMock()
        mock_response.text = "Welcome to your podcast!"

        with patch("services.gemini.asyncio.to_thread", return_value=mock_response):
            result = await generate_podcast_script({"summary": {}})

        assert result == "Welcome to your podcast!"

    @pytest.mark.asyncio
    async def test_includes_report_in_prompt(self):
        mock_response = MagicMock()
        mock_response.text = "Script here"

        captured_args = {}

        async def mock_to_thread(fn, *args, **kwargs):
            captured_args["args"] = args
            captured_args["kwargs"] = kwargs
            return mock_response

        with patch("services.gemini.asyncio.to_thread", side_effect=mock_to_thread):
            await generate_podcast_script({"summary": {"total_income": 5000}})

        # The prompt (contents argument) should contain the report data
        contents_arg = captured_args["kwargs"].get("contents") or captured_args["args"][-1]
        assert "5000" in str(contents_arg)

    @pytest.mark.asyncio
    async def test_language_instruction_for_non_english(self):
        mock_response = MagicMock()
        mock_response.text = "Script"

        captured_args = {}

        async def mock_to_thread(fn, *args, **kwargs):
            captured_args["args"] = args
            captured_args["kwargs"] = kwargs
            return mock_response

        with patch("services.gemini.asyncio.to_thread", side_effect=mock_to_thread):
            await generate_podcast_script({"summary": {}}, language="es")

        contents_arg = captured_args["kwargs"].get("contents") or captured_args["args"][-1]
        assert "Spanish" in str(contents_arg)

    @pytest.mark.asyncio
    async def test_english_no_language_instruction(self):
        mock_response = MagicMock()
        mock_response.text = "Script"

        captured_args = {}

        async def mock_to_thread(fn, *args, **kwargs):
            captured_args["args"] = args
            captured_args["kwargs"] = kwargs
            return mock_response

        with patch("services.gemini.asyncio.to_thread", side_effect=mock_to_thread):
            await generate_podcast_script({"summary": {}}, language="en")

        contents_arg = captured_args["kwargs"].get("contents") or captured_args["args"][-1]
        assert "IMPORTANT: Write the ENTIRE script in" not in str(contents_arg)
