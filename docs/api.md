# API Reference

## HTTP Endpoints

### Auth

| Method | Path | Body | Auth | Response |
|--------|------|------|------|----------|
| POST | `/auth/signup` | `{email, password, display_name?}` | No | `AuthResponse` |
| POST | `/auth/login` | `{email, password}` | No | `AuthResponse` |
| GET | `/auth/me` | -- | Bearer token | `UserResponse` |

### Dashboard

| Method | Path | Auth | Response |
|--------|------|------|----------|
| GET | `/dashboard/reports` | Bearer token | `ReportSummaryItem[]` |
| GET | `/dashboard/reports/{id}` | Bearer token | `ReportDetail` |
| DELETE | `/dashboard/reports/{id}` | Bearer token | `{ok: true}` |
| GET | `/dashboard/statements` | Bearer token | `StatementItem[]` |
| DELETE | `/dashboard/statements/{id}` | Bearer token | `{ok: true}` |

### Follow-up Chat

| Method | Path | Body | Response |
|--------|------|------|----------|
| POST | `/analyze/follow-up` | `FollowUpRequest` | SSE stream |

SSE events:
```json
{"type": "chunk", "text": "..."}
{"type": "done", "full_text": "...", "podcast_script": "..."}
{"type": "error", "message": "..."}
```

---

## WebSocket Endpoint

```
ws://localhost:8000/ws/analyze
```

Single WebSocket endpoint that handles the entire analysis flow.

## Protocol

All messages are JSON strings sent via `ws.send()` / `ws.onmessage`.

## Client Messages

### `upload_files` (initial)

Sent immediately after connection opens.

```json
{
  "type": "upload_files",
  "files": [
    {
      "name": "statement.pdf",
      "content": "<base64-encoded file bytes>"
    }
  ],
  "language": "en",
  "token": "<optional JWT for authenticated users>",
  "enc_key": "<optional base64 encryption key>"
}
```

- `files` - Array of files, each with `name` (string) and `content` (base64 string)
- `language` - ISO 639-1 code. Supported: `en`, `es`, `fr`, `de`, `pt`, `it`, `ja`, `ko`, `zh`, `hi`, `ar`, `nl`, `pl`, `ru`
- `token` - Optional Cognito JWT for authenticated sessions
- `enc_key` - Optional base64 encryption key for statement storage
- Supported file types: `.pdf`, `.csv`
- Auth credentials go in the message body (not query params) to avoid server log exposure

### `use_saved_statements`

Sent to re-analyze previously saved statements (requires authentication).

```json
{
  "type": "use_saved_statements",
  "statement_ids": ["id1", "id2"],
  "files": [],
  "language": "en",
  "token": "...",
  "enc_key": "..."
}
```

- `statement_ids` - Array of saved statement IDs to retrieve from S3
- `files` - Optional array of additional new files to include

### `upload_files` (additional documents)

Sent in response to a `request_documents` server message.

```json
{
  "type": "upload_files",
  "files": [
    {
      "name": "payslip.pdf",
      "content": "<base64>"
    }
  ]
}
```

### `skip`

Sent when user declines a document request.

```json
{
  "type": "skip"
}
```

### `answer`

Sent in response to an `ask_question` server message.

```json
{
  "type": "answer",
  "answer": "I'm salaried, paid monthly"
}
```

## Server Messages

### `progress`

Sent throughout the pipeline to indicate progress.

```json
{
  "type": "progress",
  "step": "parsing",
  "message": "Extracting text from uploaded files...",
  "percent": 10
}
```

Steps in order: `parsing` (10-25%) -> `analyzing` (40-70%) -> `generating` (60-70%) -> `narrating` (80-95%)

### `thinking`

Gemini extended thinking chunks, streamed in real-time.

```json
{
  "type": "thinking",
  "text": "Looking at the transaction data, I can see..."
}
```

### `request_documents`

Agent is requesting additional documents.

```json
{
  "type": "request_documents",
  "document_type": "pay stub or income statement",
  "reason": "I see expenses but no income deposits. Having your pay stubs would help calculate your savings rate."
}
```

Client should respond with either `upload_files` or `skip`.

### `ask_question`

Agent is asking the user a multiple-choice question.

```json
{
  "type": "ask_question",
  "question": "What are you most interested in improving?",
  "options": [
    "Reducing monthly expenses",
    "Increasing savings rate",
    "Better budgeting by category"
  ]
}
```

Client should respond with `answer`. The frontend adds an "Other" option automatically.

### `report_ready`

Financial report is ready (sent before podcast generation).

```json
{
  "type": "report_ready",
  "report": {
    "summary": {
      "total_income": 5000.00,
      "total_expenses": 3500.00,
      "net_savings": 1500.00,
      "date_range": "2024-01 to 2024-03"
    },
    "categories": [
      {
        "name": "Food & Dining",
        "total": 800.00,
        "percentage": 22.86,
        "transactions": 45
      }
    ],
    "top_merchants": [
      {
        "name": "Amazon",
        "total": 450.00,
        "count": 12
      }
    ],
    "insights": [
      "Your savings rate is 30%, which is above the recommended 20%."
    ],
    "monthly_trend": [
      {
        "month": "2024-01",
        "income": 5000.00,
        "expenses": 3200.00
      }
    ],
    "grounding": {
      "sources": [{"uri": "...", "title": "...", "domain": "..."}],
      "citations": [{"text_segment": "...", "source_indices": [0]}],
      "search_entry_point_html": "..."
    }
  }
}
```

### `podcast_audio_ready`

Final result with podcast script and optional audio.

```json
{
  "type": "podcast_audio_ready",
  "podcast_script": "Hey there! Let's dive into your finances...",
  "audio_base64": "<base64-encoded MP3 or null>",
  "sentences": [
    {
      "text": "Hey there!",
      "start": 0.0,
      "end": 0.85
    },
    {
      "text": "Let's dive into your finances...",
      "start": 0.85,
      "end": 2.1
    }
  ],
  "report_id": "<optional, present for authenticated users>"
}
```

- `audio_base64` is `null` if ElevenLabs TTS fails (fallback to script-only mode)
- `sentences` contains timing data for synchronized highlighting during playback
- `report_id` is included for authenticated users so the frontend can link to the saved report

### `error`

```json
{
  "type": "error",
  "message": "Unsupported file type: document.docx. Please upload PDF or CSV files."
}
```

## Connection Lifecycle

1. Client opens WebSocket to `/ws/analyze`
2. Server enforces per-IP connection limit (max 5), accepts, creates session
3. Client sends `upload_files` or `use_saved_statements` with initial data
4. Server validates auth token if provided
5. Server streams `progress`, `thinking`, `request_documents`, `ask_question` messages
6. Client responds to agent interactions as needed
7. Server sends `report_ready` (report available to display)
8. Server sends `podcast_audio_ready` (final result)
9. For authenticated users, report and statements are saved to DynamoDB/S3
10. Connection closes

## Error Handling

- Unsupported file types return an `error` message and close
- Gemini failures return an `error` message
- ElevenLabs TTS failures fall back to script-only (no error to client)
- WebSocket disconnects are logged and session is cleaned up
- Per-IP WebSocket connection limit exceeded: close code 4029
- Invalid/expired auth token: error message and close code 4001
- File size (10MB) and file count (10) limits enforced; violations return error message
- Analysis timeout (default 300s) returns error message
