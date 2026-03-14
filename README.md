# Easy MonAI

A full-stack financial analysis app that uses Google's Gemini AI to analyze bank statements (PDF/CSV) and generate financial reports and podcast scripts.

## Tech Stack

- **Frontend**: SvelteKit, TypeScript, Vite
- **Backend**: Python, FastAPI, Uvicorn
- **AI**: Google Gemini API
- **Auth**: AWS Cognito (optional)
- **Storage**: DynamoDB + S3 (optional)

## Prerequisites

- [Node.js](https://nodejs.org/) (v18+)
- [Python](https://www.python.org/) (3.12)
- AWS account (optional - only needed for user accounts and report persistence)

## Getting Started

### 1. Clone the repository

```sh
git clone <repo-url>
cd rockethacks
```

### 2. Set up the backend

```sh
cd backend
python -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Create a `.env` file in the `backend/` directory:

```sh
cp .env.example .env
```

Then open `.env` and add your API keys:

```
GEMINI_API_KEY=your-gemini-api-key-here
ELEVENLABS_API_KEY=your-elevenlabs-api-key-here  # optional
```

You can get a Gemini API key from [Google AI Studio](https://aistudio.google.com/apikey).

For user accounts and persistence, add AWS/Cognito configuration. See `backend/.env.example` for all available variables.

### 3. Set up the frontend

```sh
cd frontend
npm install
```

### 4. Run the app

You need both servers running at the same time.

**Terminal 1 — Backend** (runs on http://localhost:8000):

```sh
cd backend
source venv/bin/activate
uvicorn main:app --reload
```

**Terminal 2 — Frontend** (runs on http://localhost:5173):

```sh
cd frontend
npm run dev
```

Open http://localhost:5173 in your browser.

## Usage

1. Sign up for an account or continue as a guest
2. Upload one or more bank statements (PDF or CSV), or re-analyze saved statements
3. The AI parses your data, asks clarifying questions, and optionally searches the web for context
4. View your financial report with income/expense breakdowns, top merchants, insights, and grounding sources
5. Listen to or read the generated podcast summarizing your finances
6. Ask follow-up questions via the advisor chat
7. View past reports on the dashboard (authenticated users)

## Building for Production

```sh
cd frontend
npm run build
npm run preview   # preview the production build
```

### Docker Deployment

```sh
# Set env vars for frontend build
export VITE_API_URL=https://your-domain.com
export VITE_WS_URL=wss://your-domain.com/ws/analyze

docker compose up -d --build
```

Services: backend (port 8000), frontend (port 3000), nginx (80/443 with Let's Encrypt), certbot (auto-renewal).
