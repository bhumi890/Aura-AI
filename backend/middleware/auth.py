"""
Authentication Middleware
Simple user identification for the wellness companion.
Provides a lightweight auth layer — can be upgraded to JWT later.
"""

from fastapi import Request, HTTPException, Depends
from fastapi.security import APIKeyHeader
from typing import Optional
from backend.config import get_settings

settings = get_settings()

# Simple API key header (optional — for basic protection)
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def get_current_user_id(request: Request) -> str:
    """
    Extract user ID from request headers.
    For now, uses a simple X-User-Id header.
    In production, replace with JWT token validation.

    Usage in routes:
        @router.get("/data")
        async def get_data(user_id: str = Depends(get_current_user_id)):
            ...
    """
    user_id = request.headers.get("X-User-Id")
    if not user_id:
        # For development, allow a default user
        user_id = "default-user"
    return user_id


async def verify_api_key(api_key: Optional[str] = Depends(api_key_header)) -> bool:
    """
    Optional API key verification.
    Only enforced if API_SECRET_KEY is set to something other than the default.
    """
    if settings.API_SECRET_KEY == "dev-secret-key-change-in-production":
        # In development, skip API key check
        return True

    if not api_key or api_key != settings.API_SECRET_KEY:
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing API key"
        )
    return True
