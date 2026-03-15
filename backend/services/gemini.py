import asyncio
import json
import logging

from google import genai
from google.genai import types

from config import GEMINI_API_KEY, GEMINI_MODEL, MAX_DOCUMENT_REQUESTS
from services.session import Session

logger = logging.getLogger("uvicorn.error")

client = genai.Client(api_key=GEMINI_API_KEY)

MODEL = GEMINI_MODEL

MULTI_DOC_REMINDER = """
IMPORTANT: You are receiving $file_count separate bank statement documents. They are separated by "--- filename ---" markers. Treat them as one combined financial picture — merge all transactions together when calculating totals, categories, and trends. Do not analyze them separately.
"""

LANGUAGE_NAMES = {
    "en": "English", "es": "Spanish", "fr": "French", "de": "German",
    "pt": "Portuguese", "it": "Italian", "ja": "Japanese", "ko": "Korean",
    "zh": "Chinese", "hi": "Hindi", "ar": "Arabic", "nl": "Dutch",
    "pl": "Polish", "ru": "Russian",
}

AGENT_PROMPT = """\
You are a financial analyst agent. You have access to tools to help you produce the best possible analysis.

You will be given bank statement data. Your goal is to analyze it and produce a comprehensive financial report. You should actively engage with the user to gather context and additional data before finalizing your report.

$language_instruction

## Your tools

1. **request_documents** — Request additional documents from the user. You should be proactive about this! Examples of when to use it:
   - You see expenses but no income source — ask for pay stubs or bank statements showing deposits
   - Only one month of data — ask for more months to identify trends
   - Credit card statements but no bank account statements (or vice versa)
   - You see loan payments but no loan statements
   - Investment or savings accounts are referenced but not included
   - You only have partial data (e.g., one account but the user likely has more)
   - Bills & Utilities spending looks high — ask for utility bills to break down what's driving the cost
   Always be specific about what you need and explain how it will improve the analysis.

2. **ask_question** — Ask the user a multiple-choice question to better understand their financial situation. Provide 2-4 options. The UI will automatically add an "Other" option where the user can type a custom answer, so do NOT include an "Other", "None of the above", or catch-all option yourself. Use this to:
   - Clarify ambiguous transactions (e.g., "Is 'ACME Corp' your employer or a vendor?")
   - Understand financial goals (e.g., "What are you most interested in: saving more, reducing debt, or budgeting?")
   - Get context about their situation (e.g., "Do you have other bank accounts not included here?")
   - Clarify income patterns (e.g., "Are you salaried, freelance, or a mix?")

3. **search_web** — Search the web for current financial data, benchmark comparisons, average spending statistics, or relevant context. Use this to ground your insights in real data — for example, comparing the user's savings rate to the national average, or referencing current interest rates. Provide a specific search query.

When you are ready to finalize your analysis, you MUST call these three tools IN ORDER:

4. **submit_report** — Call this FIRST. Submit the full financial report with category breakdown (for the bar chart). Provide the complete report object.

5. **submit_pie_data** — Call this SECOND, after submit_report. Submit income allocation segments for a doughnut chart. Group spending into high-level buckets showing how income is distributed (e.g., Essentials, Lifestyle, Savings, Financial/Debt). Each segment should have a name, total amount, and percentage of total income.

6. **submit_heatmap_data** — Call this THIRD, after submit_pie_data. Submit daily spending totals for a calendar heatmap. Provide one entry per day in the statement date range with the date (YYYY-MM-DD) and total spending that day.

## Report format

When calling submit_report, provide a report object with this exact structure:
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
- You MUST call ask_question or request_documents at least TWICE before calling submit_report. Never go straight to submit_report.
- On your FIRST turn, always ask a question to understand the user's goals or clarify something about the data.
- On your SECOND turn, either ask another question or request a missing document.
- Only call submit_report after you've gathered enough context through questions/documents.
- After submit_report, you MUST call submit_pie_data, then submit_heatmap_data — all three in sequence.
- Use ask_question liberally — it's cheap and makes the report much better. Ask about goals, clarify ambiguous merchants, confirm income sources, etc.
- You may make at most $max_requests total interactions (document requests + questions combined).
- If the user declines or skips, proceed with what you have.
- Incorporate user answers into your insights and recommendations.
- You can reference external data (market rates, national averages, benchmarks) — the system will search for this automatically. When citing external data in insights, be specific.

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

$language_instruction

IMPORTANT: Your output will be fed directly into a text-to-speech engine and read aloud as-is. Write ONLY the spoken words. Do NOT include:
- Speaker labels (e.g., "Host:", "Narrator:")
- Stage directions (e.g., "(intro music fades in)", "(pause)", "(laughs)")
- Sound effects or music cues
- Any formatting, headers, or markdown

Just write the natural spoken monologue, as if you are already talking into a microphone.

Keep the tone conversational, like you're talking to a friend. Use the actual numbers from the data.

Financial analysis:
$report_json
"""

FOLLOWUP_AGENT_PROMPT = """\
You are a friendly, helpful financial advisor agent. You previously generated a financial report based on the user's bank statements.
The user is now asking follow-up questions or proposing "what-if" scenarios.

Answer the user's question directly, clearly, and concisely based on their original financial figures.
If they ask a "what-if" question, project the new numbers (e.g., how much they would save) and provide a helpful insight.

$language_instruction

Original Financial Report Context:
$report_json
"""

FOLLOWUP_PODCAST_PROMPT = """\
You are a friendly, engaging financial podcast host. You previously recorded a script for this user.
The user just asked a follow-up question, and we gave them a response.

User prompt: "$prompt"
Our response: "$ai_response"

Write a SHORT, 30-second audio update to the podcast.
1. Acknowledge their question directly ("You asked what would happen if...")
2. Give the bottom line of our response.
3. Keep it brief and encouraging.

$language_instruction

IMPORTANT: Your output will be fed directly into a text-to-speech engine and read aloud as-is. Write ONLY the spoken words. Do NOT include formatting, stage directions, or speaker labels.
"""


# Tool declarations for the agentic loop
#
# NOTE: google_search (GoogleSearch tool) cannot be passed alongside
# function_declarations in the same API request — the Gemini API rejects the
# combination. To work around this, search_web is declared as a regular
# function that the agent can call. When invoked, _do_grounded_search() makes
# a *separate* Gemini API call with only GoogleSearch enabled, then returns
# the grounded text and source metadata back to the agent as a function
# response. This lets the agent decide when to search while keeping
# function_declarations intact for the agentic loop.
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

ASK_QUESTION_DECL = types.FunctionDeclaration(
    name="ask_question",
    description="Ask the user a multiple-choice question to clarify their financial situation or ambiguous data.",
    parameters=types.Schema(
        type="OBJECT",
        properties={
            "question": types.Schema(
                type="STRING",
                description="The question to ask the user",
            ),
            "options": types.Schema(
                type="ARRAY",
                items=types.Schema(type="STRING"),
                description="2-4 answer options for the user to choose from",
            ),
        },
        required=["question", "options"],
    ),
)

SUBMIT_REPORT_DECL = types.FunctionDeclaration(
    name="submit_report",
    description="Submit the financial report with category breakdown for the bar chart. Call this FIRST when ready to finalize.",
    parameters_json_schema={
        "type": "object",
        "properties": {
            "report": REPORT_SCHEMA,
        },
        "required": ["report"],
    },
)

PIE_SEGMENT_SCHEMA = {
    "type": "object",
    "properties": {
        "segments": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "total": {"type": "number"},
                    "percentage": {"type": "number"},
                },
                "required": ["name", "total", "percentage"],
            },
        },
    },
    "required": ["segments"],
}

SUBMIT_PIE_DATA_DECL = types.FunctionDeclaration(
    name="submit_pie_data",
    description="Submit income allocation segments for the doughnut chart. Group spending into high-level buckets (Essentials, Lifestyle, Savings, Debt, etc.) showing how income is distributed. Call this SECOND, after submit_report.",
    parameters_json_schema=PIE_SEGMENT_SCHEMA,
)

HEATMAP_SCHEMA = {
    "type": "object",
    "properties": {
        "daily_spending": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "date": {"type": "string", "description": "Date in YYYY-MM-DD format"},
                    "total": {"type": "number", "description": "Total spending on this day"},
                },
                "required": ["date", "total"],
            },
        },
    },
    "required": ["daily_spending"],
}

SUBMIT_HEATMAP_DATA_DECL = types.FunctionDeclaration(
    name="submit_heatmap_data",
    description="Submit daily spending totals for the calendar heatmap. Provide one entry per day in the statement date range. Call this THIRD, after submit_pie_data.",
    parameters_json_schema=HEATMAP_SCHEMA,
)

SEARCH_WEB_DECL = types.FunctionDeclaration(
    name="search_web",
    description="Search the web for current financial data, benchmarks, averages, or other relevant context to enrich the analysis.",
    parameters=types.Schema(
        type="OBJECT",
        properties={
            "query": types.Schema(
                type="STRING",
                description="The search query, e.g. 'average US savings rate 2024' or 'typical grocery spending per month'",
            ),
        },
        required=["query"],
    ),
)

AGENT_TOOLS = [types.Tool(function_declarations=[
    REQUEST_DOCUMENTS_DECL, ASK_QUESTION_DECL, SUBMIT_REPORT_DECL,
    SUBMIT_PIE_DATA_DECL, SUBMIT_HEATMAP_DATA_DECL, SEARCH_WEB_DECL,
])]



def _language_instruction(language: str) -> str:
    """Build a language instruction string for prompts."""
    if language == "en":
        return ""
    lang_name = LANGUAGE_NAMES.get(language, language)
    return f"IMPORTANT: You MUST write ALL of your output in {lang_name}. This includes questions, options, insights, category names, and the final report. The bank statement data may be in any language — always respond in {lang_name}."


def _extract_grounding_data(grounding_metadata) -> dict | None:
    """Convert GroundingMetadata to a serializable dict."""
    if grounding_metadata is None:
        return None

    sources = []
    if getattr(grounding_metadata, "grounding_chunks", None):
        for chunk in grounding_metadata.grounding_chunks:
            if getattr(chunk, "web", None):
                sources.append({
                    "uri": chunk.web.uri or "",
                    "title": getattr(chunk.web, "title", None),
                    "domain": getattr(chunk.web, "domain", None),
                })

    citations = []
    if getattr(grounding_metadata, "grounding_supports", None):
        for support in grounding_metadata.grounding_supports:
            if getattr(support, "segment", None) and getattr(support, "grounding_chunk_indices", None):
                citations.append({
                    "text_segment": support.segment.text or "",
                    "source_indices": list(support.grounding_chunk_indices),
                })

    search_entry_point_html = None
    if getattr(grounding_metadata, "search_entry_point", None):
        search_entry_point_html = getattr(
            grounding_metadata.search_entry_point, "rendered_content", None
        )

    if not sources and not citations and not search_entry_point_html:
        return None

    return {
        "sources": sources,
        "citations": citations,
        "search_entry_point_html": search_entry_point_html,
    }


def _deduplicate_sources(sources: list[dict], citations: list[dict]) -> tuple[list[dict], list[dict]]:
    """Deduplicate sources by URI and remap citation indices."""
    seen: dict[str, int] = {}
    deduped: list[dict] = []
    index_map: dict[int, int] = {}

    for old_idx, source in enumerate(sources):
        uri = source.get("uri", "")
        if uri in seen:
            index_map[old_idx] = seen[uri]
        else:
            new_idx = len(deduped)
            seen[uri] = new_idx
            index_map[old_idx] = new_idx
            deduped.append(source)

    remapped_citations = []
    for citation in citations:
        remapped_citations.append({
            "text_segment": citation["text_segment"],
            "source_indices": [index_map.get(i, i) for i in citation["source_indices"]],
        })

    return deduped, remapped_citations


async def _do_grounded_search(query: str) -> tuple[str, object | None]:
    """Make a separate Gemini call with GoogleSearch grounding.

    Returns (text_result, grounding_metadata).

    google_search cannot be combined with function_declarations in the same
    API request, so the agent declares search_web as a regular function and
    this helper performs the actual grounded search in an isolated call.
    """
    try:
        response = await asyncio.to_thread(
            client.models.generate_content,
            model=MODEL,
            contents=query,
            config=types.GenerateContentConfig(
                tools=[types.Tool(google_search=types.GoogleSearch())],
            ),
        )
        text = response.text or ""
        grounding_meta = None
        if response.candidates:
            grounding_meta = getattr(response.candidates[0], "grounding_metadata", None)
        return text, grounding_meta
    except Exception as e:
        logger.warning(f"  Grounded search failed: {e}")
        return f"Search failed: {e}", None


async def _handle_search_web(query, contents, response_content,
                             all_grounding_sources, all_grounding_citations,
                             search_entry_point_html):
    """Perform a grounded search, accumulate grounding data, and append to contents."""
    search_result, grounding_meta = await _do_grounded_search(query)

    if grounding_meta:
        gd = _extract_grounding_data(grounding_meta)
        if gd:
            offset = len(all_grounding_sources)
            all_grounding_sources.extend(gd["sources"])
            for citation in gd["citations"]:
                citation["source_indices"] = [i + offset for i in citation["source_indices"]]
            all_grounding_citations.extend(gd["citations"])
            if gd["search_entry_point_html"]:
                search_entry_point_html = gd["search_entry_point_html"]

    func_response = types.Part.from_function_response(
        name="search_web",
        response={"result": search_result},
    )
    contents.append(response_content)
    contents.append(types.Content(role="user", parts=[func_response]))
    return search_entry_point_html


def _build_interaction_event(fc):
    """Return the appropriate event tuple for a request_documents or ask_question tool call."""
    if fc.name == "request_documents":
        return ("request_documents", {
            "document_type": fc.args["document_type"],
            "reason": fc.args["reason"],
        })
    return ("ask_question", {
        "question": fc.args["question"],
        "options": fc.args.get("options", []),
    })


def _handle_interaction_response(fc, session, contents, response_content,
                                  interaction_count, max_requests):
    """Process user response for request_documents or ask_question and append to contents."""
    user_response = session.user_response
    session.user_response = None

    if fc.name == "request_documents":
        logger.info(f"  Agent requesting document: {fc.args['document_type']} (interaction {interaction_count}/{max_requests})")
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
    else:
        answer = (user_response or {}).get("answer", "No answer provided")
        logger.info(f"  Agent asking question: {fc.args['question']} (interaction {interaction_count}/{max_requests})")
        func_response = types.Part.from_function_response(
            name="ask_question",
            response={"result": f"User answered: {answer}"},
        )

    contents.append(response_content)
    contents.append(types.Content(role="user", parts=[func_response]))

    if interaction_count >= max_requests:
        contents.append(
            types.Content(
                role="user",
                parts=[types.Part.from_text(text="You have used all your interaction requests. Please call finish now with the best report you can produce from the available data.")],
            )
        )


async def analyze_with_gemini_agent(
    statement_text: str,
    file_count: int,
    session: Session,
    max_requests: int = MAX_DOCUMENT_REQUESTS,
    language: str = "en",
):
    """Async generator yielding: ("result", data), ("request_documents", data), ("ask_question", data), ("thinking", text), ("error", msg)."""
    from string import Template

    prompt = Template(AGENT_PROMPT).safe_substitute(
        statement_text=statement_text,
        max_requests=max_requests,
        language_instruction=_language_instruction(language),
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
        thinking_config=types.ThinkingConfig(include_thoughts=True),
    )

    interaction_count = 0
    max_iterations = max_requests + 5  # safety cap (extra room for search iterations)

    # Accumulate grounding data across iterations
    all_grounding_sources: list[dict] = []
    all_grounding_citations: list[dict] = []
    search_entry_point_html: str | None = None

    def _attach_grounding(report_data: dict) -> dict:
        """Attach accumulated grounding data to a report dict."""
        if all_grounding_sources:
            sources, citations = _deduplicate_sources(all_grounding_sources, all_grounding_citations)
            report_data["grounding"] = {
                "sources": sources,
                "citations": citations,
                "search_entry_point_html": search_entry_point_html,
            }
        return report_data

    for iteration in range(max_iterations):
        logger.info(f"  Agent loop iteration {iteration + 1}")

        # Stream the response, yielding thinking chunks along the way
        response_content = None
        async for event_type, event_data in _stream_via_thread(contents, config):
            if event_type == "thinking":
                yield ("thinking", event_data)
            elif event_type == "_response":
                response_content = event_data

        if response_content is None:
            yield ("error", "Agent returned empty response")
            return

        # Extract function calls from the response
        function_calls = [p.function_call for p in response_content.parts if p.function_call]

        if not function_calls:
            # Fallback: model returned text instead of tool call
            logger.warning("  Agent returned text instead of tool call, attempting JSON parse")
            text_parts = [p.text for p in response_content.parts if p.text and not getattr(p, "thought", False)]
            full_text = "".join(text_parts)
            try:
                yield ("report_ready", _attach_grounding(json.loads(full_text)))
            except (json.JSONDecodeError, ValueError):
                yield ("error", "Agent failed to produce a valid report")
            return

        for fc in function_calls:
            if fc.name == "submit_report":
                report_data = fc.args.get("report", fc.args)
                logger.info("  Agent called submit_report")
                yield ("report_ready", _attach_grounding(report_data))
                func_response = types.Part.from_function_response(
                    name="submit_report",
                    response={"result": "Report received. Now call submit_pie_data with income allocation segments for the doughnut chart. Group spending into high-level buckets (e.g., Essentials, Lifestyle, Savings, Debt) showing how income is distributed as a percentage of total income."},
                )
                contents.append(response_content)
                contents.append(types.Content(role="user", parts=[func_response]))
                break

            elif fc.name == "submit_pie_data":
                pie_data = fc.args.get("segments", [])
                logger.info(f"  Agent called submit_pie_data ({len(pie_data)} segments)")
                yield ("pie_chart_ready", {"segments": pie_data})
                func_response = types.Part.from_function_response(
                    name="submit_pie_data",
                    response={"result": "Pie chart data received. Now call submit_heatmap_data with daily spending totals. Provide one entry per day (YYYY-MM-DD format) covering the full statement date range."},
                )
                contents.append(response_content)
                contents.append(types.Content(role="user", parts=[func_response]))
                break

            elif fc.name == "submit_heatmap_data":
                heatmap_data = fc.args.get("daily_spending", [])
                logger.info(f"  Agent called submit_heatmap_data ({len(heatmap_data)} days)")
                yield ("heatmap_ready", {"daily_spending": heatmap_data})
                return

            elif fc.name == "search_web":
                query = fc.args.get("query", "")
                logger.info(f"  Agent searching web: {query}")
                yield ("thinking", f"Searching the web: {query}")

                search_entry_point_html = await _handle_search_web(
                    query, contents, response_content,
                    all_grounding_sources, all_grounding_citations, search_entry_point_html,
                )
                break

            elif fc.name in ("request_documents", "ask_question"):
                interaction_count += 1
                event = _build_interaction_event(fc)
                yield event
                _handle_interaction_response(
                    fc, session, contents, response_content,
                    interaction_count, max_requests,
                )
                break

    yield ("error", "Agent exceeded maximum iterations")


async def _stream_via_thread(contents, config):
    """Run the synchronous streaming generator in a thread and yield events."""
    import threading

    loop = asyncio.get_event_loop()
    q = asyncio.Queue()

    def _run():
        try:
            collected_parts = []
            for chunk in client.models.generate_content_stream(
                model=MODEL,
                contents=contents,
                config=config,
            ):
                if not chunk.candidates:
                    continue
                for part in chunk.candidates[0].content.parts:
                    if getattr(part, "thought", False) and part.text:
                        loop.call_soon_threadsafe(q.put_nowait, ("thinking", part.text))
                    else:
                        # Accumulate non-thought parts (function calls, text)
                        # so they aren't lost when later chunks only have thoughts
                        collected_parts.append(part)
            loop.call_soon_threadsafe(q.put_nowait, ("_collected_parts", collected_parts))
        except Exception as e:
            loop.call_soon_threadsafe(q.put_nowait, ("_error", str(e)))
        finally:
            loop.call_soon_threadsafe(q.put_nowait, None)  # sentinel

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()

    collected_parts = []
    while True:
        item = await q.get()
        if item is None:
            break
        event_type, event_data = item
        if event_type == "thinking":
            yield ("thinking", event_data)
        elif event_type == "_collected_parts":
            collected_parts = event_data
        elif event_type == "_error":
            yield ("error", event_data)
            return

    if collected_parts:
        yield ("_response", types.Content(role="model", parts=collected_parts))


async def generate_podcast_script(report: dict, language: str = "en") -> str:
    from string import Template

    lang_name = LANGUAGE_NAMES.get(language, language)
    if language == "en":
        lang_instruction = ""
    else:
        lang_instruction = f"IMPORTANT: Write the ENTIRE script in {lang_name}. The listener speaks {lang_name}."

    prompt = Template(PODCAST_PROMPT).safe_substitute(
        report_json=json.dumps(report, indent=2),
        language_instruction=lang_instruction,
    )
    response = await asyncio.to_thread(
        client.models.generate_content,
        model=MODEL,
        contents=prompt,
    )
    return response.text


def _build_followup_contents(report_data: dict, prompt: str, history: list, language: str = "en"):
    """Build the contents list for a follow-up chat call."""
    from string import Template
    import json

    lang_instruction = _language_instruction(language)
    system_prompt = Template(FOLLOWUP_AGENT_PROMPT).safe_substitute(
        report_json=json.dumps(report_data, indent=2),
        language_instruction=lang_instruction,
    )

    contents = [
        types.Content(role="user", parts=[types.Part.from_text(text=system_prompt)]),
        types.Content(role="model", parts=[types.Part.from_text(text="Understood. I'm ready to help.")]),
    ]

    for msg in history:
        role = "user" if getattr(msg, 'role', 'user') == 'user' else "model"
        content = getattr(msg, 'content', '')
        contents.append(types.Content(role=role, parts=[types.Part.from_text(text=content)]))

    contents.append(types.Content(role="user", parts=[types.Part.from_text(text=prompt)]))
    return contents


async def generate_followup_chat(report_data: dict, prompt: str, history: list, language: str = "en") -> str:
    contents = _build_followup_contents(report_data, prompt, history, language)
    response = await asyncio.to_thread(
        client.models.generate_content, model=MODEL, contents=contents,
    )
    return response.text


async def generate_followup_chat_stream(report_data: dict, prompt: str, history: list, language: str = "en"):
    """Async generator yielding text chunks from a streaming follow-up chat."""
    import threading

    contents = _build_followup_contents(report_data, prompt, history, language)
    loop = asyncio.get_event_loop()
    q: asyncio.Queue[str | None] = asyncio.Queue()

    def _run():
        try:
            for chunk in client.models.generate_content_stream(
                model=MODEL, contents=contents,
            ):
                if chunk.text:
                    loop.call_soon_threadsafe(q.put_nowait, chunk.text)
        except Exception as e:
            logger.error(f"Followup stream error: {e}")
        finally:
            loop.call_soon_threadsafe(q.put_nowait, None)

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()

    while True:
        item = await q.get()
        if item is None:
            break
        yield item


async def generate_followup_podcast_script(ai_response: str, prompt: str, language: str = "en") -> str:
    from string import Template

    lang_name = LANGUAGE_NAMES.get(language, language)
    lang_instruction = "" if language == "en" else f"IMPORTANT: Write the ENTIRE script in {lang_name}. The listener speaks {lang_name}."

    sys_prompt = Template(FOLLOWUP_PODCAST_PROMPT).safe_substitute(
        prompt=prompt,
        ai_response=ai_response,
        language_instruction=lang_instruction,
    )

    response = await asyncio.to_thread(
        client.models.generate_content,
        model=MODEL,
        contents=sys_prompt,
    )
    return response.text
