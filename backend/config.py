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

# Security / limits
MAX_FILE_SIZE_BYTES = int(os.getenv("MAX_FILE_SIZE_MB", "10")) * 1024 * 1024  # 10 MB default
MAX_FILES_PER_UPLOAD = int(os.getenv("MAX_FILES_PER_UPLOAD", "10"))
WS_RECEIVE_TIMEOUT = int(os.getenv("WS_RECEIVE_TIMEOUT", "300"))  # 5 min
MAX_WS_CONNECTIONS_PER_IP = int(os.getenv("MAX_WS_CONNECTIONS_PER_IP", "5"))
MAX_TEXT_LENGTH = int(os.getenv("MAX_TEXT_LENGTH", "500000"))  # 500K chars
MAX_PDF_PAGES = int(os.getenv("MAX_PDF_PAGES", "200"))
AUTH_RATE_LIMIT_REQUESTS = int(os.getenv("AUTH_RATE_LIMIT_REQUESTS", "10"))
AUTH_RATE_LIMIT_WINDOW = int(os.getenv("AUTH_RATE_LIMIT_WINDOW", "60"))  # seconds


def validate():
    """Call at startup to fail fast on missing required config."""
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY not set in environment")
