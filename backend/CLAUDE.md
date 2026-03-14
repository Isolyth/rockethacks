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

- `main.py` - FastAPI app, CORS middleware (configurable via `CORS_ORIGINS`), security headers middleware, DynamoDB table creation on startup via lifespan hook
- `config.py` - Centralized configuration: all env vars with defaults
- `routes/analyze.py` - WebSocket `/ws/analyze` endpoint + HTTP POST `/analyze/follow-up` (SSE streaming), orchestrates the full pipeline
- `routes/auth.py` - `POST /auth/signup`, `POST /auth/login`, `GET /auth/me` (Cognito)
- `routes/dashboard.py` - `GET/DELETE /dashboard/reports[/{id}]`, `GET/DELETE /dashboard/statements[/{id}]`
- `services/gemini.py` - Gemini agent with 4-tool agentic loop (`request_documents`, `ask_question`, `finish`, `search_web`) + podcast script generation + follow-up chat
- `services/parser.py` - PDF (pypdf) and CSV parsing
- `services/elevenlabs_tts.py` - TTS with sentence-level timestamp alignment
- `services/session.py` - In-memory session (dataclass: session_id, language, user_response, active, user_id, encryption_key)
- `services/auth.py` - Cognito signup/login/token validation + PBKDF2 key derivation for encryption
- `services/dynamo.py` - DynamoDB CRUD for reports, statements, user salts; auto-creates tables on startup
- `services/storage.py` - S3 upload/download for statements and audio; presigned URLs
- `services/encryption.py` - AES-256-GCM encrypt/decrypt for statement files
- `services/rate_limit.py` - RateLimiter (token-bucket), FailedLoginLimiter, WS connection tracking per IP
- `models/schemas.py` - Pydantic models: FinancialReport, CategoryBreakdown, GroundingData, auth models (SignupRequest, LoginRequest, AuthResponse), dashboard models (ReportSummaryItem, ReportDetail, StatementItem), follow-up models (ChatMessage, FollowUpRequest)
- `tests/` - test_analyze, test_parser, test_schemas, test_session, test_elevenlabs_tts, test_gemini, test_main
- `scripts/test_elevenlabs_tts.py` - Standalone CLI script for testing ElevenLabs TTS

## Key Patterns

- Gemini streaming runs in a background thread via `_stream_via_thread()` to avoid blocking the event loop; it accumulates non-thought parts across chunks to prevent function calls from being lost
- Agent loop uses Python async generators to yield events back to the route handler
- Session's `user_response` field is set by the route handler between generator yields (cooperative coroutine pattern)
- `string.Template.safe_substitute()` used for prompt templating (not f-strings)
- **Google Search workaround**: `google_search` (GoogleSearch tool) cannot be combined with `function_declarations` in the same Gemini API request. Instead, `search_web` is declared as a regular function the agent can call, and `_do_grounded_search()` makes a separate API call with only GoogleSearch enabled. Grounding metadata (sources, citations) is accumulated across iterations and attached to the final report.
- Follow-up chat uses `generate_followup_chat_stream` (async generator yielding SSE chunks) + `generate_followup_podcast_script`
- AWS services degrade gracefully - if AWS creds not configured, runs in guest-only mode (no persistence)
- Rate limiting: auth 10 req/60s per IP, login lockout 6 failures/360s per email, WS 5 connections/IP, follow-up 20 req/60s per IP
- Filename sanitization strips path traversal and non-alphanumeric characters; file size limit 10MB; max 10 files per upload; text truncated at 500K chars
