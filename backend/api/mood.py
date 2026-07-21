"""
Mood API Routes
Handles mood logging, history retrieval, and mood statistics.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import datetime
import math

from backend.database.connection import get_db
from backend.database.schema import (
    MoodCreate,
    MoodResponse,
    MoodStats,
    PaginatedResponse,
)
from backend.database.crud import (
    get_or_create_user,
    create_mood_log,
    get_mood_logs,
    get_mood_stats,
)
from backend.utils.logger import api_logger

router = APIRouter(prefix="/api/mood", tags=["Mood"])


@router.post("/", response_model=MoodResponse)
async def log_mood(
    request: MoodCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Log a mood entry.

    Records the user's current mood along with optional metadata
    like energy level, sleep quality, stress level, and activities.
    """
    api_logger.info(f"Logging mood for user {request.user_id}: {request.mood}")

    await get_or_create_user(db, request.user_id)

    log = await create_mood_log(
        db,
        user_id=request.user_id,
        mood=request.mood.value,
        emotion=request.emotion,
        note=request.note,
        energy_level=request.energy_level,
        sleep_quality=request.sleep_quality,
        stress_level=request.stress_level,
        activities=request.activities,
    )

    return MoodResponse.model_validate(log)


@router.get("/history", response_model=PaginatedResponse)
async def get_mood_history(
    user_id: str,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Get mood history for a user with optional date filtering.

    Query parameters:
    - start_date: Filter logs from this date (ISO format)
    - end_date: Filter logs until this date (ISO format)
    """
    logs, total = await get_mood_logs(
        db,
        user_id=user_id,
        start_date=start_date,
        end_date=end_date,
        page=page,
        page_size=page_size,
    )

    return PaginatedResponse(
        items=[MoodResponse.model_validate(log) for log in logs],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=math.ceil(total / page_size) if total > 0 else 0,
    )


@router.get("/stats", response_model=MoodStats)
async def mood_statistics(
    user_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Get aggregated mood statistics for a user.

    Returns averages for energy, sleep, stress,
    the most common mood, and mood distribution.
    """
    stats = await get_mood_stats(db, user_id)
    return MoodStats(**stats)
