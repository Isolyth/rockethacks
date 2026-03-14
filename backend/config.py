"""Centralized configuration for the backend."""

import os

from dotenv import load_dotenv

load_dotenv()

# API keys
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")

# Gemini
GEMINI_MODEL = "gemini-flash-latest"
MAX_DOCUMENT_REQUESTS = int(os.getenv("MAX_DOCUMENT_REQUESTS", "3"))

# ElevenLabs
ELEVENLABS_VOICE_ID = "JBFqnCBsd6RMkjVDRZzb"  # George
ELEVENLABS_MODEL_ID = "eleven_flash_v2_5"
ELEVENLABS_OUTPUT_FORMAT = "mp3_44100_128"

# CORS
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")


def validate():
    """Call at startup to fail fast on missing required config."""
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY not set in environment")
