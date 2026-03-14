# Data Models

Backend models (Pydantic) and frontend interfaces (TypeScript) are kept in sync manually.

## Backend: `backend/models/schemas.py`

## Frontend: `frontend/src/lib/types.ts`

---

## Models

### FinancialReport

Top-level report returned by the Gemini agent.

| Field | Type | Description |
|-------|------|-------------|
| `summary` | `FinancialSummary` | Income, expenses, savings overview |
| `categories` | `CategoryBreakdown[]` | Spending by category |
| `top_merchants` | `MerchantSummary[]` | Highest-spend merchants |
| `insights` | `string[]` | AI-generated financial insights |
| `monthly_trend` | `MonthlyTrend[]` | Month-by-month income vs expenses |

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

### AnalysisResult

| Field | Type | Description |
|-------|------|-------------|
| `report` | `FinancialReport` | The financial report |
| `podcast_script` | `string` | Generated podcast script |

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
