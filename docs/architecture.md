# Architecture

## Overview

Easy MonAI is a multi-tier application with a SvelteKit frontend, FastAPI backend, and AWS services for persistence.

```
┌──────────────┐  WebSocket + HTTP  ┌──────────────┐
│   SvelteKit  │ ◄────────────────► │   FastAPI     │
│   Frontend   │  /ws/analyze       │   Backend     │
│  :5173       │  /auth/*           │  :8000        │
│              │  /dashboard/*      │               │
│              │  /analyze/follow-up│               │
└──────────────┘                    └──────┬────────┘
                                           │
                        ┌──────────────────┼──────────────────┐
                        │          │       │       │          │
                   ┌────▼───┐ ┌────▼──┐ ┌──▼───┐ ┌▼───────┐ ┌▼────────┐
                   │ Gemini │ │ pypdf │ │Eleven│ │Cognito │ │DynamoDB │
                   │  API   │ │Parser │ │ Labs │ │ Auth   │ │  + S3   │
                   └────────┘ └───────┘ └──────┘ └────────┘ └─────────┘
```

## Data Flow

### Analysis Pipeline

1. **File Upload** - User drops PDF/CSV files in the browser
2. **Base64 Encoding** - Frontend converts files to base64, sends over WebSocket
3. **Parsing** - Backend extracts text using pypdf (PDF) or UTF-8 decode (CSV)
4. **Agentic Analysis** - Gemini agent analyzes data in a multi-turn loop:
   - Agent can request additional documents (user uploads more files)
   - Agent can ask multiple-choice questions (user selects an answer)
   - Agent can search the web for context (GoogleSearch grounding)
   - Agent must interact at least 2 times before calling `finish`
   - Max 3 interactions (configurable)
5. **Report Generation** - Agent returns structured FinancialReport JSON with grounding data
6. **Podcast Script** - Separate Gemini call generates a spoken monologue script
7. **TTS Audio** - ElevenLabs converts script to MP3 with character-level timestamps
8. **Sentence Alignment** - Character timestamps mapped to sentence boundaries
9. **Delivery** - Report, script, and base64 audio sent to frontend
10. **Persistence** - For authenticated users, report saved to DynamoDB, audio to S3, statements encrypted and stored

### WebSocket Message Types

**Client -> Server:**
| Type | Fields | When |
|------|--------|------|
| `upload_files` | `files: [{name, content}], language, token?, enc_key?` | Initial upload or additional docs |
| `use_saved_statements` | `statement_ids[], files?, language, token, enc_key` | Re-analyzing saved statements |
| `skip` | -- | User skips document request |
| `answer` | `answer: string` | User answers agent question |

**Server -> Client:**
| Type | Fields | When |
|------|--------|------|
| `progress` | `step, message, percent` | Pipeline step updates |
| `thinking` | `text` | Gemini extended thinking chunks |
| `request_documents` | `document_type, reason` | Agent needs more docs |
| `ask_question` | `question, options[]` | Agent asks clarifying question |
| `report_ready` | `report: FinancialReport` | Report generated (sent early) |
| `podcast_audio_ready` | `podcast_script, audio_base64, sentences[], report_id?` | Final result |
| `error` | `message` | Any failure |

## Agentic Loop

The Gemini agent uses function calling with four tools:

```
┌─────────────┐
│ Start       │
└──────┬──────┘
       │
       ▼
┌──────────────┐    request_documents    ┌───────────────┐
│  Gemini      │ ──────────────────────► │ User uploads   │
│  Thinks +    │ ◄────────────────────── │ or skips       │
│  Calls Tool  │                         └───────────────┘
│              │    ask_question          ┌───────────────┐
│              │ ──────────────────────► │ User answers    │
│              │ ◄────────────────────── │ question        │
│              │                         └───────────────┘
│              │    search_web           ┌───────────────┐
│              │ ──────────────────────► │ GoogleSearch    │
│              │ ◄────────────────────── │ (separate call) │
└──────┬───────┘                         └───────────────┘
       │ finish
       ▼
┌──────────────┐
│ Report JSON  │
│ + Grounding  │
└──────────────┘
```

- Agent loop runs as a Python async generator
- Each yield pauses execution, returns control to the route handler
- Route handler forwards the event to the client via WebSocket
- Client response is written to `session.user_response` before resuming the generator
- Gemini streaming runs in a background thread to avoid blocking asyncio
- `search_web` triggers a separate Gemini API call with GoogleSearch enabled (workaround: GoogleSearch cannot coexist with function_declarations)

## Authentication Flow

1. User signs up or logs in via `/auth/signup`, `/auth/login` (Cognito)
2. Server derives an encryption key from the password via PBKDF2 + per-user salt (stored in DynamoDB)
3. Server returns JWT token + base64 encryption key
4. Frontend stores token in localStorage, encryption key in sessionStorage (lost on tab close)
5. WebSocket initial message includes token + encryption key in the message body
6. Uploaded statements are encrypted with AES-256-GCM before S3 upload
7. On retrieval, statements are decrypted with the same key

## Follow-up Chat

- HTTP POST `/analyze/follow-up` with SSE streaming
- Client sends the original report, a prompt, chat history, and language
- Gemini generates a streaming response, then a follow-up podcast script
- SSE events: `chunk` (incremental text), `done` (full text + podcast script), `error`

## Frontend State Machine

```
idle ──► processing ──► done
              │    ▲
              ▼    │
    awaiting_documents
              │    ▲
              ▼    │
     awaiting_answer
              │
              ▼
            error
```

## Session Management

- Each WebSocket connection gets a unique session ID
- Sessions are stored in-memory (`dict[str, Session]`)
- Session holds: `session_id`, `language`, `user_response`, `active`, `user_id`, `encryption_key`
- Session is cleaned up when WebSocket disconnects
- In-memory only; for authenticated users, reports and statements are persisted to DynamoDB/S3

## Security

- Rate limiting: auth 10 req/60s per IP, follow-up 20 req/60s per IP, login lockout 6 failures/360s per email
- Per-IP WebSocket connection limit (5 concurrent)
- Security headers: X-Content-Type-Options, X-Frame-Options, Referrer-Policy, Permissions-Policy
- File size limit (10MB), file count limit (10), text truncation (500K chars)
- Filename sanitization (path traversal prevention)
- AES-256-GCM encryption for stored statements with password-derived keys
