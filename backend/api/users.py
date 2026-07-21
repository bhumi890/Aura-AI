"""
Users & Auth API Routes
Demo-ready onboarding (login, register, and profile/memory management).
"""

import base64
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from backend.database.connection import get_db
from backend.database.schema import (
    RegisterRequest,
    LoginRequest,
    AuthResponse,
    UserResponse,
)
from backend.database.models import User, UserProfile, Conversation, Message
from backend.database.crud import create_user, get_user_by_username, get_user, get_user_profile, upsert_user_profile
from backend.utils.logger import logger

router = APIRouter(prefix="/api/users", tags=["Users"])


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(request: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """
    Register a new user (demo-ready onboarding).
    Checks if username exists; if not, creates a new user and returns a demo token.
    """
    logger.info(f"Register request for username: {request.username}")
    existing = await get_user_by_username(db, request.username)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered. Please login or choose another."
        )

    user = await create_user(db, username=request.username, password_hash=request.password)
    await db.commit()
    await db.refresh(user)

    token = base64.b64encode(f"{user.username}:{user.id}".encode()).decode()
    return AuthResponse(user_id=user.id, username=user.username, token=token)


@router.post("/login", response_model=AuthResponse)
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    """
    Login as an existing user.
    """
    logger.info(f"Login request for username: {request.username}")
    user = await get_user_by_username(db, request.username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found. Please check your username or register a new account."
        )

    # Demo-level check: if password_hash is set, check it; otherwise allow (e.g. legacy/demo admin)
    if user.password_hash and user.password_hash != request.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid password."
        )

    token = base64.b64encode(f"{user.username}:{user.id}".encode()).decode()
    return AuthResponse(user_id=user.id, username=user.username, token=token)


@router.get("/{user_id}/profile")
async def get_profile(user_id: str, db: AsyncSession = Depends(get_db)):
    """
    Get user profile details, including stored AI memory summary and conversation counts.
    Used by Item 6 (User Background & Data Visibility).
    """
    user = await get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    profile = await get_user_profile(db, user_id)
    memory_summary = profile.memory_summary if profile and profile.memory_summary else "No background information stored yet. Chat with MindMate to build your AI profile."

    # Count conversations & messages
    conv_count_res = await db.execute(select(func.count(Conversation.id)).where(Conversation.user_id == user_id))
    conv_count = conv_count_res.scalar() or 0

    # Count messages via conversations
    msg_count_res = await db.execute(
        select(func.count(Message.id))
        .join(Conversation, Message.conversation_id == Conversation.id)
        .where(Conversation.user_id == user_id)
    )
    msg_count = msg_count_res.scalar() or 0

    return {
        "user_id": user.id,
        "username": user.username,
        "email": user.email,
        "created_at": user.created_at.isoformat() if user.created_at else None,
        "memory_summary": memory_summary,
        "last_summarized_at": profile.last_summarized_at.isoformat() if profile and profile.last_summarized_at else None,
        "conversation_count": conv_count,
        "message_count": msg_count,
    }


@router.delete("/{user_id}/profile/memory")
async def clear_ai_memory(user_id: str, db: AsyncSession = Depends(get_db)):
    """
    Clear the stored AI memory summary for this user.
    """
    profile = await get_user_profile(db, user_id)
    if profile:
        profile.memory_summary = ""
        profile.last_summarized_at = None
        await db.commit()
    return {"status": "success", "message": "AI memory cleared."}
