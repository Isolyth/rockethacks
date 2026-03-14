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

# AWS
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
AWS_S3_BUCKET = os.getenv("AWS_S3_BUCKET", "monai-uploads")

# Cognito
COGNITO_USER_POOL_ID = os.getenv("COGNITO_USER_POOL_ID")
COGNITO_CLIENT_ID = os.getenv("COGNITO_CLIENT_ID")
COGNITO_CLIENT_SECRET = os.getenv("COGNITO_CLIENT_SECRET")

# DynamoDB
DYNAMO_REPORTS_TABLE = os.getenv("DYNAMO_REPORTS_TABLE", "monai-reports")
DYNAMO_STATEMENTS_TABLE = os.getenv("DYNAMO_STATEMENTS_TABLE", "monai-statements")
DYNAMO_USER_SALTS_TABLE = os.getenv("DYNAMO_USER_SALTS_TABLE", "monai-user-salts")

# CORS
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")


def validate():
    """Call at startup to fail fast on missing required config."""
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY not set in environment")
