import base64
import json
import logging
import time
import uuid

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from services.parser import parse_pdf, parse_csv
from services.gemini import analyze_with_gemini_agent, generate_podcast_script
from services.elevenlabs_tts import generate_podcast_audio
from services.session import Session, sessions
from models.schemas import FinancialReport

logger = logging.getLogger("uvicorn.error")

router = APIRouter()


async def send_json(ws: WebSocket, data: dict):
    await ws.send_text(json.dumps(data))


def parse_file_data(name: str, content_bytes: bytes) -> str | None:
    """Parse a file's bytes into text. Returns None if unsupported type."""
    lower = name.lower()
    if lower.endswith(".pdf"):
        return parse_pdf(content_bytes)
    elif lower.endswith(".csv"):
        return parse_csv(content_bytes)
    return None


@router.websocket("/ws/analyze")
async def ws_analyze(ws: WebSocket):
    await ws.accept()
    session_id = uuid.uuid4().hex
    session = Session(session_id=session_id)
    sessions[session_id] = session

    try:
        # Step 1: Receive initial files from client
        raw = await ws.receive_text()
        msg = json.loads(raw)

        if msg.get("type") != "upload_files" or not msg.get("files"):
            await send_json(ws, {"type": "error", "message": "Expected upload_files message with files"})
            return

        t0 = time.time()
        files = msg["files"]
        file_names = [f["name"] for f in files]
        logger.info(f"=== WS /ws/analyze with {len(files)} file(s): {file_names} ===")

        await send_json(ws, {
            "type": "progress",
            "step": "parsing",
            "message": "Extracting text from uploaded files...",
            "percent": 10,
        })

        # Parse all files
        all_text = ""
        for f in files:
            name = f["name"]
            content_bytes = base64.b64decode(f["content"])
            logger.info(f"  Reading {name} ({len(content_bytes)} bytes)")

            text = parse_file_data(name, content_bytes)
            if text is None:
                await send_json(ws, {
                    "type": "error",
                    "message": f"Unsupported file type: {name}. Please upload PDF or CSV files.",
                })
                return

            logger.info(f"  Parsed: {len(text)} chars extracted")
            all_text += f"\n--- {name} ---\n{text}"

        logger.info(f"[1/4] Parsing done. Total text: {len(all_text)} chars ({time.time() - t0:.1f}s)")
        await send_json(ws, {
            "type": "progress",
            "step": "parsing",
            "message": "Files parsed successfully",
            "percent": 25,
        })

        # Step 2: Agentic Gemini analysis
        logger.info("[2/4] Starting agentic Gemini analysis...")
        await send_json(ws, {
            "type": "progress",
            "step": "analyzing",
            "message": "AI is analyzing your spending...",
            "percent": 40,
        })

        t1 = time.time()
        report_data = None

        async for event_type, event_data in analyze_with_gemini_agent(
            all_text, file_count=len(files), session=session
        ):
            if event_type == "thinking":
                await send_json(ws, {
                    "type": "thinking",
                    "text": event_data,
                })

            elif event_type == "request_documents":
                logger.info(f"  Agent requesting: {event_data['document_type']}")
                await send_json(ws, {
                    "type": "request_documents",
                    "document_type": event_data["document_type"],
                    "reason": event_data["reason"],
                })

                # Wait for client response
                raw_resp = await ws.receive_text()
                resp_msg = json.loads(raw_resp)

                if resp_msg.get("type") == "upload_files" and resp_msg.get("files"):
                    new_text = ""
                    for f in resp_msg["files"]:
                        name = f["name"]
                        content_bytes = base64.b64decode(f["content"])
                        text = parse_file_data(name, content_bytes)
                        if text:
                            new_text += f"\n--- {name} ---\n{text}"
                            logger.info(f"  Additional file: {name} ({len(text)} chars)")

                    session.user_response = {"action": "upload", "document_text": new_text}
                else:
                    logger.info("  User skipped document request")
                    session.user_response = {"action": "skip"}

                await send_json(ws, {
                    "type": "progress",
                    "step": "analyzing",
                    "message": "Continuing analysis...",
                    "percent": 55,
                })

            elif event_type == "ask_question":
                logger.info(f"  Agent asking: {event_data['question']}")
                await send_json(ws, {
                    "type": "ask_question",
                    "question": event_data["question"],
                    "options": event_data["options"],
                })

                # Wait for client answer
                raw_resp = await ws.receive_text()
                resp_msg = json.loads(raw_resp)

                answer = resp_msg.get("answer", "No answer provided")
                logger.info(f"  User answered: {answer}")
                session.user_response = {"answer": answer}

                await send_json(ws, {
                    "type": "progress",
                    "step": "analyzing",
                    "message": "Continuing analysis...",
                    "percent": 55,
                })

            elif event_type == "result":
                report_data = event_data
                logger.info(f"[2/5] Gemini analysis done ({time.time() - t1:.1f}s)")

            elif event_type == "error":
                await send_json(ws, {"type": "error", "message": event_data})
                return

        if report_data is None:
            await send_json(ws, {"type": "error", "message": "Analysis failed to produce a report"})
            return

        # Validate report
        report = FinancialReport(**report_data)
        logger.info(f"  Report: {len(report.categories)} categories, {len(report.insights)} insights")

        await send_json(ws, {
            "type": "progress",
            "step": "analyzing",
            "message": "Financial report generated",
            "percent": 50,
        })

        # Send report immediately so frontend can display it
        logger.info("[2/5] Sending report to client")
        await send_json(ws, {
            "type": "report_ready",
            "report": report.model_dump(),
        })

        # Step 3: Podcast script
        logger.info("[3/5] Generating podcast script...")
        await send_json(ws, {
            "type": "progress",
            "step": "generating",
            "message": "Creating your podcast script...",
            "percent": 60,
        })

        t2 = time.time()
        podcast_script = await generate_podcast_script(report_data)
        logger.info(f"[3/5] Podcast script done ({time.time() - t2:.1f}s, {len(podcast_script)} chars)")

        await send_json(ws, {
            "type": "progress",
            "step": "generating",
            "message": "Podcast script complete!",
            "percent": 70,
        })

        # Step 4: Generate TTS audio with ElevenLabs
        logger.info("[4/5] Generating podcast audio...")
        await send_json(ws, {
            "type": "progress",
            "step": "narrating",
            "message": "Generating audio narration...",
            "percent": 80,
        })

        t3 = time.time()
        try:
            audio_result = await generate_podcast_audio(podcast_script)
            logger.info(f"[4/5] Audio done ({time.time() - t3:.1f}s, {len(audio_result['sentences'])} sentences)")

            await send_json(ws, {
                "type": "progress",
                "step": "narrating",
                "message": "Audio narration complete!",
                "percent": 95,
            })

            # Step 5: Send podcast audio
            logger.info(f"[5/5] Sending result. Total time: {time.time() - t0:.1f}s")
            await send_json(ws, {
                "type": "podcast_audio_ready",
                "podcast_script": podcast_script,
                "audio_base64": audio_result["audio_base64"],
                "sentences": audio_result["sentences"],
            })
        except Exception as e:
            logger.error(f"[4/5] ElevenLabs TTS failed: {e}", exc_info=True)
            await send_json(ws, {
                "type": "progress",
                "step": "narrating",
                "message": "Audio generation failed — showing script only",
                "percent": 95,
            })
            # Fallback: send script without audio
            await send_json(ws, {
                "type": "podcast_audio_ready",
                "podcast_script": podcast_script,
                "audio_base64": None,
                "sentences": [],
            })

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected (session {session_id})")
    except Exception as e:
        logger.error(f"Error during analysis: {type(e).__name__}: {e}", exc_info=True)
        try:
            await send_json(ws, {"type": "error", "message": str(e)})
        except Exception:
            pass
    finally:
        session.active = False
        sessions.pop(session_id, None)
