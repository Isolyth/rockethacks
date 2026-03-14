"""Authentication endpoints using Amazon Cognito."""

import logging

from fastapi import APIRouter, Depends, Header, HTTPException, Request

from config import (
    AUTH_RATE_LIMIT_REQUESTS,
    AUTH_RATE_LIMIT_WINDOW,
    LOGIN_MAX_FAILURES,
    LOGIN_LOCKOUT_WINDOW,
)
from models.schemas import AuthResponse, LoginRequest, SignupRequest, UserResponse
from services.auth import cognito_login, cognito_signup, get_user_from_token
from services.rate_limit import RateLimiter, FailedLoginLimiter

logger = logging.getLogger("uvicorn.error")
router = APIRouter(prefix="/auth", tags=["auth"])

_auth_limiter = RateLimiter(
    max_requests=AUTH_RATE_LIMIT_REQUESTS,
    window_seconds=AUTH_RATE_LIMIT_WINDOW,
)

_failed_login_limiter = FailedLoginLimiter(
    max_failures=LOGIN_MAX_FAILURES,
    lockout_window_seconds=LOGIN_LOCKOUT_WINDOW,
)


def _check_rate_limit(request: Request):
    """Raise 429 if client IP exceeds auth rate limit."""
    client_ip = request.client.host if request.client else "unknown"
    if not _auth_limiter.is_allowed(client_ip):
        raise HTTPException(status_code=429, detail="Too many requests. Please try again later.")


async def get_current_user(authorization: str = Header(...)) -> dict:
    """Dependency that extracts and validates the Cognito access token."""
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")

    token = authorization[7:]
    user = await get_user_from_token(token)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return user


@router.post("/signup", response_model=AuthResponse)
async def signup(req: SignupRequest, request: Request):
    _check_rate_limit(request)
    try:
        result = await cognito_signup(
            req.email, req.password, req.display_name or ""
        )
    except Exception as e:
        detail = str(e)
        if "UsernameExistsException" in detail:
            raise HTTPException(status_code=409, detail="Email already registered")
        if "InvalidPasswordException" in detail:
            raise HTTPException(status_code=400, detail="Password does not meet requirements")
        logger.error(f"Signup error: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail="Signup failed")

    return AuthResponse(
        token=result["token"],
        user=UserResponse(**result["user"]),
        encryption_key=result.get("encryption_key"),
    )


@router.post("/login", response_model=AuthResponse)
async def login(req: LoginRequest, request: Request):
    _check_rate_limit(request)
    
    email_key = req.email.lower()
    if _failed_login_limiter.is_locked(email_key):
        raise HTTPException(status_code=429, detail="Too many failed login attempts. Please wait 6 minutes.")
        
    try:
        result = await cognito_login(req.email, req.password)
        _failed_login_limiter.clear(email_key)
    except Exception as e:
        detail = str(e)
        if "NotAuthorizedException" in detail or "UserNotFoundException" in detail:
            _failed_login_limiter.add_failure(email_key)
            raise HTTPException(status_code=401, detail="Invalid email or password")
        logger.error(f"Login error: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail="Login failed")

    return AuthResponse(
        token=result["token"],
        user=UserResponse(**result["user"]),
        encryption_key=result.get("encryption_key"),
    )


@router.get("/me", response_model=UserResponse)
async def me(user: dict = Depends(get_current_user)):
    return UserResponse(**user)
