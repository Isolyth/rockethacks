# Architecture

## Overview

Easy monAI is a two-tier application with a SvelteKit frontend and a FastAPI backend communicating over a single WebSocket connection.

```
┌──────────────┐    WebSocket     ┌──────────────┐
│   SvelteKit  │ ◄──────────────► │   FastAPI     │
│   Frontend   │  /ws/analyze     │   Backend     │
│  :5173       │                  │  :8000        │
└──────────────┘                  └──────┬────────┘
                                         │
                              ┌──────────┼──────────┐
                              │          │          │
                         ┌────▼───┐ ┌────▼───┐ ┌───▼────┐
                         │ Gemini │ │ pypdf  │ │Eleven  │
                         │  API   │ │ Parser │ │ Labs   │
                         └────────┘ └────────┘ └────────┘
```

## Data Flow

### Analysis Pipeline

1. **File Upload** - User drops PDF/CSV files in the browser
2. **Base64 Encoding** - Frontend converts files to base64, sends over WebSocket
3. **Parsing** - Backend extracts text using pypdf (PDF) or UTF-8 decode (CSV)
4. **Agentic Analysis** - Gemini agent analyzes data in a multi-turn loop:
   - Agent can request additional documents (user uploads more files)
   - Agent can ask multiple-choice questions (user selects an answer)
   - Agent must interact at least 2 times before calling `finish`
   - Max 3 interactions (configurable)
5. **Report Generation** - Agent returns structured FinancialReport JSON
6. **Podcast Script** - Separate Gemini call generates a spoken monologue script
7. **TTS Audio** - ElevenLabs converts script to MP3 with character-level timestamps
8. **Sentence Alignment** - Character timestamps mapped to sentence boundaries
9. **Delivery** - Report, script, and base64 audio sent to frontend

### WebSocket Message Types

**Client -> Server:**
| Type | Fields | When |
|------|--------|------|
| `upload_files` | `files: [{name, content}], language` | Initial upload or additional docs |
| `skip` | — | User skips document request |
| `answer_question` | `answer: string` | User answers agent question |

**Server -> Client:**
| Type | Fields | When |
|------|--------|------|
| `progress` | `step, message, percent` | Pipeline step updates |
| `thinking` | `text` | Gemini extended thinking chunks |
| `request_documents` | `document_type, reason` | Agent needs more docs |
| `ask_question` | `question, options[]` | Agent asks clarifying question |
| `report_ready` | `report: FinancialReport` | Report generated (sent early) |
| `podcast_audio_ready` | `podcast_script, audio_base64, sentences[]` | Final result |
| `error` | `message` | Any failure |

## Agentic Loop

The Gemini agent uses function calling with three tools:

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
└──────┬───────┘                         └───────────────┘
       │ finish
       ▼
┌──────────────┐
│ Report JSON  │
└──────────────┘
```

- Agent loop runs as a Python async generator
- Each yield pauses execution, returns control to the route handler
- Route handler forwards the event to the client via WebSocket
- Client response is written to `session.user_response` before resuming the generator
- Gemini streaming runs in a background thread to avoid blocking asyncio

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
- Session holds: `session_id`, `language`, `user_response`, `active` flag
- Session is cleaned up when WebSocket disconnects
- No persistence across server restarts
