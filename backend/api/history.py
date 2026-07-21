"""
History API Routes
Provides conversation history with pagination.
"""

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import datetime
import math

from backend.database.connection import get_db
from backend.database.schema import PaginatedResponse, ConversationListItem, ConversationResponse
from backend.database.crud import get_user_conversations, get_conversation, delete_conversation
from backend.utils.logger import api_logger

router = APIRouter(prefix="/api/history", tags=["History"])


@router.get("/", response_model=PaginatedResponse)
async def get_history(
    user_id: str,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """
    Get conversation history for a user with pagination.

    Returns a list of conversations (without messages)
    sorted by most recent first.
    """
    api_logger.info(f"History request: user={user_id}, page={page}")

    conversations, total = await get_user_conversations(
        db,
        user_id=user_id,
        page=page,
        page_size=page_size,
    )

    items = []
    for c in conversations:
        items.append({
            "id": c.id,
            "title": c.title,
            "created_at": c.created_at.isoformat(),
            "updated_at": c.updated_at.isoformat(),
        })

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=math.ceil(total / page_size) if total > 0 else 0,
    )


@router.get("/{conversation_id}", response_model=ConversationResponse)
async def get_conversation_detail(
    conversation_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Get a single conversation including all its messages.
    """
    convo = await get_conversation(db, conversation_id)
    if not convo:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return convo


@router.delete("/{conversation_id}")
async def delete_conversation_route(
    conversation_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a conversation by ID.
    """
    success = await delete_conversation(db, conversation_id)
    if not success:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"status": "deleted"}


