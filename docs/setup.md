# Setup Guide

## Prerequisites

- [Node.js](https://nodejs.org/) v18+
- [Python](https://www.python.org/) 3.12 (see `.python-version`)
- [Google AI Studio](https://aistudio.google.com/apikey) API key (Gemini)
- [ElevenLabs](https://elevenlabs.io/) API key (for podcast audio; optional - app falls back to script-only)

## Backend Setup

```sh
cd backend
python -m venv venv
source venv/bin/activate      # macOS/Linux
# venv\Scripts\activate       # Windows
pip install -r requirements.txt
```

Create environment file:

```sh
cp .env.example .env
```

Edit `.env` and add your API keys:

```
GEMINI_API_KEY=your-gemini-api-key-here
ELEVENLABS_API_KEY=your-elevenlabs-api-key-here
```

Start the backend:

```sh
uvicorn main:app --reload
```

Backend runs at http://localhost:8000

## Frontend Setup

```sh
cd frontend
npm install
npm run dev
```

Frontend runs at http://localhost:5173

## Running Both

You need two terminal windows:

```sh
# Terminal 1 - Backend
cd backend && source venv/bin/activate && uvicorn main:app --reload

# Terminal 2 - Frontend
cd frontend && npm run dev
```

Then open http://localhost:5173 in your browser.

## Running Tests

```sh
cd backend
source venv/bin/activate
pytest
```

## Production Build

```sh
cd frontend
npm run build
npm run preview   # preview the production build
```

## Troubleshooting

**"WebSocket connection error. Is the backend running?"**
- Make sure the backend is running on port 8000

**"GEMINI_API_KEY not set"**
- Check that `.env` exists in the `backend/` directory with the key set

**"ELEVENLABS_API_KEY not set"**
- The app works without it but falls back to script-only mode (no audio)
- Add the key to `.env` if you want podcast audio

**PDF parsing returns empty text**
- Some PDFs use images instead of text; pypdf can only extract text-based PDFs

**CORS errors in browser**
- Backend CORS is configured for `http://localhost:5173` only
- If using a different port, update `allow_origins` in `backend/main.py`
