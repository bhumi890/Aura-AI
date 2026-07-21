"""
Journal API Routes
Handles journal entry creation, retrieval, and management.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from backend.database.connection import get_db
from backend.database.schema import (
    JournalCreate,
    JournalUpdate,
    JournalResponse,
    PaginatedResponse,
)
from backend.database.crud import (
    get_or_create_user,
    create_journal_entry,
    get_journal_entry,
    get_user_journal_entries,
    update_journal_entry,
    delete_journal_entry,
)
from backend.utils.logger import api_logger
import math

router = APIRouter(prefix="/api/journal", tags=["Journal"])


@router.post("/", response_model=JournalResponse)
async def create_entry(
    request: JournalCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new journal entry."""
    api_logger.info(f"Creating journal entry for user {request.user_id}")

    await get_or_create_user(db, request.user_id)

    entry = await create_journal_entry(
        db,
        user_id=request.user_id,
        content=request.content,
        title=request.title,
        mood=request.mood.value if request.mood else None,
        tags=request.tags,
    )

    return JournalResponse.model_validate(entry)


@router.get("/", response_model=PaginatedResponse)
async def list_entries(
    user_id: str,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Get paginated journal entries for a user."""
    entries, total = await get_user_journal_entries(db, user_id, page, page_size)

    return PaginatedResponse(
        items=[JournalResponse.model_validate(e) for e in entries],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=math.ceil(total / page_size) if total > 0 else 0,
    )


@router.get("/{entry_id}", response_model=JournalResponse)
async def get_entry(
    entry_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get a single journal entry."""
    entry = await get_journal_entry(db, entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Journal entry not found")

    return JournalResponse.model_validate(entry)


@router.put("/{entry_id}", response_model=JournalResponse)
async def update_entry(
    entry_id: str,
    request: JournalUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update a journal entry."""
    update_data = request.model_dump(exclude_unset=True)

    # Convert mood enum to string if present
    if "mood" in update_data and update_data["mood"] is not None:
        update_data["mood"] = update_data["mood"].value

    entry = await update_journal_entry(db, entry_id, **update_data)
    if not entry:
        raise HTTPException(status_code=404, detail="Journal entry not found")

    return JournalResponse.model_validate(entry)


@router.delete("/{entry_id}")
async def delete_entry(
    entry_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Delete a journal entry."""
    deleted = await delete_journal_entry(db, entry_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Journal entry not found")

    return {"message": "Journal entry deleted", "id": entry_id}
