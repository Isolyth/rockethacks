# Backend

Python 3.12 + FastAPI backend.

## Setup

```sh
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # then fill in API keys
uvicorn main:app --reload
```

## Testing

```sh
pytest                    # run all tests
pytest tests/test_parser.py  # specific test file
```

181 tests across 7 test files. Uses FastAPI's TestClient with mocks for Gemini and ElevenLabs. Shared fixtures in `tests/conftest.py`.

## Structure

- `main.py` - FastAPI app, CORS middleware (allows localhost:5173)
- `routes/analyze.py` - WebSocket `/ws/analyze` endpoint, orchestrates the full pipeline
- `services/gemini.py` - Gemini agent with agentic tool loop + podcast script generation
- `services/parser.py` - PDF (pypdf) and CSV parsing
- `services/elevenlabs_tts.py` - TTS with sentence-level timestamp alignment
- `services/session.py` - In-memory session management (dataclass + dict)
- `models/schemas.py` - Pydantic models: FinancialReport, CategoryBreakdown, GroundingData, etc.
- `tests/` - test_analyze, test_parser, test_schemas, test_session, test_elevenlabs_tts, test_gemini, test_main
- `scripts/test_elevenlabs_tts.py` - Standalone CLI script for testing ElevenLabs TTS

## Key Patterns

- Gemini streaming runs in a background thread via `_stream_via_thread()` to avoid blocking the event loop; it accumulates non-thought parts across chunks to prevent function calls from being lost
- Agent loop uses Python async generators to yield events back to the route handler
- Session's `user_response` field is set by the route handler between generator yields (cooperative coroutine pattern)
- `string.Template.safe_substitute()` used for prompt templating (not f-strings)
- **Google Search workaround**: `google_search` (GoogleSearch tool) cannot be combined with `function_declarations` in the same Gemini API request. Instead, `search_web` is declared as a regular function the agent can call, and `_do_grounded_search()` makes a separate API call with only GoogleSearch enabled. Grounding metadata (sources, citations) is accumulated across iterations and attached to the final report.
