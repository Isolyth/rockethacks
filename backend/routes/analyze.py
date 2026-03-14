import asyncio
import base64
import json
import logging
import re
import time
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request, WebSocket, WebSocketDisconnect

from config import (
    MAX_FILE_SIZE_BYTES,
    MAX_FILES_PER_UPLOAD,
    MAX_TEXT_LENGTH,
    MAX_WS_CONNECTIONS_PER_IP,
    WS_RECEIVE_TIMEOUT,
)
from services.parser import parse_pdf, parse_csv
from services.gemini import analyze_with_gemini_agent, generate_podcast_script
from services.elevenlabs_tts import generate_podcast_audio
from services.session import Session, sessions
from services.auth import get_user_from_token
from services.dynamo import save_report, save_statement, get_statement
from services.encryption import encrypt_bytes, decrypt_bytes
from services.storage import upload_statement, upload_audio, get_statement_bytes
from services.rate_limit import track_ws_connection, release_ws_connection, RateLimiter
from models.schemas import FinancialReport, FollowUpRequest, FollowUpResponse

logger = logging.getLogger("uvicorn.error")

router = APIRouter()


async def send_json(ws: WebSocket, data: dict):
    await ws.send_text(json.dumps(data))


async def send_progress(ws: WebSocket, step: str, message: str, percent: int):
    await send_json(ws, {"type": "progress", "step": step, "message": message, "percent": percent})


async def _receive_json(ws: WebSocket) -> dict:
    """Receive and parse a JSON message with timeout."""
    raw = await asyncio.wait_for(ws.receive_text(), timeout=WS_RECEIVE_TIMEOUT)
    return json.loads(raw)


def _get_client_ip(ws: WebSocket) -> str:
    """Extract client IP from WebSocket connection."""
    if ws.client:
        return ws.client.host
    return "unknown"


def parse_file_data(name: str, content_bytes: bytes) -> str | None:
    """Parse a file's bytes into text. Returns None if unsupported type."""
    lower = name.lower()
    if lower.endswith(".pdf"):
        return parse_pdf(content_bytes)
    elif lower.endswith(".csv"):
        return parse_csv(content_bytes)
    return None


def sanitize_filename(filename: str) -> str:
    """Sanitize filename to prevent path traversal and XSS."""
    if not isinstance(filename, str):
        filename = "unnamed"
    # Keep only alphanumeric chars, dots, dashes, and underscores
    clean_name = re.sub(r'[^a-zA-Z0-9.\-_]', '_', filename)
    # Prevent directory traversal attempts
    clean_name = clean_name.replace('..', '_')
    # Prevent empty filename or just extension
    if not clean_name or clean_name.startswith('.'):
        clean_name = "unnamed_file" + (clean_name if '.' in clean_name else "")
    # Restrict length
    return clean_name[:255]


def _validate_files(files: list[dict]) -> str | None:
    """Validate file count and sizes. Returns error message or None."""
    if len(files) > MAX_FILES_PER_UPLOAD:
        return f"Too many files. Maximum is {MAX_FILES_PER_UPLOAD}."
    for f in files:
        content = f.get("content", "")
        # base64 is ~4/3 the size of the raw data
        estimated_size = len(content) * 3 // 4
        if estimated_size > MAX_FILE_SIZE_BYTES:
            max_mb = MAX_FILE_SIZE_BYTES // (1024 * 1024)
            return f"File '{f['name']}' exceeds the {max_mb} MB size limit."
    return None


async def _save_statement_to_aws(user_id: str, name: str, content_bytes: bytes,
                                  encryption_key: bytes | None = None) -> str | None:
    """Save a statement to S3 and DynamoDB. Encrypts if key provided. Returns statement_id."""
    statement_id = uuid.uuid4().hex
    file_type = "pdf" if name.lower().endswith(".pdf") else "csv"

    store_bytes = encrypt_bytes(encryption_key, content_bytes) if encryption_key else content_bytes
    s3_key = await upload_statement(user_id, statement_id, name, store_bytes)

    await save_statement(user_id, statement_id, {
        "uploaded_at": datetime.now(timezone.utc).isoformat(),
        "filename": name,
        "s3_key": s3_key or "",
        "file_size": len(content_bytes),
        "file_type": file_type,
        "encrypted": bool(encryption_key),
    })
    return statement_id


async def _save_report_to_aws(user_id: str, report_data: dict, podcast_script: str,
                               audio_base64: str | None, sentences: list[dict],
                               language: str, statement_ids: list[str]) -> str | None:
    """Save a completed report to DynamoDB (and audio to S3). Returns report_id."""
    report_id = uuid.uuid4().hex

    # Upload audio to S3 if present
    audio_s3_key = None
    if audio_base64:
        audio_bytes = base64.b64decode(audio_base64)
        audio_s3_key = await upload_audio(user_id, report_id, audio_bytes)

    # Derive title from date_range
    date_range = report_data.get("summary", {}).get("date_range", "")
    title = f"{date_range} Analysis" if date_range else "Financial Analysis"

    await save_report(user_id, report_id, {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "language": language,
        "title": title,
        "report": report_data,
        "podcast_script": podcast_script,
        "audio_s3_key": audio_s3_key,
        "sentences": sentences,
        "statement_ids": statement_ids,
    })

    logger.info(f"Saved report {report_id} for user {user_id}")
    return report_id


async def _parse_and_save_files(files: list[dict], user_id: str | None,
                                encryption_key: bytes | None = None):
    """Parse uploaded files and optionally save to S3/DynamoDB.

    Returns (all_text, statement_ids, file_count) or (None, bad_filename, []) on error.
    """
    text_parts = []
    statement_ids = []
    save_tasks = []

    for f in files:
        name = f["name"]
        content_bytes = base64.b64decode(f["content"])
        logger.info(f"  Reading {name} ({len(content_bytes)} bytes)")

        text = parse_file_data(name, content_bytes)
        if text is None:
            return None, name, []

        logger.info(f"  Parsed: {len(text)} chars extracted")
        text_parts.append(f"\n--- {name} ---\n{text}")

        if user_id:
            save_tasks.append(_save_statement_to_aws(user_id, name, content_bytes, encryption_key))

    # Save statements concurrently
    if save_tasks:
        results = await asyncio.gather(*save_tasks, return_exceptions=True)
        for r in results:
            if isinstance(r, str):
                statement_ids.append(r)
            elif isinstance(r, Exception):
                logger.error(f"Failed to save statement: {r}")

    return "".join(text_parts), None, statement_ids


@router.websocket("/ws/analyze")
async def ws_analyze(ws: WebSocket, token: str | None = None, enc_key: str | None = None):
    client_ip = _get_client_ip(ws)

    # Enforce per-IP connection limit
    if not track_ws_connection(client_ip, MAX_WS_CONNECTIONS_PER_IP):
        await ws.close(code=4029, reason="Too many connections")
        return

    # Authenticate before accepting connection
    user_info = None
    if token:
        user_info = await get_user_from_token(token)
        if user_info is None:
            await ws.close(code=4001, reason="Invalid token")
            release_ws_connection(client_ip)
            return

    await ws.accept()
    session_id = uuid.uuid4().hex
    session = Session(session_id=session_id)
    
    if user_info:
        session.user_id = user_info["id"]
        if enc_key:
            session.encryption_key = base64.b64decode(enc_key)
        logger.info(f"Authenticated WebSocket session for user {session.user_id}")
        
    sessions[session_id] = session

    try:
        # Step 1: Receive initial message
        try:
            msg = await _receive_json(ws)
        except (json.JSONDecodeError, asyncio.TimeoutError):
            await send_json(ws, {"type": "error", "message": "Invalid or missing initial message"})
            return

        t0 = time.time()
        language = msg.get("language", "en")
        session.language = language
        statement_ids: list[str] = []

        msg_type = msg.get("type")

        if msg_type == "use_saved_statements":
            # Authenticated user re-analyzing saved statements
            if not session.user_id:
                await send_json(ws, {"type": "error", "message": "Authentication required for saved statements"})
                return

            saved_ids = msg.get("statement_ids", [])
            new_files = msg.get("files", [])

            # Validate new files if any
            if new_files:
                for f in new_files:
                    f["name"] = sanitize_filename(f.get("name", "unnamed"))
                file_error = _validate_files(new_files)
                if file_error:
                    await send_json(ws, {"type": "error", "message": file_error})
                    return

            logger.info(f"=== WS /ws/analyze with {len(saved_ids)} saved + {len(new_files)} new file(s) lang={language} ===")
            await send_progress(ws, "parsing", "Loading saved statements...", 10)

            # Load saved statements from S3
            text_parts = []
            for sid in saved_ids:
                stmt = await get_statement(session.user_id, sid)
                if stmt and stmt.get("s3_key"):
                    try:
                        raw_bytes = await get_statement_bytes(stmt["s3_key"])
                        content_bytes = decrypt_bytes(session.encryption_key, raw_bytes) if session.encryption_key and stmt.get("encrypted") else raw_bytes
                        text = parse_file_data(stmt["filename"], content_bytes)
                        if text:
                            text_parts.append(f"\n--- {stmt['filename']} ---\n{text}")
                            statement_ids.append(sid)
                            logger.info(f"  Loaded saved: {stmt['filename']} ({len(text)} chars)")
                    except Exception as e:
                        logger.error(f"  Failed to load saved statement {sid}: {e}")

            # Parse and save new files
            if new_files:
                all_new_text, bad_name, new_sids = await _parse_and_save_files(new_files, session.user_id, session.encryption_key)
                if all_new_text is None:
                    await send_json(ws, {
                        "type": "error",
                        "message": f"Unsupported file type: {bad_name}. Please upload PDF or CSV files.",
                    })
                    return
                text_parts.append(all_new_text)
                statement_ids.extend(new_sids)

            all_text = "".join(text_parts)
            file_count = len(saved_ids) + len(new_files)

        elif msg_type == "upload_files" and msg.get("files"):
            files = msg["files"]
            for f in files:
                f["name"] = sanitize_filename(f.get("name", "unnamed"))

            # Validate file count and sizes
            file_error = _validate_files(files)
            if file_error:
                await send_json(ws, {"type": "error", "message": file_error})
                return

            file_names = [f["name"] for f in files]
            logger.info(f"=== WS /ws/analyze with {len(files)} file(s): {file_names} lang={language} ===")

            await send_progress(ws, "parsing", "Extracting text from uploaded files...", 10)

            all_text, bad_name, statement_ids = await _parse_and_save_files(files, session.user_id, session.encryption_key)
            if all_text is None:
                await send_json(ws, {
                    "type": "error",
                    "message": f"Unsupported file type: {bad_name}. Please upload PDF or CSV files.",
                })
                return

            file_count = len(files)

        else:
            await send_json(ws, {"type": "error", "message": "Expected upload_files or use_saved_statements message"})
            return

        if not all_text.strip():
            await send_json(ws, {"type": "error", "message": "No text could be extracted from the files"})
            return

        # Truncate text to prevent excessive API costs
        if len(all_text) > MAX_TEXT_LENGTH:
            logger.warning(f"Truncating text from {len(all_text)} to {MAX_TEXT_LENGTH} chars")
            all_text = all_text[:MAX_TEXT_LENGTH]

        logger.info(f"[1/5] Parsing done. Total text: {len(all_text)} chars ({time.time() - t0:.1f}s)")
        await send_progress(ws, "parsing", "Files parsed successfully", 25)

        # Step 2: Agentic Gemini analysis
        logger.info("[2/5] Starting agentic Gemini analysis...")
        await send_progress(ws, "analyzing", "AI is analyzing your spending...", 40)

        t1 = time.time()
        report_data = None

        async for event_type, event_data in analyze_with_gemini_agent(
            all_text, file_count=file_count, session=session, language=language
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

                # Wait for client response (with timeout)
                try:
                    resp_msg = await _receive_json(ws)
                except (json.JSONDecodeError, asyncio.TimeoutError):
                    await send_json(ws, {"type": "error", "message": "Invalid response or timeout"})
                    return

                if resp_msg.get("type") == "upload_files" and resp_msg.get("files"):
                    new_files = resp_msg["files"]
                    for f in new_files:
                        f["name"] = sanitize_filename(f.get("name", "unnamed"))
                    file_error = _validate_files(new_files)
                    if file_error:
                        await send_json(ws, {"type": "error", "message": file_error})
                        return

                    new_parts = []
                    for f in new_files:
                        name = f["name"]
                        content_bytes = base64.b64decode(f["content"])
                        text = parse_file_data(name, content_bytes)
                        if text:
                            new_parts.append(f"\n--- {name} ---\n{text}")
                            logger.info(f"  Additional file: {name} ({len(text)} chars)")

                            # Save additional files for authenticated users
                            if session.user_id:
                                try:
                                    sid = await _save_statement_to_aws(session.user_id, name, content_bytes, session.encryption_key)
                                    if sid:
                                        statement_ids.append(sid)
                                except Exception as e:
                                    logger.error(f"Failed to save additional statement: {e}")

                    session.user_response = {"action": "upload", "document_text": "".join(new_parts)}
                else:
                    logger.info("  User skipped document request")
                    session.user_response = {"action": "skip"}

                await send_progress(ws, "analyzing", "Continuing analysis...", 55)

            elif event_type == "ask_question":
                logger.info(f"  Agent asking: {event_data['question']}")
                await send_json(ws, {
                    "type": "ask_question",
                    "question": event_data["question"],
                    "options": event_data["options"],
                })

                # Wait for client answer (with timeout)
                try:
                    resp_msg = await _receive_json(ws)
                except (json.JSONDecodeError, asyncio.TimeoutError):
                    await send_json(ws, {"type": "error", "message": "Invalid response or timeout"})
                    return

                answer = resp_msg.get("answer", "No answer provided")
                logger.info(f"  User answered: {answer}")
                session.user_response = {"answer": answer}

                await send_progress(ws, "analyzing", "Continuing analysis...", 55)

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

        await send_progress(ws, "analyzing", "Financial report generated", 50)

        # Send report immediately so frontend can display it
        logger.info("[3/5] Sending report to client")
        await send_json(ws, {
            "type": "report_ready",
            "report": report.model_dump(),
        })

        # Step 3: Podcast script
        logger.info("[3/5] Generating podcast script...")
        await send_progress(ws, "generating", "Creating your podcast script...", 60)

        t2 = time.time()
        podcast_script = await generate_podcast_script(report_data, language=language)
        logger.info(f"[3/5] Podcast script done ({time.time() - t2:.1f}s, {len(podcast_script)} chars)")
        await send_progress(ws, "generating", "Podcast script complete!", 70)

        # Step 4: Generate TTS audio with ElevenLabs
        logger.info("[4/5] Generating podcast audio...")
        await send_progress(ws, "narrating", "Generating audio narration...", 80)

        t3 = time.time()
        audio_base64_result = None
        sentences_result = []
        try:
            audio_result = await generate_podcast_audio(podcast_script, language=language)
            audio_base64_result = audio_result["audio_base64"]
            sentences_result = audio_result["sentences"]
            logger.info(f"[4/5] Audio done ({time.time() - t3:.1f}s, {len(sentences_result)} sentences)")
            await send_progress(ws, "narrating", "Audio narration complete!", 95)
        except Exception as e:
            logger.error(f"[4/5] ElevenLabs TTS failed: {e}", exc_info=True)
            await send_progress(ws, "narrating", "Audio generation failed — showing script only", 95)

        # Save report for authenticated users
        report_id = None
        if session.user_id:
            try:
                report_id = await _save_report_to_aws(
                    session.user_id, report_data, podcast_script,
                    audio_base64_result, sentences_result,
                    language, statement_ids,
                )
            except Exception as e:
                logger.error(f"Failed to save report: {e}", exc_info=True)

        # Step 5: Send podcast audio
        logger.info(f"[5/5] Sending result. Total time: {time.time() - t0:.1f}s")
        response = {
            "type": "podcast_audio_ready",
            "podcast_script": podcast_script,
            "audio_base64": audio_base64_result,
            "sentences": sentences_result,
        }
        if report_id:
            response["report_id"] = report_id
        await send_json(ws, response)

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected (session {session_id})")
    except asyncio.TimeoutError:
        logger.info(f"WebSocket timed out (session {session_id})")
        try:
            await send_json(ws, {"type": "error", "message": "Connection timed out"})
        except Exception:
            pass
    except Exception as e:
        logger.error(f"Error during analysis: {type(e).__name__}: {e}", exc_info=True)
        try:
            await send_json(ws, {"type": "error", "message": "An internal error occurred. Please try again."})
        except Exception:
            pass
    finally:
        session.active = False
        sessions.pop(session_id, None)
        release_ws_connection(client_ip)


_followup_limiter = RateLimiter(max_requests=20, window_seconds=60)


@router.post("/analyze/follow-up")
async def analyze_followup(request: FollowUpRequest, raw_request: Request):
    """Stream a follow-up response via SSE."""
    from starlette.responses import StreamingResponse
    from services.gemini import generate_followup_chat_stream, generate_followup_podcast_script

    client_ip = raw_request.client.host if raw_request.client else "unknown"
    if not _followup_limiter.is_allowed(client_ip):
        raise HTTPException(status_code=429, detail="Too many requests. Please try again later.")

    async def event_stream():
        t0 = time.time()
        logger.info(f"=== POST /analyze/follow-up (stream) lang={request.language} ===")
        full_text = ""

        try:
            async for chunk in generate_followup_chat_stream(
                report_data=request.report_data,
                prompt=request.prompt,
                history=request.history,
                language=request.language,
            ):
                full_text += chunk
                yield f"data: {json.dumps({'type': 'chunk', 'text': chunk})}\n\n"

            logger.info(f"  [1/2] Follow-up stream done ({time.time() - t0:.1f}s)")

            t1 = time.time()
            podcast_script = await generate_followup_podcast_script(
                ai_response=full_text,
                prompt=request.prompt,
                language=request.language,
            )
            logger.info(f"  [2/2] Follow-up script done ({time.time() - t1:.1f}s)")

            yield f"data: {json.dumps({'type': 'done', 'full_text': full_text, 'podcast_script': podcast_script})}\n\n"
        except Exception as e:
            logger.error(f"Error during follow-up stream: {e}", exc_info=True)
            yield f"data: {json.dumps({'type': 'error', 'message': 'An internal error occurred.'})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
