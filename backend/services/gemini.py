import asyncio
import json
import logging
import os

from dotenv import load_dotenv
from google import genai
from google.genai import types

from services.session import Session

load_dotenv()

logger = logging.getLogger("uvicorn.error")

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

MODEL = "gemini-2.5-flash"

MAX_DOCUMENT_REQUESTS = int(os.getenv("MAX_DOCUMENT_REQUESTS", "3"))

MULTI_DOC_REMINDER = """
IMPORTANT: You are receiving $file_count separate bank statement documents. They are separated by "--- filename ---" markers. Treat them as one combined financial picture — merge all transactions together when calculating totals, categories, and trends. Do not analyze them separately.
"""

AGENT_PROMPT = """\
You are a financial analyst agent. You have access to tools to help you produce the best possible analysis.

You will be given bank statement data. Your goal is to analyze it and produce a comprehensive financial report.

## Your tools

1. **request_documents** — Use this if the data seems incomplete or you could produce a significantly better analysis with additional documents. For example:
   - You see expenses but no income source
   - Only one month of data when trends would be useful
   - Credit card statements but no bank account statements (or vice versa)
   Be specific about what document type you need and why.

2. **finish** — Use this when you have enough data to produce a comprehensive report. Call this with the complete financial report JSON.

## Report format

When calling finish, provide a report object with this exact structure:
{
  "summary": {
    "total_income": <number>,
    "total_expenses": <number>,
    "net_savings": <number>,
    "date_range": "<start> to <end>"
  },
  "categories": [
    {"name": "<category name>", "total": <number>, "percentage": <number>, "transactions": <count>}
  ],
  "top_merchants": [
    {"name": "<merchant>", "total": <number>, "count": <count>}
  ],
  "insights": ["<insight string>"],
  "monthly_trend": [
    {"month": "<YYYY-MM>", "income": <number>, "expenses": <number>}
  ]
}

Categories should include things like: Food & Dining, Transportation, Shopping, Entertainment, Bills & Utilities, Healthcare, Subscriptions, Transfers, Income, etc.

## Guidelines
- If the data looks reasonably complete, just call finish directly. Don't request documents unnecessarily.
- You may request documents at most $max_requests times.
- If the user declines to provide a document, proceed with what you have.

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

# Tool declarations for the agentic loop
REPORT_SCHEMA = {
    "type": "object",
    "properties": {
        "summary": {
            "type": "object",
            "properties": {
                "total_income": {"type": "number"},
                "total_expenses": {"type": "number"},
                "net_savings": {"type": "number"},
                "date_range": {"type": "string"},
            },
            "required": ["total_income", "total_expenses", "net_savings", "date_range"],
        },
        "categories": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "total": {"type": "number"},
                    "percentage": {"type": "number"},
                    "transactions": {"type": "integer"},
                },
                "required": ["name", "total", "percentage", "transactions"],
            },
        },
        "top_merchants": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "total": {"type": "number"},
                    "count": {"type": "integer"},
                },
                "required": ["name", "total", "count"],
            },
        },
        "insights": {
            "type": "array",
            "items": {"type": "string"},
        },
        "monthly_trend": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "month": {"type": "string"},
                    "income": {"type": "number"},
                    "expenses": {"type": "number"},
                },
                "required": ["month", "income", "expenses"],
            },
        },
    },
    "required": ["summary", "categories", "top_merchants", "insights", "monthly_trend"],
}

REQUEST_DOCUMENTS_DECL = types.FunctionDeclaration(
    name="request_documents",
    description="Request additional documents from the user to improve the analysis. Use when data appears incomplete.",
    parameters=types.Schema(
        type="OBJECT",
        properties={
            "document_type": types.Schema(
                type="STRING",
                description="The type of document needed, e.g. 'pay stub', 'bank statement', 'credit card statement'",
            ),
            "reason": types.Schema(
                type="STRING",
                description="Why this document would help improve the analysis",
            ),
        },
        required=["document_type", "reason"],
    ),
)

FINISH_DECL = types.FunctionDeclaration(
    name="finish",
    description="Complete the analysis and return the final financial report.",
    parameters_json_schema={
        "type": "object",
        "properties": {
            "report": REPORT_SCHEMA,
        },
        "required": ["report"],
    },
)

AGENT_TOOLS = [types.Tool(function_declarations=[REQUEST_DOCUMENTS_DECL, FINISH_DECL])]


async def analyze_with_gemini_agent(
    statement_text: str,
    file_count: int,
    session: Session,
    max_requests: int = MAX_DOCUMENT_REQUESTS,
):
    """Async generator that yields events: ("result", report_dict), ("request_documents", {document_type, reason}), or ("error", msg)."""
    from string import Template

    prompt = Template(AGENT_PROMPT).safe_substitute(
        statement_text=statement_text,
        max_requests=max_requests,
    )
    if file_count > 1:
        reminder = Template(MULTI_DOC_REMINDER).safe_substitute(file_count=file_count)
        prompt = reminder + "\n" + prompt

    contents = [types.Content(role="user", parts=[types.Part.from_text(text=prompt)])]
    config = types.GenerateContentConfig(
        tools=AGENT_TOOLS,
        tool_config=types.ToolConfig(
            function_calling_config=types.FunctionCallingConfig(mode="ANY")
        ),
    )

    request_count = 0
    max_iterations = max_requests + 2  # safety cap

    for iteration in range(max_iterations):
        logger.info(f"  Agent loop iteration {iteration + 1}")

        response = await asyncio.to_thread(
            client.models.generate_content,
            model=MODEL,
            contents=contents,
            config=config,
        )

        if not response.function_calls:
            # Fallback: model returned text instead of tool call
            logger.warning("  Agent returned text instead of tool call, attempting JSON parse")
            try:
                yield ("result", json.loads(response.text))
            except (json.JSONDecodeError, ValueError):
                yield ("error", "Agent failed to produce a valid report")
            return

        for fc in response.function_calls:
            if fc.name == "finish":
                report_data = fc.args.get("report", fc.args)
                logger.info("  Agent called finish")
                yield ("result", report_data)
                return

            elif fc.name == "request_documents":
                request_count += 1
                doc_type = fc.args["document_type"]
                reason = fc.args["reason"]
                logger.info(f"  Agent requesting document: {doc_type} (request {request_count}/{max_requests})")

                yield ("request_documents", {"document_type": doc_type, "reason": reason})

                # Wait for user response via session
                session.event.clear()
                try:
                    await asyncio.wait_for(session.event.wait(), timeout=300)
                except asyncio.TimeoutError:
                    yield ("error", "Timed out waiting for document upload")
                    return

                user_response = session.user_response
                session.user_response = None

                if user_response and user_response.get("action") == "upload":
                    additional_text = user_response.get("document_text", "")
                    func_response = types.Part.from_function_response(
                        name="request_documents",
                        response={"result": f"User provided additional document:\n{additional_text}"},
                    )
                else:
                    func_response = types.Part.from_function_response(
                        name="request_documents",
                        response={"result": "User declined to provide this document. Proceed with available data."},
                    )

                # Append model response + function result to conversation
                contents.append(response.candidates[0].content)
                contents.append(types.Content(role="user", parts=[func_response]))

                # If we've hit the max, tell the model on the next iteration
                if request_count >= max_requests:
                    contents.append(
                        types.Content(
                            role="user",
                            parts=[types.Part.from_text(text="You have used all your document requests. Please call finish now with the best report you can produce from the available data.")],
                        )
                    )
                break  # restart the loop for the next generate_content call

    yield ("error", "Agent exceeded maximum iterations")


async def generate_podcast_script(report: dict) -> str:
    from string import Template

    prompt = Template(PODCAST_PROMPT).safe_substitute(report_json=json.dumps(report, indent=2))
    response = await asyncio.to_thread(
        client.models.generate_content,
        model=MODEL,
        contents=prompt,
    )
    return response.text
