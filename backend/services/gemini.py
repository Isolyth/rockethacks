import asyncio
import json
import os

from dotenv import load_dotenv
from google import genai

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

MODEL = "gemini-flash-latest"

MULTI_DOC_REMINDER = """
IMPORTANT: You are receiving $file_count separate bank statement documents. They are separated by "--- filename ---" markers. Treat them as one combined financial picture — merge all transactions together when calculating totals, categories, and trends. Do not analyze them separately.
"""

ANALYSIS_PROMPT = """\
You are a financial analyst. Analyze the following bank statement data and return a JSON object with this exact structure:

{
  "summary": {
    "total_income": <number>,
    "total_expenses": <number>,
    "net_savings": <number>,
    "date_range": "<start> to <end>"
  },
  "categories": [
    {
      "name": "<category name>",
      "total": <number>,
      "percentage": <number>,
      "transactions": <count>
    }
  ],
  "top_merchants": [
    {"name": "<merchant>", "total": <number>, "count": <count>}
  ],
  "insights": [
    "<insight string>"
  ],
  "monthly_trend": [
    {"month": "<YYYY-MM>", "income": <number>, "expenses": <number>}
  ]
}

Categories should include things like: Food & Dining, Transportation, Shopping, Entertainment, Bills & Utilities, Healthcare, Subscriptions, Transfers, Income, etc.

Return ONLY valid JSON, no markdown formatting.

Bank statement data:
---
$statement_text
"""

PODCAST_PROMPT = """\
You are a friendly, engaging financial podcast host. Based on the following financial analysis, write a 2-3 minute podcast script that:

1. Opens with a warm greeting
2. Summarizes the person's financial health (income vs expenses, savings rate)
3. Highlights the top spending categories with specific numbers
4. Calls out any concerning patterns or positive habits
5. Gives 2-3 actionable tips based on the data
6. Closes with encouragement

Keep the tone conversational, like you're talking to a friend. Use the actual numbers from the data.

Financial analysis:
$report_json
"""


async def analyze_with_gemini(statement_text: str, file_count: int = 1) -> dict:
    from string import Template
    prompt = Template(ANALYSIS_PROMPT).safe_substitute(statement_text=statement_text)
    if file_count > 1:
        reminder = Template(MULTI_DOC_REMINDER).safe_substitute(file_count=file_count)
        prompt = reminder + "\n" + prompt
    response = await asyncio.to_thread(
        client.models.generate_content,
        model=MODEL,
        contents=prompt,
        config={"response_mime_type": "application/json"},
    )
    return json.loads(response.text)


async def generate_podcast_script(report: dict) -> str:
    from string import Template
    prompt = Template(PODCAST_PROMPT).safe_substitute(report_json=json.dumps(report, indent=2))
    response = await asyncio.to_thread(
        client.models.generate_content,
        model=MODEL,
        contents=prompt,
    )
    return response.text
