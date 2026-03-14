"""Authentication endpoints using Amazon Cognito."""

import logging

from fastapi import APIRouter, Depends, Header, HTTPException

from models.schemas import AuthResponse, LoginRequest, SignupRequest, UserResponse
from services.auth import cognito_login, cognito_signup, get_user_from_token

logger = logging.getLogger("uvicorn.error")
router = APIRouter(prefix="/auth", tags=["auth"])


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
async def signup(req: SignupRequest):
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
    )


@router.post("/login", response_model=AuthResponse)
async def login(req: LoginRequest):
    try:
        result = await cognito_login(req.email, req.password)
    except Exception as e:
        detail = str(e)
        if "NotAuthorizedException" in detail or "UserNotFoundException" in detail:
            raise HTTPException(status_code=401, detail="Invalid email or password")
        logger.error(f"Login error: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail="Login failed")

    return AuthResponse(
        token=result["token"],
        user=UserResponse(**result["user"]),
    )


@router.get("/me", response_model=UserResponse)
async def me(user: dict = Depends(get_current_user)):
    return UserResponse(**user)
