# Data Models

Backend models (Pydantic) and frontend interfaces (TypeScript) are kept in sync manually.

## Backend: `backend/models/schemas.py`

## Frontend: `frontend/src/lib/types.ts`

---

## Financial Models

### FinancialReport

Top-level report returned by the Gemini agent.

| Field | Type | Description |
|-------|------|-------------|
| `summary` | `FinancialSummary` | Income, expenses, savings overview |
| `categories` | `CategoryBreakdown[]` | Spending by category |
| `top_merchants` | `MerchantSummary[]` | Highest-spend merchants |
| `insights` | `string[]` | AI-generated financial insights |
| `monthly_trend` | `MonthlyTrend[]` | Month-by-month income vs expenses |
| `grounding` | `GroundingData?` | Web search sources and citations (null if no search) |

### FinancialSummary

| Field | Type | Description |
|-------|------|-------------|
| `total_income` | `float` | Total income in the period |
| `total_expenses` | `float` | Total expenses in the period |
| `net_savings` | `float` | Income minus expenses |
| `date_range` | `string` | e.g. "2024-01 to 2024-03" |

### CategoryBreakdown

| Field | Type | Description |
|-------|------|-------------|
| `name` | `string` | Category name (e.g. "Food & Dining") |
| `total` | `float` | Total spend in category |
| `percentage` | `float` | Percentage of total expenses |
| `transactions` | `int` | Number of transactions |

### MerchantSummary

| Field | Type | Description |
|-------|------|-------------|
| `name` | `string` | Merchant name |
| `total` | `float` | Total spend at merchant |
| `count` | `int` | Number of transactions |

### MonthlyTrend

| Field | Type | Description |
|-------|------|-------------|
| `month` | `string` | Format: "YYYY-MM" |
| `income` | `float` | Income for that month |
| `expenses` | `float` | Expenses for that month |

### DocumentRequest

| Field | Type | Description |
|-------|------|-------------|
| `document_type` | `string` | Type of document needed |
| `reason` | `string` | Why it would improve analysis |

---

## Grounding Models

### GroundingSource

| Field | Type | Description |
|-------|------|-------------|
| `uri` | `string` | Source URL |
| `title` | `string?` | Page title |
| `domain` | `string?` | Domain name |

### GroundingCitation

| Field | Type | Description |
|-------|------|-------------|
| `text_segment` | `string` | Cited text |
| `source_indices` | `int[]` | Indices into sources array |

### GroundingData

| Field | Type | Description |
|-------|------|-------------|
| `sources` | `GroundingSource[]` | Web sources used |
| `citations` | `GroundingCitation[]` | Text citations with source references |
| `search_entry_point_html` | `string?` | Google search widget HTML |

---

## Auth Models

### SignupRequest

| Field | Type | Description |
|-------|------|-------------|
| `email` | `string` | User email (validated, lowercased) |
| `password` | `string` | Min 8 chars |
| `display_name` | `string?` | Optional display name |

### LoginRequest

| Field | Type | Description |
|-------|------|-------------|
| `email` | `string` | |
| `password` | `string` | |

### UserResponse

| Field | Type | Description |
|-------|------|-------------|
| `id` | `string` | Cognito user sub |
| `email` | `string` | |
| `display_name` | `string` | |

### AuthResponse

| Field | Type | Description |
|-------|------|-------------|
| `token` | `string` | Cognito access token |
| `user` | `UserResponse` | User info |
| `encryption_key` | `string?` | Base64 AES-256 key (derived from password) |

---

## Dashboard Models

### ReportSummaryItem

| Field | Type | Description |
|-------|------|-------------|
| `id` | `string` | Report ID |
| `title` | `string` | e.g. "2024-01 to 2024-03 Analysis" |
| `created_at` | `string` | ISO 8601 timestamp |
| `language` | `string` | ISO 639-1 code |
| `total_income` | `float` | |
| `total_expenses` | `float` | |
| `net_savings` | `float` | |

### ReportDetail

| Field | Type | Description |
|-------|------|-------------|
| `id` | `string` | |
| `title` | `string` | |
| `created_at` | `string` | |
| `language` | `string` | |
| `report` | `FinancialReport` | Full report data |
| `podcast_script` | `string` | Generated podcast script |
| `audio_url` | `string?` | Presigned S3 URL for audio |
| `sentences` | `PodcastSentence[]` | Sentence timing for sync |
| `statements` | `{id, filename, file_type}[]` | Associated statements |

### StatementItem

| Field | Type | Description |
|-------|------|-------------|
| `id` | `string` | Statement ID |
| `filename` | `string` | Original filename |
| `uploaded_at` | `string` | ISO 8601 timestamp |
| `file_type` | `string` | "pdf" or "csv" |
| `file_size` | `int` | Size in bytes |

---

## Follow-up Models

### ChatMessage

| Field | Type | Description |
|-------|------|-------------|
| `role` | `string` | "user" or "assistant" |
| `content` | `string` | Message text |

### FollowUpRequest

| Field | Type | Description |
|-------|------|-------------|
| `report_data` | `dict` | Original FinancialReport as dict |
| `prompt` | `string` | User's follow-up question |
| `history` | `ChatMessage[]` | Previous conversation turns |
| `language` | `string` | Default "en" |

### FollowUpResponse

| Field | Type | Description |
|-------|------|-------------|
| `message` | `string` | AI response text |
| `podcast_script` | `string?` | Follow-up podcast script |

---

## Frontend-Only Types

### ProgressEvent

| Field | Type | Description |
|-------|------|-------------|
| `step` | `'parsing' \| 'analyzing' \| 'generating' \| 'narrating'` | Current pipeline step |
| `message` | `string` | Human-readable status |
| `percent` | `number` | Progress percentage (0-100) |

### PodcastSentence

| Field | Type | Description |
|-------|------|-------------|
| `text` | `string` | Sentence text |
| `start` | `number` | Start time in seconds |
| `end` | `number` | End time in seconds |

### PodcastAudio

| Field | Type | Description |
|-------|------|-------------|
| `podcast_script` | `string` | Full script text |
| `audio_base64` | `string \| null` | Base64 MP3 (null if TTS failed) |
| `sentences` | `PodcastSentence[]` | Sentence timing for sync |

### AgentQuestion

| Field | Type | Description |
|-------|------|-------------|
| `question` | `string` | The question text |
| `options` | `string[]` | Answer choices (UI adds "Other") |

### AppState

Union type: `'idle' | 'processing' | 'awaiting_documents' | 'awaiting_answer' | 'done' | 'error'`

### AnalysisHandle

Returned by `startAnalysis()` for bidirectional WebSocket communication.

| Method | Signature | Description |
|--------|-----------|-------------|
| `respond` | `(action: 'upload' \| 'skip', files?: File[]) => Promise<void>` | Respond to document request |
| `answerQuestion` | `(answer: string) => void` | Answer agent question |
| `close` | `() => void` | Close WebSocket connection |
