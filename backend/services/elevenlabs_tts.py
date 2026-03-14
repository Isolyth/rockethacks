import asyncio
import re

from elevenlabs.client import ElevenLabs

from config import ELEVENLABS_API_KEY, ELEVENLABS_VOICE_ID, ELEVENLABS_MODEL_ID, ELEVENLABS_OUTPUT_FORMAT

VOICE_ID = ELEVENLABS_VOICE_ID
MODEL_ID = ELEVENLABS_MODEL_ID
OUTPUT_FORMAT = ELEVENLABS_OUTPUT_FORMAT


def _get_client() -> ElevenLabs:
    if not ELEVENLABS_API_KEY:
        raise RuntimeError("ELEVENLABS_API_KEY not set in environment")
    return ElevenLabs(api_key=ELEVENLABS_API_KEY)


def _split_sentences(text: str) -> list[str]:
    """Split text into sentences, preserving all whitespace in output."""
    parts = re.split(r'(?<=[.!?])\s+', text.strip())
    return [p for p in parts if p.strip()]


def _build_sentence_timestamps(
    text: str,
    sentences: list[str],
    char_starts: list[float],
    char_ends: list[float],
) -> list[dict]:
    """Map character-level timestamps to sentence-level timestamps."""
    result = []
    search_from = 0

    for sentence in sentences:
        idx = text.find(sentence, search_from)
        if idx == -1:
            continue

        end_idx = idx + len(sentence) - 1

        # Clamp indices to alignment array bounds
        start_i = min(idx, len(char_starts) - 1)
        end_i = min(end_idx, len(char_ends) - 1)

        result.append({
            "text": sentence,
            "start": char_starts[start_i],
            "end": char_ends[end_i],
        })
        search_from = idx + len(sentence)

    return result


async def generate_podcast_audio(text: str, language: str = "en") -> dict:
    """Generate TTS audio with sentence-level timestamps.

    Returns dict with:
        audio_base64: str  - base64-encoded MP3
        sentences: list    - [{text, start, end}, ...]
    """
    client = _get_client()

    kwargs = dict(
        text=text,
        voice_id=VOICE_ID,
        model_id=MODEL_ID,
        output_format=OUTPUT_FORMAT,
    )
    if language != "en":
        kwargs["language_code"] = language

    response = await asyncio.to_thread(
        client.text_to_speech.convert_with_timestamps,
        **kwargs,
    )

    audio_b64 = response.audio_base_64
    sentences = _split_sentences(text)

    # Build sentence timestamps from character alignment
    alignment = response.alignment
    if alignment and alignment.character_start_times_seconds:
        sentence_data = _build_sentence_timestamps(
            text,
            sentences,
            alignment.character_start_times_seconds,
            alignment.character_end_times_seconds,
        )
    else:
        # Fallback: no timestamps, just return sentences without timing
        sentence_data = [{"text": s, "start": 0, "end": 0} for s in sentences]

    return {
        "audio_base64": audio_b64,
        "sentences": sentence_data,
    }
