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

MODEL = "gemini-flash-latest"

MAX_DOCUMENT_REQUESTS = int(os.getenv("MAX_DOCUMENT_REQUESTS", "3"))

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

3. **finish** — Use this when you have enough data and context to produce a comprehensive report. Call this with the complete financial report JSON.

4. **search_web** — Search the web for current financial data, benchmark comparisons, average spending statistics, or relevant context. Use this to ground your insights in real data — for example, comparing the user's savings rate to the national average, or referencing current interest rates. Provide a specific search query.

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
- You MUST call ask_question or request_documents at least TWICE before calling finish. Never go straight to finish.
- On your FIRST turn, always ask a question to understand the user's goals or clarify something about the data.
- On your SECOND turn, either ask another question or request a missing document.
- Only call finish after you've gathered enough context through questions/documents.
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
    REQUEST_DOCUMENTS_DECL, ASK_QUESTION_DECL, FINISH_DECL, SEARCH_WEB_DECL,
])]


async def _stream_and_collect(contents, config):
    """Stream a Gemini response, yielding thinking chunks, and return the full response."""
    collected_parts = []
    response_content = None

    for chunk in client.models.generate_content_stream(
        model=MODEL,
        contents=contents,
        config=config,
    ):
        if not chunk.candidates:
            continue
        for part in chunk.candidates[0].content.parts:
            if getattr(part, "thought", False) and part.text:
                yield ("thinking", part.text)
            elif part.function_call:
                collected_parts.append(part)
            elif part.text:
                collected_parts.append(part)
        response_content = chunk.candidates[0].content

    # Yield the final collected response so caller can process tool calls
    if response_content:
        yield ("_response", response_content)
    elif collected_parts:
        yield ("_response", types.Content(role="model", parts=collected_parts))


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
                yield ("result", _attach_grounding(json.loads(full_text)))
            except (json.JSONDecodeError, ValueError):
                yield ("error", "Agent failed to produce a valid report")
            return

        for fc in function_calls:
            if fc.name == "finish":
                report_data = fc.args.get("report", fc.args)
                logger.info("  Agent called finish")
                yield ("result", _attach_grounding(report_data))
                return

            elif fc.name == "search_web":
                query = fc.args.get("query", "")
                logger.info(f"  Agent searching web: {query}")
                yield ("thinking", f"Searching the web: {query}")

                # Make a separate Gemini call with GoogleSearch grounding.
                # This is needed because google_search tool cannot be combined
                # with function_declarations in the same request.
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
                break

            elif fc.name == "request_documents":
                interaction_count += 1
                doc_type = fc.args["document_type"]
                reason = fc.args["reason"]
                logger.info(f"  Agent requesting document: {doc_type} (interaction {interaction_count}/{max_requests})")

                # Yield pauses this generator. The route handler will set
                # session.user_response before resuming us (by requesting
                # the next item from the generator).
                yield ("request_documents", {"document_type": doc_type, "reason": reason})

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

                contents.append(response_content)
                contents.append(types.Content(role="user", parts=[func_response]))

                if interaction_count >= max_requests:
                    contents.append(
                        types.Content(
                            role="user",
                            parts=[types.Part.from_text(text="You have used all your interaction requests. Please call finish now with the best report you can produce from the available data.")],
                        )
                    )
                break

            elif fc.name == "ask_question":
                interaction_count += 1
                question = fc.args["question"]
                options = fc.args.get("options", [])
                logger.info(f"  Agent asking question: {question} (interaction {interaction_count}/{max_requests})")

                # Same pattern: yield pauses, route handler sets
                # session.user_response before resuming.
                yield ("ask_question", {"question": question, "options": options})

                user_response = session.user_response
                session.user_response = None

                answer = (user_response or {}).get("answer", "No answer provided")
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
                break

    yield ("error", "Agent exceeded maximum iterations")


async def _stream_via_thread(contents, config):
    """Run the synchronous streaming generator in a thread and yield events."""
    import queue
    import threading

    q = queue.Queue()

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
                        q.put(("thinking", part.text))
                    else:
                        # Accumulate non-thought parts (function calls, text)
                        # so they aren't lost when later chunks only have thoughts
                        collected_parts.append(part)
            q.put(("_collected_parts", collected_parts))
        except Exception as e:
            q.put(("_error", str(e)))
        finally:
            q.put(None)  # sentinel

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()

    collected_parts = []
    while True:
        # Poll queue without blocking the event loop
        while True:
            try:
                item = q.get_nowait()
                break
            except queue.Empty:
                await asyncio.sleep(0.05)
                continue

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
