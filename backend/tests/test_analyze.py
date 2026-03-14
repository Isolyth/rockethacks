import json
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from main import app

MOCK_REPORT = {
    "summary": {
        "total_income": 5000.0,
        "total_expenses": 3200.0,
        "net_savings": 1800.0,
        "date_range": "2024-01-01 to 2024-01-31",
    },
    "categories": [
        {"name": "Food & Dining", "total": 800.0, "percentage": 25.0, "transactions": 15},
    ],
    "top_merchants": [
        {"name": "Starbucks", "total": 120.0, "count": 10},
    ],
    "insights": ["You spend 25% on food"],
    "monthly_trend": [
        {"month": "2024-01", "income": 5000.0, "expenses": 3200.0},
    ],
}

MOCK_PODCAST = "Welcome to your financial podcast! Let's dive into your spending."


def parse_sse_events(raw: str) -> list[dict]:
    """Parse raw SSE text into a list of {event, data} dicts."""
    events = []
    # Normalize line endings
    raw = raw.replace("\r\n", "\n").replace("\r", "\n")
    for block in raw.split("\n\n"):
        if not block.strip():
            continue
        event_type = ""
        data_lines = []
        for line in block.split("\n"):
            if line.startswith("event:"):
                event_type = line[6:].strip()
            elif line.startswith("data:"):
                data_lines.append(line[5:])
            # Skip comment lines (: ping, etc.)
        if data_lines:
            data_str = "\n".join(data_lines).strip()
            try:
                data = json.loads(data_str)
            except json.JSONDecodeError:
                data = data_str
            events.append({"event": event_type, "data": data})
    return events


@patch("routes.analyze.generate_podcast_script", new_callable=AsyncMock, return_value=MOCK_PODCAST)
@patch("routes.analyze.analyze_with_gemini", new_callable=AsyncMock, return_value=MOCK_REPORT)
def test_analyze_csv_success(mock_gemini, mock_podcast):
    client = TestClient(app)
    csv_content = b"date,amount,description\n2024-01-01,50.00,Coffee"

    with client.stream("POST", "/analyze", files=[("files", ("test.csv", csv_content, "text/csv"))]) as resp:
        assert resp.status_code == 200
        assert "text/event-stream" in resp.headers["content-type"]
        raw = resp.read().decode()

    events = parse_sse_events(raw)
    event_types = [e["event"] for e in events]

    # Must have progress events for each step and a final result
    assert "progress" in event_types
    assert "result" in event_types

    # Check progress steps appear in order
    progress_steps = [e["data"]["step"] for e in events if e["event"] == "progress"]
    assert "parsing" in progress_steps
    assert "analyzing" in progress_steps
    assert "generating" in progress_steps
    assert progress_steps.index("parsing") < progress_steps.index("analyzing") < progress_steps.index("generating")

    # Check result event has expected fields
    result_event = [e for e in events if e["event"] == "result"][0]
    assert "report" in result_event["data"]
    assert "podcast_script" in result_event["data"]
    assert result_event["data"]["podcast_script"] == MOCK_PODCAST


@patch("routes.analyze.generate_podcast_script", new_callable=AsyncMock, return_value=MOCK_PODCAST)
@patch("routes.analyze.analyze_with_gemini", new_callable=AsyncMock, return_value=MOCK_REPORT)
def test_analyze_multiple_files(mock_gemini, mock_podcast):
    client = TestClient(app)
    files = [
        ("files", ("stmt1.csv", b"date,amount\n2024-01-01,50", "text/csv")),
        ("files", ("stmt2.csv", b"date,amount\n2024-02-01,75", "text/csv")),
    ]

    with client.stream("POST", "/analyze", files=files) as resp:
        raw = resp.read().decode()

    events = parse_sse_events(raw)
    result_events = [e for e in events if e["event"] == "result"]
    assert len(result_events) == 1

    # Gemini should have been called with text from both files
    call_text = mock_gemini.call_args[0][0]
    assert "stmt1.csv" in call_text
    assert "stmt2.csv" in call_text


def test_analyze_unsupported_file_type():
    client = TestClient(app)

    with client.stream("POST", "/analyze", files=[("files", ("test.txt", b"hello", "text/plain"))]) as resp:
        raw = resp.read().decode()

    events = parse_sse_events(raw)
    error_events = [e for e in events if e["event"] == "error"]
    assert len(error_events) == 1
    assert "Unsupported file type" in error_events[0]["data"]["message"]


@patch("routes.analyze.analyze_with_gemini", new_callable=AsyncMock, side_effect=Exception("Gemini API error"))
def test_analyze_gemini_failure(mock_gemini):
    client = TestClient(app)

    with client.stream("POST", "/analyze", files=[("files", ("test.csv", b"date,amount\n2024-01-01,50", "text/csv"))]) as resp:
        raw = resp.read().decode()

    events = parse_sse_events(raw)
    error_events = [e for e in events if e["event"] == "error"]
    assert len(error_events) == 1
    assert "Gemini API error" in error_events[0]["data"]["message"]


def test_sse_wire_format():
    """Verify the raw SSE format uses proper event: and data: prefixes with \\n separator."""
    client = TestClient(app)

    with (
        patch("routes.analyze.analyze_with_gemini", new_callable=AsyncMock, return_value=MOCK_REPORT),
        patch("routes.analyze.generate_podcast_script", new_callable=AsyncMock, return_value=MOCK_PODCAST),
    ):
        with client.stream("POST", "/analyze", files=[("files", ("test.csv", b"a,b\n1,2", "text/csv"))]) as resp:
            raw = resp.read().decode()

    # Every event block should have event: and data: lines
    raw_normalized = raw.replace("\r\n", "\n").replace("\r", "\n")
    blocks = [b for b in raw_normalized.split("\n\n") if b.strip()]
    for block in blocks:
        lines = block.strip().split("\n")
        has_event = any(l.startswith("event:") for l in lines)
        has_data = any(l.startswith("data:") for l in lines)
        assert has_event, f"Block missing event: prefix: {block!r}"
        assert has_data, f"Block missing data: prefix: {block!r}"
