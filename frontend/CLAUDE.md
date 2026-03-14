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

- `src/routes/+layout.svelte` - Root layout with nav header, auth hydration, logout
- `src/routes/+page.svelte` - Landing page (hero for guests, upload for authenticated users)
- `src/routes/login/+page.svelte` - Login page
- `src/routes/signup/+page.svelte` - Signup page with password requirements display
- `src/routes/analyze/+page.svelte` - Main analysis flow with saved statements selector
- `src/routes/dashboard/+page.svelte` - Dashboard with Reports and Statements tabs
- `src/routes/dashboard/report/[id]/+page.svelte` - Individual report view with advisor chat
- `src/lib/api.ts` - WebSocket client (`startAnalysis`) + REST client (auth, dashboard) + SSE follow-up (`streamFollowup`)
- `src/lib/types.ts` - TypeScript interfaces matching backend Pydantic models (includes auth, dashboard, grounding types)
- `src/lib/stores/auth.svelte.ts` - Auth state (token, user, encryptionKey) with localStorage/sessionStorage persistence
- `src/lib/utils/file-upload.ts` - Shared file validation, drag-drop handlers, size formatting
- `src/lib/components/` - All UI components:
  - `FileUpload.svelte` - Drag-drop upload with language selector
  - `Report.svelte` - Financial report display (categories, merchants, insights, grounding sources)
  - `PodcastPlayer.svelte` - Audio player with sentence-level highlight sync (supports base64 and presigned URLs)
  - `ProgressBar.svelte` - Multi-step progress (parsing/analyzing/generating/narrating)
  - `DocumentRequest.svelte` - Agent document request UI with file upload
  - `QuestionCard.svelte` - Agent multiple-choice question UI
  - `ThinkingIndicator.svelte` - Animated AI thinking display
  - `AdvisorChat.svelte` - Follow-up chat with SSE streaming, markdown rendering, thinking indicator
  - `SavedStatements.svelte` - Saved statements checkbox selector for re-analysis

## Key Patterns

- Svelte 5 runes: `$state`, `$derived`, `$effect`, `$bindable` (not stores, except auth)
- Auth store (`auth.svelte.ts`) uses `$state` rune; JWT in localStorage, encryption key in sessionStorage; `hydrateAuth()` validates on mount
- App state machine: `idle` -> `processing` -> `awaiting_documents`/`awaiting_answer` -> `done`/`error`
- WebSocket URL auto-detects protocol (ws/wss); configurable via `VITE_WS_URL` env var
- Auth credentials sent in WebSocket message body (not URL) to avoid server log exposure
- Files sent as base64 JSON over WebSocket
- Audio playback uses base64-decoded Blob URL or presigned S3 URL
- Markdown rendering via `marked` + `isomorphic-dompurify` (used in AdvisorChat)
- Follow-up chat streams via SSE (`streamFollowup` in api.ts)
- No external CSS framework - custom CSS with dark theme variables
