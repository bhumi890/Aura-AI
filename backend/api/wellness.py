"""
Wellness Plan API Routes
Manages personalized wellness plans for users.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.connection import get_db
from backend.database.schema import (
    WellnessPlanCreate,
    WellnessPlanUpdate,
    WellnessPlanResponse,
)
from backend.database.crud import (
    get_or_create_user,
    create_wellness_plan,
    get_wellness_plan,
    update_wellness_plan,
)
from backend.utils.logger import api_logger

router = APIRouter(prefix="/api/wellness", tags=["Wellness"])


@router.get("/plan", response_model=WellnessPlanResponse)
async def get_plan(
    user_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Get the active wellness plan for a user.
    If no plan exists, creates a default one.
    """
    api_logger.info(f"Getting wellness plan for user {user_id}")

    await get_or_create_user(db, user_id)

    plan = await get_wellness_plan(db, user_id)

    if not plan:
        # Create a default wellness plan
        plan = await create_wellness_plan(
            db,
            user_id=user_id,
            title="My Wellness Plan",
            goals=[
                {"title": "Practice mindfulness", "description": "5 minutes daily meditation", "completed": False},
                {"title": "Stay active", "description": "30 minutes of exercise", "completed": False},
                {"title": "Journal regularly", "description": "Write about your feelings", "completed": False},
            ],
        )
        api_logger.info(f"Created default wellness plan for user {user_id}")

    return WellnessPlanResponse.model_validate(plan)


@router.post("/plan", response_model=WellnessPlanResponse)
async def create_plan(
    request: WellnessPlanCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new wellness plan."""
    api_logger.info(f"Creating wellness plan for user {request.user_id}")

    await get_or_create_user(db, request.user_id)

    goals_data = None
    if request.goals:
        goals_data = [g.model_dump() for g in request.goals]

    plan = await create_wellness_plan(
        db,
        user_id=request.user_id,
        title=request.title,
        goals=goals_data,
    )

    return WellnessPlanResponse.model_validate(plan)


@router.put("/plan/{plan_id}", response_model=WellnessPlanResponse)
async def update_plan(
    plan_id: str,
    request: WellnessPlanUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update an existing wellness plan."""
    update_data = request.model_dump(exclude_unset=True)

    # Convert goal objects to dicts
    if "goals" in update_data and update_data["goals"] is not None:
        update_data["goals"] = [
            g.model_dump() if hasattr(g, "model_dump") else g
            for g in update_data["goals"]
        ]

    plan = await update_wellness_plan(db, plan_id, **update_data)

    if not plan:
        raise HTTPException(status_code=404, detail="Wellness plan not found")

    return WellnessPlanResponse.model_validate(plan)
