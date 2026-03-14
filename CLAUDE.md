# Easy monAI

AI-powered financial analysis app that parses bank statements (PDF/CSV) and generates reports + podcast narration.

## Tech Stack

- **Frontend:** SvelteKit 2, Svelte 5 (runes), TypeScript, Vite 7
- **Backend:** Python 3.12, FastAPI, Uvicorn
- **AI:** Google Gemini API (`gemini-2.5-flash`) with extended thinking + function calling
- **TTS:** ElevenLabs API (`eleven_flash_v2_5`, voice: George)
- **Communication:** WebSocket (single endpoint: `/ws/analyze`)

## Project Structure

```
rockethacks/
├── backend/          # Python FastAPI server
│   ├── main.py       # App entry, CORS config
│   ├── routes/       # WebSocket endpoint (analyze.py)
│   ├── services/     # Gemini AI, parser, ElevenLabs TTS, sessions
│   ├── models/       # Pydantic schemas
│   └── tests/        # pytest tests
├── frontend/         # SvelteKit app
│   └── src/
│       ├── routes/   # Pages (+page.svelte, +layout.svelte)
│       └── lib/      # Components, API client, types
└── docs/             # Project documentation
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

Backend `.env` requires:
- `GEMINI_API_KEY` - Google AI Studio API key
- `ELEVENLABS_API_KEY` - ElevenLabs API key

## Key Commands

- `cd backend && pytest` - Run backend tests
- `cd frontend && npm run check` - TypeScript/Svelte type checking
- `cd frontend && npm run build` - Production build

## Architecture Notes

- Single WebSocket connection handles the entire analysis flow (upload -> parse -> analyze -> podcast -> audio)
- Gemini agent uses an agentic loop with 3 tools: `request_documents`, `ask_question`, `finish`
- Agent must interact at least twice (questions/doc requests) before finishing
- Max 3 agent interactions (configurable via `MAX_DOCUMENT_REQUESTS` env var)
- ElevenLabs TTS generates audio with character-level timestamps, mapped to sentence-level for sync highlighting
- If TTS fails, falls back to script-only mode (no audio)
- Frontend uses Svelte 5 runes (`$state`, `$derived`, `$effect`) for reactivity
- 14 languages supported (en, es, fr, de, pt, it, ja, ko, zh, hi, ar, nl, pl, ru)
- CORS currently allows only localhost:5173 - must update for production

## Conventions

- Backend uses `uvicorn.error` logger throughout
- Pydantic models in `backend/models/schemas.py` mirror TypeScript interfaces in `frontend/src/lib/types.ts`
- WebSocket messages use `{ type: "...", ...payload }` format
- Files transmitted as base64 over WebSocket
- No database - all state is in-memory per session
