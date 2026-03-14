"""Authentication via Amazon Cognito."""

import asyncio
import logging

import boto3

from config import (
    AWS_ACCESS_KEY_ID,
    AWS_SECRET_ACCESS_KEY,
    AWS_REGION,
    COGNITO_USER_POOL_ID,
    COGNITO_CLIENT_ID,
)

logger = logging.getLogger("uvicorn.error")

_cognito_client = None


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


def _extract_user_attrs(attrs: list[dict]) -> dict:
    """Convert Cognito user attributes list to a flat dict."""
    out = {}
    for a in attrs:
        out[a["Name"]] = a["Value"]
    return out


async def cognito_signup(email: str, password: str, display_name: str) -> dict:
    """Sign up a new user, auto-confirm, and return {token, user}."""
    client = _get_cognito()
    if client is None:
        raise RuntimeError("Cognito not configured")

    email_lower = email.lower()
    name = display_name or email_lower.split("@")[0]

    # Create user
    await asyncio.to_thread(
        client.sign_up,
        ClientId=COGNITO_CLIENT_ID,
        Username=email_lower,
        Password=password,
        UserAttributes=[
            {"Name": "email", "Value": email_lower},
            {"Name": "custom:display_name", "Value": name},
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
        AuthParameters={"USERNAME": email_lower, "PASSWORD": password},
    )

    tokens = auth_result["AuthenticationResult"]
    access_token = tokens["AccessToken"]

    # Get user info
    user_info = await get_user_from_token(access_token)

    return {"token": access_token, "user": user_info}


async def cognito_login(email: str, password: str) -> dict:
    """Log in and return {token, user}."""
    client = _get_cognito()
    if client is None:
        raise RuntimeError("Cognito not configured")

    auth_result = await asyncio.to_thread(
        client.admin_initiate_auth,
        UserPoolId=COGNITO_USER_POOL_ID,
        ClientId=COGNITO_CLIENT_ID,
        AuthFlow="ADMIN_USER_PASSWORD_AUTH",
        AuthParameters={"USERNAME": email.lower(), "PASSWORD": password},
    )

    tokens = auth_result["AuthenticationResult"]
    access_token = tokens["AccessToken"]

    user_info = await get_user_from_token(access_token)

    return {"token": access_token, "user": user_info}


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
        "display_name": attrs.get("custom:display_name", attrs.get("email", "").split("@")[0]),
    }
