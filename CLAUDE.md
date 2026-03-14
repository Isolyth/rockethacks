# Easy MonAI

AI-powered financial analysis app that parses bank statements (PDF/CSV) and generates reports + podcast narration.

## Tech Stack

- **Frontend:** SvelteKit 2, Svelte 5 (runes), TypeScript, Vite 7
- **Backend:** Python 3.12, FastAPI, Uvicorn
- **AI:** Google Gemini API (`gemini-flash-latest`) with extended thinking + function calling
- **TTS:** ElevenLabs API (`eleven_flash_v2_5`, voice: George)
- **Auth:** AWS Cognito (optional - app works in guest mode without it)
- **Storage:** AWS DynamoDB + S3 (optional - for authenticated user persistence)
- **Communication:** WebSocket (`/ws/analyze`) + HTTP REST (auth, dashboard, follow-up SSE)

## Project Structure

```
rockethacks/
├── backend/
│   ├── main.py           # App entry, CORS, security headers, lifespan
│   ├── config.py         # Centralized env vars and defaults
│   ├── routes/           # analyze.py (WS + follow-up), auth.py, dashboard.py
│   ├── services/         # gemini, parser, elevenlabs_tts, session, auth, dynamo, storage, encryption, rate_limit
│   ├── models/           # Pydantic schemas
│   └── tests/            # pytest tests
├── frontend/
│   └── src/
│       ├── routes/       # /, /login, /signup, /analyze, /dashboard, /dashboard/report/[id]
│       └── lib/          # Components, API client, types, stores, utils
├── docs/                 # Project documentation
├── docker-compose.yml    # backend, frontend, nginx, certbot
└── .github/workflows/    # deploy.yml (auto-deploy via SSH)
```

## Running the App

```sh
# Backend (terminal 1)
cd backend && source venv/bin/activate && uvicorn main:app --reload

# Frontend (terminal 2)
cd frontend && npm run dev
```

Backend: http://localhost:8000 | Frontend: http://localhost:5173

## Environment Variables

Backend `.env`:

**Required:**
- `GEMINI_API_KEY` - Google AI Studio API key

**Optional:**
- `ELEVENLABS_API_KEY` - ElevenLabs API key (falls back to script-only without it)

**AWS / Auth (required for user accounts & persistence, not needed for guest mode):**
- `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION`
- `AWS_S3_BUCKET` - S3 bucket for statements and audio
- `COGNITO_USER_POOL_ID`, `COGNITO_CLIENT_ID`, `COGNITO_CLIENT_SECRET`
- `DYNAMO_REPORTS_TABLE`, `DYNAMO_STATEMENTS_TABLE`, `DYNAMO_USER_SALTS_TABLE`
- `CORS_ORIGINS` - Comma-separated allowed origins (default: `http://localhost:5173`)

See `backend/config.py` for all env vars with defaults.

## Key Commands

- `cd backend && pytest` - Run backend tests
- `cd frontend && npm run check` - TypeScript/Svelte type checking
- `cd frontend && npm run build` - Production build
- `docker compose up -d --build` - Production Docker deployment

## Architecture Notes

- WebSocket connection handles the analysis flow (upload -> parse -> analyze -> podcast -> audio)
- Gemini agent uses an agentic loop with 4 tools: `request_documents`, `ask_question`, `finish`, `search_web`
- Agent must interact at least twice (questions/doc requests) before finishing
- Max 3 agent interactions (configurable via `MAX_DOCUMENT_REQUESTS` env var)
- `search_web` triggers a separate Gemini API call with GoogleSearch (workaround for API limitation)
- Follow-up chat via HTTP POST `/analyze/follow-up` with SSE streaming
- ElevenLabs TTS generates audio with character-level timestamps, mapped to sentence-level for sync highlighting
- If TTS fails, falls back to script-only mode (no audio)
- AWS Cognito authentication (signup/login/token validation); optional - app works in guest mode without AWS
- DynamoDB stores reports, statements, user salts; S3 stores files and audio; tables auto-created on startup
- AES-256-GCM encryption for stored statements using password-derived keys (PBKDF2)
- Rate limiting on auth endpoints, WS connections, and follow-up; failed login lockout after 6 attempts
- Security headers middleware (X-Content-Type-Options, X-Frame-Options, Referrer-Policy, Permissions-Policy)
- Frontend uses Svelte 5 runes (`$state`, `$derived`, `$effect`) for reactivity
- 14 languages supported (en, es, fr, de, pt, it, ja, ko, zh, hi, ar, nl, pl, ru)
- CORS configurable via `CORS_ORIGINS` env var (comma-separated)

## Conventions

- Backend uses `uvicorn.error` logger throughout
- All configuration centralized in `backend/config.py`
- Pydantic models in `backend/models/schemas.py` mirror TypeScript interfaces in `frontend/src/lib/types.ts`
- WebSocket messages use `{ type: "...", ...payload }` format
- Files transmitted as base64 over WebSocket
- In-memory sessions; authenticated users get reports/statements persisted to DynamoDB/S3
