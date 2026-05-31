"""
Auth API Routes
===============
Authentication endpoints — placeholder stubs that return HTTP 501.

These endpoints exist so the frontend and /docs don't 404, but they do NOT
issue real tokens.  Replace this file with a real JWT + DB implementation
before any user-facing deployment.
"""

from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.core.logging import get_logger

logger = get_logger("routes.auth")

router = APIRouter(prefix="/auth", tags=["Auth"])


class LoginRequest(BaseModel):
    email: str
    password: str


class RegisterRequest(BaseModel):
    email: str
    password: str
    full_name: Optional[str] = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: Optional[str] = None
    is_active: bool = True


_NOT_IMPLEMENTED = {
    "error": "not_implemented",
    "message": (
        "Authentication is not yet implemented. "
        "Add JWT + database integration before using in production."
    ),
}


@router.post("/login")
async def login(request: LoginRequest):
    """
    Authenticate user and return access token.

    NOT IMPLEMENTED — returns 501.
    Implement: password hash verification, JWT generation, DB user lookup.
    """
    logger.warning("Login endpoint called — not implemented")
    raise HTTPException(status_code=501, detail=_NOT_IMPLEMENTED)


@router.post("/register")
async def register(request: RegisterRequest):
    """
    Register a new user.

    NOT IMPLEMENTED — returns 501.
    Implement: password hashing, email validation, DB user creation.
    """
    logger.warning("Register endpoint called — not implemented")
    raise HTTPException(status_code=501, detail=_NOT_IMPLEMENTED)


@router.get("/me")
async def get_current_user():
    """
    Get current authenticated user.

    NOT IMPLEMENTED — returns 501.
    Implement: JWT token validation, DB user lookup.
    """
    logger.warning("Get current user endpoint called — not implemented")
    raise HTTPException(status_code=501, detail=_NOT_IMPLEMENTED)
