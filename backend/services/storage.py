"""AWS S3 storage helpers."""

import asyncio
import logging

import boto3

from config import AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_S3_BUCKET, AWS_REGION

logger = logging.getLogger("uvicorn.error")

_s3_client = None


def _get_s3():
    global _s3_client
    if _s3_client is None and AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY:
        _s3_client = boto3.client(
            "s3",
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
            region_name=AWS_REGION,
        )
    return _s3_client


def _sanitize_filename(filename: str) -> str:
    """Strip path components and restrict to safe characters."""
    import os
    import re
    name = os.path.basename(filename)
    name = re.sub(r"[^a-zA-Z0-9._-]", "_", name)
    return name[:255] or "file"


async def upload_statement(user_id: str, statement_id: str, filename: str, content_bytes: bytes) -> str | None:
    """Upload a statement file to S3. Returns the S3 key or None if S3 not configured."""
    s3 = _get_s3()
    if s3 is None:
        return None
    safe_name = _sanitize_filename(filename)
    key = f"users/{user_id}/statements/{statement_id}_{safe_name}"
    await asyncio.to_thread(
        s3.put_object, Bucket=AWS_S3_BUCKET, Key=key, Body=content_bytes
    )
    logger.info(f"Uploaded statement to S3: {key}")
    return key


async def upload_audio(user_id: str, report_id: str, audio_bytes: bytes) -> str | None:
    """Upload podcast audio to S3. Returns the S3 key or None."""
    s3 = _get_s3()
    if s3 is None:
        return None
    key = f"users/{user_id}/audio/{report_id}.mp3"
    await asyncio.to_thread(
        s3.put_object, Bucket=AWS_S3_BUCKET, Key=key, Body=audio_bytes, ContentType="audio/mpeg"
    )
    logger.info(f"Uploaded audio to S3: {key}")
    return key


async def get_statement_bytes(s3_key: str) -> bytes:
    """Download a statement file from S3."""
    s3 = _get_s3()
    if s3 is None:
        raise RuntimeError("S3 not configured")
    resp = await asyncio.to_thread(
        s3.get_object, Bucket=AWS_S3_BUCKET, Key=s3_key
    )
    return resp["Body"].read()


async def generate_presigned_url(s3_key: str, expires: int = 3600,
                                 download_filename: str | None = None) -> str | None:
    """Generate a presigned URL for a file in S3."""
    s3 = _get_s3()
    if s3 is None:
        return None
    params: dict = {"Bucket": AWS_S3_BUCKET, "Key": s3_key}
    if download_filename:
        params["ResponseContentDisposition"] = f'attachment; filename="{download_filename}"'
    return await asyncio.to_thread(
        s3.generate_presigned_url,
        "get_object",
        Params=params,
        ExpiresIn=expires,
    )
