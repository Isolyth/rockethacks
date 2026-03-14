# Frontend

SvelteKit 2 + Svelte 5 + TypeScript app.

## Setup

```sh
npm install
npm run dev
```

## Key Commands

```sh
npm run dev          # dev server (localhost:5173)
npm run build        # production build
npm run preview      # preview production build
npm run check        # svelte-check + TypeScript
```

## Structure

- `src/routes/+page.svelte` - Main (and only) page, manages all app state
- `src/lib/api.ts` - WebSocket client, `startAnalysis()` returns an `AnalysisHandle`
- `src/lib/types.ts` - TypeScript interfaces matching backend Pydantic models
- `src/lib/components/` - All UI components:
  - `FileUpload.svelte` - Drag-drop upload with language selector
  - `Report.svelte` - Financial report display (categories, merchants, insights)
  - `PodcastPlayer.svelte` - Audio player with sentence-level highlight sync
  - `PodcastScript.svelte` - Script-only fallback (no audio)
  - `ProgressBar.svelte` - Multi-step progress (parsing/analyzing/generating/narrating)
  - `DocumentRequest.svelte` - Agent document request UI with file upload
  - `QuestionCard.svelte` - Agent multiple-choice question UI
  - `ThinkingIndicator.svelte` - Animated AI thinking display

## Key Patterns

- Svelte 5 runes: `$state`, `$derived`, `$effect` (not stores)
- App state machine: `idle` -> `processing` -> `awaiting_documents`/`awaiting_answer` -> `done`/`error`
- WebSocket connects to `ws://localhost:8000/ws/analyze`
- Files sent as base64 JSON over WebSocket
- Audio playback uses base64-decoded Blob URL
- No external CSS framework - custom CSS with dark theme variables
