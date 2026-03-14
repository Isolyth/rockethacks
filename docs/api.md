# WebSocket API Reference

## Endpoint

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
  "language": "en"
}
```

- `files` - Array of files, each with `name` (string) and `content` (base64 string)
- `language` - ISO 639-1 code. Supported: `en`, `es`, `fr`, `de`, `pt`, `it`, `ja`, `ko`, `zh`, `hi`, `ar`, `nl`, `pl`, `ru`
- Supported file types: `.pdf`, `.csv`

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

### `answer_question`

Sent in response to an `ask_question` server message.

```json
{
  "type": "answer_question",
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

Client should respond with `answer_question`. The frontend adds an "Other" option automatically.

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
    ]
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
  ]
}
```

- `audio_base64` is `null` if ElevenLabs TTS fails (fallback to script-only mode)
- `sentences` contains timing data for synchronized highlighting during playback

### `error`

```json
{
  "type": "error",
  "message": "Unsupported file type: document.docx. Please upload PDF or CSV files."
}
```

## Connection Lifecycle

1. Client opens WebSocket to `/ws/analyze`
2. Server accepts, creates session
3. Client sends `upload_files` with initial files
4. Server streams `progress`, `thinking`, `request_documents`, `ask_question` messages
5. Client responds to agent interactions as needed
6. Server sends `report_ready` (report available to display)
7. Server sends `podcast_audio_ready` (final result)
8. Connection closes

## Error Handling

- Unsupported file types return an `error` message and close
- Gemini failures return an `error` message
- ElevenLabs TTS failures fall back to script-only (no error to client)
- WebSocket disconnects are logged and session is cleaned up
