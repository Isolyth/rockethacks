"""Tests for routes/analyze.py — WebSocket endpoint and helpers."""

import base64
import json
import pytest
from unittest.mock import patch, MagicMock, AsyncMock

from starlette.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from main import app
from routes.analyze import parse_file_data, send_json
from tests.conftest import VALID_REPORT_DATA, MOCK_PODCAST_SCRIPT


# ── parse_file_data ──────────────────────────────────────────────────────────

class TestParseFileData:
    def test_csv_file(self):
        result = parse_file_data("statement.csv", b"date,amount\n2024-01-01,50")
        assert result is not None
        assert "date,amount" in result

    def test_pdf_file(self):
        with patch("routes.analyze.parse_pdf") as mock_parse:
            mock_parse.return_value = "PDF content"
            result = parse_file_data("statement.pdf", b"fake pdf")
            assert result == "PDF content"

    def test_uppercase_csv(self):
        result = parse_file_data("STATEMENT.CSV", b"a,b\n1,2")
        assert result is not None

    def test_uppercase_pdf(self):
        with patch("routes.analyze.parse_pdf", return_value="text"):
            result = parse_file_data("STATEMENT.PDF", b"fake")
            assert result == "text"

    def test_unsupported_txt(self):
        result = parse_file_data("notes.txt", b"hello")
        assert result is None

    def test_unsupported_xlsx(self):
        result = parse_file_data("data.xlsx", b"binary")
        assert result is None

    def test_unsupported_no_extension(self):
        result = parse_file_data("file", b"data")
        assert result is None

    def test_mixed_case_extension(self):
        result = parse_file_data("data.CsV", b"a,b\n1,2")
        assert result is not None


# ── send_json ────────────────────────────────────────────────────────────────

class TestSendJson:
    @pytest.mark.asyncio
    async def test_sends_json_text(self):
        mock_ws = AsyncMock()
        await send_json(mock_ws, {"type": "progress", "step": "parsing"})
        mock_ws.send_text.assert_called_once()
        sent = json.loads(mock_ws.send_text.call_args[0][0])
        assert sent["type"] == "progress"
        assert sent["step"] == "parsing"

    @pytest.mark.asyncio
    async def test_sends_nested_data(self):
        mock_ws = AsyncMock()
        data = {"type": "report_ready", "report": {"summary": {"total_income": 5000}}}
        await send_json(mock_ws, data)
        sent = json.loads(mock_ws.send_text.call_args[0][0])
        assert sent["report"]["summary"]["total_income"] == 5000


# ── Helper for WebSocket tests ──────────────────────────────────────────────

def _make_upload_msg(files, language="en"):
    """Build an upload_files WebSocket message."""
    file_list = []
    for name, content in files:
        file_list.append({
            "name": name,
            "content": base64.b64encode(content).decode(),
        })
    return json.dumps({"type": "upload_files", "files": file_list, "language": language})


def _collect_ws_messages(ws, respond_to=None):
    """Read all messages from a WebSocket until terminal event or disconnect.

    respond_to: dict mapping message type to a callback(ws, msg) that sends a reply.
    """
    messages = []
    respond_to = respond_to or {}
    try:
        for _ in range(100):  # safety limit
            raw = ws.receive_text()
            data = json.loads(raw)
            messages.append(data)
            # Handle interactive responses
            if data["type"] in respond_to:
                respond_to[data["type"]](ws, data)
            # Terminal events
            if data["type"] in ("podcast_audio_ready", "error"):
                break
    except WebSocketDisconnect:
        pass
    return messages


# ── WebSocket /ws/analyze ────────────────────────────────────────────────────

class TestWsAnalyze:
    def test_csv_full_pipeline(self):
        """Happy path: CSV upload → progress → report → podcast."""
        mock_audio = {
            "audio_base64": "bW9ja2F1ZGlv",
            "sentences": [{"text": "Hello.", "start": 0.0, "end": 1.0}],
        }

        async def fake_agent(text, file_count, session, language="en", **kw):
            yield ("result", VALID_REPORT_DATA)

        with (
            patch("routes.analyze.analyze_with_gemini_agent", side_effect=fake_agent),
            patch("routes.analyze.generate_podcast_script", new_callable=AsyncMock, return_value=MOCK_PODCAST_SCRIPT),
            patch("routes.analyze.generate_podcast_audio", new_callable=AsyncMock, return_value=mock_audio),
        ):
            client = TestClient(app)
            with client.websocket_connect("/ws/analyze") as ws:
                ws.send_text(_make_upload_msg([("test.csv", b"date,amount\n2024-01-01,50")]))
                messages = _collect_ws_messages(ws)

        types = [m["type"] for m in messages]
        assert "progress" in types
        assert "report_ready" in types
        assert "podcast_audio_ready" in types

        report_msg = next(m for m in messages if m["type"] == "report_ready")
        assert report_msg["report"]["summary"]["total_income"] == 5000.0

        audio_msg = next(m for m in messages if m["type"] == "podcast_audio_ready")
        assert audio_msg["podcast_script"] == MOCK_PODCAST_SCRIPT
        assert audio_msg["audio_base64"] == "bW9ja2F1ZGlv"

    def test_pdf_upload(self):
        """PDF file is parsed and sent to agent."""
        async def fake_agent(text, file_count, session, language="en", **kw):
            yield ("result", VALID_REPORT_DATA)

        mock_audio = {"audio_base64": "data", "sentences": []}

        with (
            patch("routes.analyze.parse_pdf", return_value="PDF statement text"),
            patch("routes.analyze.analyze_with_gemini_agent", side_effect=fake_agent),
            patch("routes.analyze.generate_podcast_script", new_callable=AsyncMock, return_value="Script"),
            patch("routes.analyze.generate_podcast_audio", new_callable=AsyncMock, return_value=mock_audio),
        ):
            client = TestClient(app)
            with client.websocket_connect("/ws/analyze") as ws:
                ws.send_text(_make_upload_msg([("bank.pdf", b"fake pdf bytes")]))
                messages = _collect_ws_messages(ws)

        types = [m["type"] for m in messages]
        assert "report_ready" in types

    def test_unsupported_file_type(self):
        """Uploading an unsupported file type returns an error."""
        client = TestClient(app)
        with client.websocket_connect("/ws/analyze") as ws:
            ws.send_text(_make_upload_msg([("data.txt", b"hello")]))
            messages = _collect_ws_messages(ws)

        error_msg = next(m for m in messages if m["type"] == "error")
        assert "Unsupported file type" in error_msg["message"]

    def test_invalid_message_type(self):
        """Sending wrong message type returns error."""
        client = TestClient(app)
        with client.websocket_connect("/ws/analyze") as ws:
            ws.send_text(json.dumps({"type": "wrong_type", "data": "bad"}))
            messages = _collect_ws_messages(ws)

        assert any(m["type"] == "error" for m in messages)
        error_msg = next(m for m in messages if m["type"] == "error")
        assert "Expected upload_files" in error_msg["message"]

    def test_no_files(self):
        """Sending upload_files with empty files list returns error."""
        client = TestClient(app)
        with client.websocket_connect("/ws/analyze") as ws:
            ws.send_text(json.dumps({"type": "upload_files", "files": []}))
            messages = _collect_ws_messages(ws)

        assert any(m["type"] == "error" for m in messages)

    def test_multiple_files(self):
        """Multiple CSV files are combined."""
        captured_text = []

        async def fake_agent(text, file_count, session, language="en", **kw):
            captured_text.append(text)
            yield ("result", VALID_REPORT_DATA)

        mock_audio = {"audio_base64": "data", "sentences": []}

        with (
            patch("routes.analyze.analyze_with_gemini_agent", side_effect=fake_agent),
            patch("routes.analyze.generate_podcast_script", new_callable=AsyncMock, return_value="Script"),
            patch("routes.analyze.generate_podcast_audio", new_callable=AsyncMock, return_value=mock_audio),
        ):
            client = TestClient(app)
            with client.websocket_connect("/ws/analyze") as ws:
                ws.send_text(_make_upload_msg([
                    ("jan.csv", b"date,amount\n2024-01-01,50"),
                    ("feb.csv", b"date,amount\n2024-02-01,75"),
                ]))
                messages = _collect_ws_messages(ws)

        assert len(captured_text) == 1
        assert "jan.csv" in captured_text[0]
        assert "feb.csv" in captured_text[0]

    def test_language_forwarded(self):
        """Language parameter is forwarded to the agent."""
        captured_lang = []

        async def fake_agent(text, file_count, session, language="en", **kw):
            captured_lang.append(language)
            yield ("result", VALID_REPORT_DATA)

        mock_audio = {"audio_base64": "data", "sentences": []}

        with (
            patch("routes.analyze.analyze_with_gemini_agent", side_effect=fake_agent),
            patch("routes.analyze.generate_podcast_script", new_callable=AsyncMock, return_value="Script"),
            patch("routes.analyze.generate_podcast_audio", new_callable=AsyncMock, return_value=mock_audio),
        ):
            client = TestClient(app)
            with client.websocket_connect("/ws/analyze") as ws:
                ws.send_text(_make_upload_msg([("test.csv", b"a,b\n1,2")], language="fr"))
                messages = _collect_ws_messages(ws)

        assert captured_lang == ["fr"]

    def test_agent_error_propagated(self):
        """Agent yielding error is sent to the client."""
        async def fake_agent(text, file_count, session, language="en", **kw):
            yield ("error", "Gemini API is down")

        with patch("routes.analyze.analyze_with_gemini_agent", side_effect=fake_agent):
            client = TestClient(app)
            with client.websocket_connect("/ws/analyze") as ws:
                ws.send_text(_make_upload_msg([("test.csv", b"a,b\n1,2")]))
                messages = _collect_ws_messages(ws)

        error_msg = next(m for m in messages if m["type"] == "error")
        assert "Gemini API is down" in error_msg["message"]

    def test_agent_no_result(self):
        """Agent yields nothing useful → error about no report."""
        async def fake_agent(text, file_count, session, language="en", **kw):
            yield ("thinking", "Hmm...")

        with patch("routes.analyze.analyze_with_gemini_agent", side_effect=fake_agent):
            client = TestClient(app)
            with client.websocket_connect("/ws/analyze") as ws:
                ws.send_text(_make_upload_msg([("test.csv", b"a,b\n1,2")]))
                messages = _collect_ws_messages(ws)

        error_msg = next(m for m in messages if m["type"] == "error")
        assert "failed" in error_msg["message"].lower() or "report" in error_msg["message"].lower()

    def test_thinking_events_forwarded(self):
        """Thinking events from agent are forwarded to client."""
        async def fake_agent(text, file_count, session, language="en", **kw):
            yield ("thinking", "Analyzing data...")
            yield ("thinking", "Looking at categories...")
            yield ("result", VALID_REPORT_DATA)

        mock_audio = {"audio_base64": "data", "sentences": []}

        with (
            patch("routes.analyze.analyze_with_gemini_agent", side_effect=fake_agent),
            patch("routes.analyze.generate_podcast_script", new_callable=AsyncMock, return_value="Script"),
            patch("routes.analyze.generate_podcast_audio", new_callable=AsyncMock, return_value=mock_audio),
        ):
            client = TestClient(app)
            with client.websocket_connect("/ws/analyze") as ws:
                ws.send_text(_make_upload_msg([("test.csv", b"a,b\n1,2")]))
                messages = _collect_ws_messages(ws)

        thinking_msgs = [m for m in messages if m["type"] == "thinking"]
        assert len(thinking_msgs) >= 2
        assert thinking_msgs[0]["text"] == "Analyzing data..."

    def test_tts_failure_fallback(self):
        """If ElevenLabs TTS fails, podcast script is still sent without audio."""
        async def fake_agent(text, file_count, session, language="en", **kw):
            yield ("result", VALID_REPORT_DATA)

        with (
            patch("routes.analyze.analyze_with_gemini_agent", side_effect=fake_agent),
            patch("routes.analyze.generate_podcast_script", new_callable=AsyncMock, return_value="Script text"),
            patch("routes.analyze.generate_podcast_audio", new_callable=AsyncMock, side_effect=Exception("TTS failed")),
        ):
            client = TestClient(app)
            with client.websocket_connect("/ws/analyze") as ws:
                ws.send_text(_make_upload_msg([("test.csv", b"a,b\n1,2")]))
                messages = _collect_ws_messages(ws)

        audio_msg = next(m for m in messages if m["type"] == "podcast_audio_ready")
        assert audio_msg["podcast_script"] == "Script text"
        assert audio_msg["audio_base64"] is None
        assert audio_msg["sentences"] == []

    def test_progress_steps_in_order(self):
        """Progress messages follow parsing → analyzing → generating → narrating order."""
        async def fake_agent(text, file_count, session, language="en", **kw):
            yield ("result", VALID_REPORT_DATA)

        mock_audio = {"audio_base64": "data", "sentences": []}

        with (
            patch("routes.analyze.analyze_with_gemini_agent", side_effect=fake_agent),
            patch("routes.analyze.generate_podcast_script", new_callable=AsyncMock, return_value="Script"),
            patch("routes.analyze.generate_podcast_audio", new_callable=AsyncMock, return_value=mock_audio),
        ):
            client = TestClient(app)
            with client.websocket_connect("/ws/analyze") as ws:
                ws.send_text(_make_upload_msg([("test.csv", b"a,b\n1,2")]))
                messages = _collect_ws_messages(ws)

        progress_steps = [m["step"] for m in messages if m["type"] == "progress"]
        assert "parsing" in progress_steps
        assert "analyzing" in progress_steps
        assert "generating" in progress_steps
        assert "narrating" in progress_steps

        first_parsing = progress_steps.index("parsing")
        first_analyzing = progress_steps.index("analyzing")
        first_generating = progress_steps.index("generating")
        first_narrating = progress_steps.index("narrating")
        assert first_parsing < first_analyzing < first_generating < first_narrating

    def test_document_request_flow(self):
        """Agent requests a document, client skips → agent finishes."""
        async def fake_agent(text, file_count, session, language="en", **kw):
            yield ("request_documents", {"document_type": "pay stub", "reason": "need income"})
            yield ("result", VALID_REPORT_DATA)

        mock_audio = {"audio_base64": "data", "sentences": []}

        def on_doc_request(ws, msg):
            ws.send_text(json.dumps({"type": "skip"}))

        with (
            patch("routes.analyze.analyze_with_gemini_agent", side_effect=fake_agent),
            patch("routes.analyze.generate_podcast_script", new_callable=AsyncMock, return_value="Script"),
            patch("routes.analyze.generate_podcast_audio", new_callable=AsyncMock, return_value=mock_audio),
        ):
            client = TestClient(app)
            with client.websocket_connect("/ws/analyze") as ws:
                ws.send_text(_make_upload_msg([("test.csv", b"a,b\n1,2")]))
                messages = _collect_ws_messages(ws, respond_to={
                    "request_documents": on_doc_request,
                })

        types = [m["type"] for m in messages]
        assert "request_documents" in types
        assert "report_ready" in types

    def test_question_flow(self):
        """Agent asks a question, client answers → agent finishes."""
        async def fake_agent(text, file_count, session, language="en", **kw):
            yield ("ask_question", {"question": "What is your goal?", "options": ["Save", "Budget"]})
            yield ("result", VALID_REPORT_DATA)

        mock_audio = {"audio_base64": "data", "sentences": []}

        def on_question(ws, msg):
            ws.send_text(json.dumps({"type": "answer_question", "answer": "Save"}))

        with (
            patch("routes.analyze.analyze_with_gemini_agent", side_effect=fake_agent),
            patch("routes.analyze.generate_podcast_script", new_callable=AsyncMock, return_value="Script"),
            patch("routes.analyze.generate_podcast_audio", new_callable=AsyncMock, return_value=mock_audio),
        ):
            client = TestClient(app)
            with client.websocket_connect("/ws/analyze") as ws:
                ws.send_text(_make_upload_msg([("test.csv", b"a,b\n1,2")]))
                messages = _collect_ws_messages(ws, respond_to={
                    "ask_question": on_question,
                })

        types = [m["type"] for m in messages]
        assert "ask_question" in types
        assert "report_ready" in types

        q_msg = next(m for m in messages if m["type"] == "ask_question")
        assert q_msg["question"] == "What is your goal?"
        assert q_msg["options"] == ["Save", "Budget"]
