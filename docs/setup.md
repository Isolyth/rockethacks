# Setup Guide

## Prerequisites

- [Node.js](https://nodejs.org/) v18+
- [Python](https://www.python.org/) 3.12 (see `.python-version`)
- [Google AI Studio](https://aistudio.google.com/apikey) API key (Gemini)
- [ElevenLabs](https://elevenlabs.io/) API key (for podcast audio; optional - app falls back to script-only)
- AWS account with Cognito user pool, DynamoDB, and S3 bucket (optional - only needed for user accounts and persistence; not needed for guest mode)

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

Edit `.env` and add your configuration:

```
GEMINI_API_KEY=your-key          # Required
ELEVENLABS_API_KEY=your-key      # Optional (falls back to script-only)

# For user accounts & persistence (all optional for guest mode):
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_REGION=us-east-1
AWS_S3_BUCKET=monai-uploads
COGNITO_USER_POOL_ID=...
COGNITO_CLIENT_ID=...
COGNITO_CLIENT_SECRET=...
CORS_ORIGINS=http://localhost:5173
```

See `backend/config.py` for all env vars with defaults.

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

## Docker Deployment

```sh
# Set env vars for frontend build
export VITE_API_URL=https://your-domain.com
export VITE_WS_URL=wss://your-domain.com/ws/analyze

docker compose up -d --build
```

Services: backend (port 8000), frontend (port 3000), nginx (80/443 with Let's Encrypt), certbot (auto-renewal).

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
- Update `CORS_ORIGINS` env var in backend `.env` (comma-separated list of allowed origins)

**"Too many connections" / WebSocket close code 4029**
- Per-IP limit of 5 concurrent WebSocket connections; close unused tabs

**"Too many requests" / HTTP 429**
- Rate limit on auth or follow-up endpoints; wait and retry

**DynamoDB table errors**
- Tables auto-create on startup; ensure AWS credentials and region are correct in `.env`
