# Easy MonAI

A full-stack financial analysis app that uses Google's Gemini AI to analyze bank statements (PDF/CSV) and generate financial reports and podcast scripts.

## Tech Stack

- **Frontend**: SvelteKit, TypeScript, Vite
- **Backend**: Python, FastAPI, Uvicorn
- **AI**: Google Gemini API

## Prerequisites

- [Node.js](https://nodejs.org/) (v18+)
- [Python](https://www.python.org/) (3.10+)

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

Then open `.env` and add your Gemini API key:

```
GEMINI_API_KEY=your-gemini-api-key-here
```

You can get an API key from [Google AI Studio](https://aistudio.google.com/apikey).

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

1. Upload one or more bank statements (PDF or CSV)
2. Wait for the AI to parse and analyze your financial data
3. View your financial report with income/expense breakdowns, top merchants, and insights
4. Read or copy the generated podcast script summarizing your finances

## Building for Production

```sh
cd frontend
npm run build
npm run preview   # preview the production build
```
