"""Authentication via Amazon Cognito with password-derived encryption keys."""

import asyncio
import base64
import hashlib
import hmac
import logging
import os

import boto3
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

from config import (
    AWS_ACCESS_KEY_ID,
    AWS_SECRET_ACCESS_KEY,
    AWS_REGION,
    COGNITO_USER_POOL_ID,
    COGNITO_CLIENT_ID,
    COGNITO_CLIENT_SECRET,
)
from services.dynamo import save_user_salt, get_user_salt

logger = logging.getLogger("uvicorn.error")

_cognito_client = None

PBKDF2_ITERATIONS = 100_000


def _get_cognito():
    global _cognito_client
    if _cognito_client is None and COGNITO_USER_POOL_ID and COGNITO_CLIENT_ID:
        _cognito_client = boto3.client(
            "cognito-idp",
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
            region_name=AWS_REGION,
        )
    return _cognito_client


def _compute_secret_hash(username: str) -> str:
    """Compute the SECRET_HASH required when the app client has a secret."""
    msg = username + COGNITO_CLIENT_ID
    dig = hmac.new(
        COGNITO_CLIENT_SECRET.encode("utf-8"),
        msg.encode("utf-8"),
        hashlib.sha256,
    ).digest()
    return base64.b64encode(dig).decode("utf-8")


def _derive_key(password: str, salt: bytes) -> bytes:
    """Derive a 256-bit AES key from password + salt using PBKDF2."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=PBKDF2_ITERATIONS,
    )
    return kdf.derive(password.encode("utf-8"))


def _extract_user_attrs(attrs: list[dict]) -> dict:
    """Convert Cognito user attributes list to a flat dict."""
    out = {}
    for a in attrs:
        out[a["Name"]] = a["Value"]
    return out


async def cognito_signup(email: str, password: str, display_name: str) -> dict:
    """Sign up a new user, auto-confirm, and return {token, user, encryption_key}."""
    client = _get_cognito()
    if client is None:
        raise RuntimeError("Cognito not configured")

    email_lower = email.lower()
    secret_hash = _compute_secret_hash(email_lower)

    # Create user
    await asyncio.to_thread(
        client.sign_up,
        ClientId=COGNITO_CLIENT_ID,
        SecretHash=secret_hash,
        Username=email_lower,
        Password=password,
        UserAttributes=[
            {"Name": "email", "Value": email_lower},
        ],
    )

    # Auto-confirm (skip email verification for now)
    await asyncio.to_thread(
        client.admin_confirm_sign_up,
        UserPoolId=COGNITO_USER_POOL_ID,
        Username=email_lower,
    )

    # Log them in to get tokens
    auth_result = await asyncio.to_thread(
        client.admin_initiate_auth,
        UserPoolId=COGNITO_USER_POOL_ID,
        ClientId=COGNITO_CLIENT_ID,
        AuthFlow="ADMIN_USER_PASSWORD_AUTH",
        AuthParameters={
            "USERNAME": email_lower,
            "PASSWORD": password,
            "SECRET_HASH": secret_hash,
        },
    )

    tokens = auth_result["AuthenticationResult"]
    access_token = tokens["AccessToken"]

    # Get user info
    user_info = await get_user_from_token(access_token)

    # Generate salt and derive encryption key
    salt = os.urandom(16)
    salt_b64 = base64.b64encode(salt).decode("utf-8")
    await save_user_salt(user_info["id"], salt_b64)
    encryption_key = _derive_key(password, salt)

    return {
        "token": access_token,
        "user": user_info,
        "encryption_key": base64.b64encode(encryption_key).decode("utf-8"),
    }


async def cognito_login(email: str, password: str) -> dict:
    """Log in and return {token, user, encryption_key}."""
    client = _get_cognito()
    if client is None:
        raise RuntimeError("Cognito not configured")

    email_lower = email.lower()
    secret_hash = _compute_secret_hash(email_lower)

    auth_result = await asyncio.to_thread(
        client.admin_initiate_auth,
        UserPoolId=COGNITO_USER_POOL_ID,
        ClientId=COGNITO_CLIENT_ID,
        AuthFlow="ADMIN_USER_PASSWORD_AUTH",
        AuthParameters={
            "USERNAME": email_lower,
            "PASSWORD": password,
            "SECRET_HASH": secret_hash,
        },
    )

    tokens = auth_result["AuthenticationResult"]
    access_token = tokens["AccessToken"]

    user_info = await get_user_from_token(access_token)

    # Retrieve salt and derive encryption key
    salt_b64 = await get_user_salt(user_info["id"])
    if salt_b64:
        salt = base64.b64decode(salt_b64)
        encryption_key = _derive_key(password, salt)
        enc_key_b64 = base64.b64encode(encryption_key).decode("utf-8")
    else:
        # Legacy user without salt — generate one now
        salt = os.urandom(16)
        salt_b64 = base64.b64encode(salt).decode("utf-8")
        await save_user_salt(user_info["id"], salt_b64)
        encryption_key = _derive_key(password, salt)
        enc_key_b64 = base64.b64encode(encryption_key).decode("utf-8")

    return {
        "token": access_token,
        "user": user_info,
        "encryption_key": enc_key_b64,
    }


async def get_user_from_token(access_token: str) -> dict | None:
    """Verify a Cognito access token and return user info dict."""
    client = _get_cognito()
    if client is None:
        return None

    try:
        resp = await asyncio.to_thread(
            client.get_user, AccessToken=access_token
        )
    except client.exceptions.NotAuthorizedException:
        return None
    except Exception:
        return None

    attrs = _extract_user_attrs(resp.get("UserAttributes", []))
    return {
        "id": attrs.get("sub", ""),
        "email": attrs.get("email", resp.get("Username", "")),
        "display_name": attrs.get("email", resp.get("Username", "")).split("@")[0],
    }
