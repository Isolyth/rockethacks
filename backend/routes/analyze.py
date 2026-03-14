import json
import logging
import time

from fastapi import APIRouter, UploadFile, File
from sse_starlette.sse import EventSourceResponse

from services.parser import parse_pdf, parse_csv
from services.gemini import analyze_with_gemini, generate_podcast_script
from models.schemas import FinancialReport

logger = logging.getLogger("uvicorn.error")

router = APIRouter()


@router.post("/analyze")
async def analyze_statements(files: list[UploadFile] = File(...)):
    file_names = [f.filename for f in files]
    logger.info(f"=== /analyze called with {len(files)} file(s): {file_names} ===")

    async def event_generator():
        t0 = time.time()
        try:
            # Step 1: Parse files
            logger.info("[1/4] Parsing uploaded files...")
            yield {
                "event": "progress",
                "data": json.dumps({"step": "parsing", "message": "Extracting text from uploaded files...", "percent": 10}),
            }

            all_text = ""
            for f in files:
                content = await f.read()
                filename = f.filename or "unknown"
                lower = filename.lower()
                logger.info(f"  Reading {filename} ({len(content)} bytes)")

                if lower.endswith(".pdf"):
                    text = parse_pdf(content)
                    logger.info(f"  Parsed PDF: {len(text)} chars extracted")
                elif lower.endswith(".csv"):
                    text = parse_csv(content)
                    logger.info(f"  Parsed CSV: {len(text)} chars")
                else:
                    logger.warning(f"  Unsupported file type: {filename}")
                    yield {
                        "event": "error",
                        "data": json.dumps({"message": f"Unsupported file type: {filename}. Please upload PDF or CSV files."}),
                    }
                    return
                all_text += f"\n--- {filename} ---\n{text}"

            logger.info(f"[1/4] Parsing done. Total text: {len(all_text)} chars ({time.time() - t0:.1f}s)")

            yield {
                "event": "progress",
                "data": json.dumps({"step": "parsing", "message": "Files parsed successfully", "percent": 25}),
            }

            # Step 2: Gemini analysis
            logger.info("[2/4] Sending to Gemini for financial analysis...")
            yield {
                "event": "progress",
                "data": json.dumps({"step": "analyzing", "message": "AI is analyzing your spending...", "percent": 40}),
            }

            t1 = time.time()
            report_data = await analyze_with_gemini(all_text, file_count=len(files))
            logger.info(f"[2/4] Gemini analysis done ({time.time() - t1:.1f}s)")

            report = FinancialReport(**report_data)
            logger.info(f"  Report: {len(report.categories)} categories, {len(report.insights)} insights")

            yield {
                "event": "progress",
                "data": json.dumps({"step": "analyzing", "message": "Financial report generated", "percent": 60}),
            }

            # Step 3: Podcast script
            logger.info("[3/4] Generating podcast script...")
            yield {
                "event": "progress",
                "data": json.dumps({"step": "generating", "message": "Creating your podcast script...", "percent": 75}),
            }

            t2 = time.time()
            podcast_script = await generate_podcast_script(report_data)
            logger.info(f"[3/4] Podcast script done ({time.time() - t2:.1f}s, {len(podcast_script)} chars)")

            yield {
                "event": "progress",
                "data": json.dumps({"step": "generating", "message": "Podcast script complete!", "percent": 95}),
            }

            # Step 4: Send result
            logger.info(f"[4/4] Sending result to client. Total time: {time.time() - t0:.1f}s")
            yield {
                "event": "result",
                "data": json.dumps({"report": report.model_dump(), "podcast_script": podcast_script}),
            }

        except Exception as e:
            logger.error(f"Error during analysis: {type(e).__name__}: {e}", exc_info=True)
            yield {
                "event": "error",
                "data": json.dumps({"message": str(e)}),
            }

    return EventSourceResponse(event_generator(), sep="\n")
