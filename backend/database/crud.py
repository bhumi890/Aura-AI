"""
CRUD Operations
Database create, read, update, delete functions for all models.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from sqlalchemy.orm import selectinload
from typing import Optional, List
from datetime import datetime

from backend.database.models import (
    User,
    Conversation,
    Message,
    JournalEntry,
    MoodLog,
    WellnessPlan,
    UserProfile,
    MessageRole,
)


# ══════════════════════════════════════════════════════════════
#  User CRUD
# ══════════════════════════════════════════════════════════════

async def create_user(db: AsyncSession, username: str, email: Optional[str] = None, password_hash: Optional[str] = None) -> User:
    """Create a new user."""
    user = User(username=username, email=email, password_hash=password_hash)
    db.add(user)
    await db.flush()
    return user



async def get_user(db: AsyncSession, user_id: str) -> Optional[User]:
    """Get a user by ID."""
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def get_user_by_username(db: AsyncSession, username: str) -> Optional[User]:
    """Get a user by username."""
    result = await db.execute(select(User).where(User.username == username))
    return result.scalar_one_or_none()


async def get_or_create_user(db: AsyncSession, user_id: str, username: str = "default_user") -> User:
    """Get existing user or create a new one."""
    user = await get_user(db, user_id)
    if not user:
        user = User(id=user_id, username=username)
        db.add(user)
        await db.flush()
    return user


# ══════════════════════════════════════════════════════════════
#  Conversation CRUD
# ══════════════════════════════════════════════════════════════

async def create_conversation(db: AsyncSession, user_id: str, title: str = "New Conversation") -> Conversation:
    """Create a new conversation."""
    convo = Conversation(user_id=user_id, title=title)
    db.add(convo)
    await db.flush()
    return convo


async def get_conversation(db: AsyncSession, conversation_id: str) -> Optional[Conversation]:
    """Get a conversation with its messages."""
    result = await db.execute(
        select(Conversation)
        .options(selectinload(Conversation.messages))
        .where(Conversation.id == conversation_id)
    )
    return result.scalar_one_or_none()


async def delete_conversation(db: AsyncSession, conversation_id: str) -> bool:
    """Soft delete a conversation by setting is_active to False."""
    result = await db.execute(
        select(Conversation).where(Conversation.id == conversation_id)
    )
    convo = result.scalar_one_or_none()
    if convo:
        convo.is_active = False
        await db.flush()
        return True
    return False


async def get_user_conversations(

    db: AsyncSession,
    user_id: str,
    page: int = 1,
    page_size: int = 20
) -> tuple[List[Conversation], int]:
    """Get paginated conversations for a user."""
    # Count total
    count_result = await db.execute(
        select(func.count(Conversation.id))
        .where(Conversation.user_id == user_id, Conversation.is_active == True)
    )
    total = count_result.scalar()

    # Fetch page
    offset = (page - 1) * page_size
    result = await db.execute(
        select(Conversation)
        .where(Conversation.user_id == user_id, Conversation.is_active == True)
        .order_by(desc(Conversation.updated_at))
        .offset(offset)
        .limit(page_size)
    )
    conversations = result.scalars().all()
    return conversations, total


# ══════════════════════════════════════════════════════════════
#  Message CRUD
# ══════════════════════════════════════════════════════════════

async def create_message(
    db: AsyncSession,
    conversation_id: str,
    role: MessageRole,
    content: str,
    emotion: Optional[str] = None,
    emotion_confidence: Optional[float] = None,
    emotion_intensity: Optional[str] = None,
    safety_flag: bool = True,
    agent_metadata: Optional[dict] = None,
    is_voice_message: bool = False,
    audio_duration: Optional[float] = None,
) -> Message:
    """Create a new message in a conversation."""
    message = Message(
        conversation_id=conversation_id,
        role=role,
        content=content,
        emotion=emotion,
        emotion_confidence=emotion_confidence,
        emotion_intensity=emotion_intensity,
        safety_flag=safety_flag,
        agent_metadata=agent_metadata,
        is_voice_message=is_voice_message,
        audio_duration=audio_duration,
    )
    db.add(message)
    await db.flush()

    # Update conversation timestamp
    result = await db.execute(
        select(Conversation).where(Conversation.id == conversation_id)
    )
    convo = result.scalar_one_or_none()
    if convo:
        convo.updated_at = datetime.utcnow()

    return message


async def get_conversation_messages(
    db: AsyncSession,
    conversation_id: str,
    limit: int = 50
) -> List[Message]:
    """Get messages for a conversation, ordered by time."""
    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at)
        .limit(limit)
    )
    return result.scalars().all()


# ══════════════════════════════════════════════════════════════
#  Journal CRUD
# ══════════════════════════════════════════════════════════════

async def create_journal_entry(
    db: AsyncSession,
    user_id: str,
    content: str,
    title: Optional[str] = None,
    mood: Optional[str] = None,
    tags: Optional[list] = None,
) -> JournalEntry:
    """Create a new journal entry."""
    entry = JournalEntry(
        user_id=user_id,
        title=title,
        content=content,
        mood=mood,
        tags=tags,
    )
    db.add(entry)
    await db.flush()
    return entry


async def get_journal_entry(db: AsyncSession, entry_id: str) -> Optional[JournalEntry]:
    """Get a journal entry by ID."""
    result = await db.execute(select(JournalEntry).where(JournalEntry.id == entry_id))
    return result.scalar_one_or_none()


async def get_user_journal_entries(
    db: AsyncSession,
    user_id: str,
    page: int = 1,
    page_size: int = 20
) -> tuple[List[JournalEntry], int]:
    """Get paginated journal entries for a user."""
    count_result = await db.execute(
        select(func.count(JournalEntry.id))
        .where(JournalEntry.user_id == user_id)
    )
    total = count_result.scalar()

    offset = (page - 1) * page_size
    result = await db.execute(
        select(JournalEntry)
        .where(JournalEntry.user_id == user_id)
        .order_by(desc(JournalEntry.created_at))
        .offset(offset)
        .limit(page_size)
    )
    entries = result.scalars().all()
    return entries, total


async def update_journal_entry(
    db: AsyncSession,
    entry_id: str,
    **kwargs
) -> Optional[JournalEntry]:
    """Update a journal entry."""
    result = await db.execute(select(JournalEntry).where(JournalEntry.id == entry_id))
    entry = result.scalar_one_or_none()
    if entry:
        for key, value in kwargs.items():
            if value is not None and hasattr(entry, key):
                setattr(entry, key, value)
        entry.updated_at = datetime.utcnow()
        await db.flush()
    return entry


async def delete_journal_entry(db: AsyncSession, entry_id: str) -> bool:
    """Delete a journal entry."""
    result = await db.execute(select(JournalEntry).where(JournalEntry.id == entry_id))
    entry = result.scalar_one_or_none()
    if entry:
        await db.delete(entry)
        await db.flush()
        return True
    return False


# ══════════════════════════════════════════════════════════════
#  Mood CRUD
# ══════════════════════════════════════════════════════════════

async def create_mood_log(
    db: AsyncSession,
    user_id: str,
    mood: str,
    emotion: Optional[str] = None,
    note: Optional[str] = None,
    energy_level: Optional[int] = None,
    sleep_quality: Optional[int] = None,
    stress_level: Optional[int] = None,
    activities: Optional[list] = None,
) -> MoodLog:
    """Log a mood entry."""
    log = MoodLog(
        user_id=user_id,
        mood=mood,
        emotion=emotion,
        note=note,
        energy_level=energy_level,
        sleep_quality=sleep_quality,
        stress_level=stress_level,
        activities=activities,
    )
    db.add(log)
    await db.flush()
    return log


async def get_mood_logs(
    db: AsyncSession,
    user_id: str,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    page: int = 1,
    page_size: int = 50,
) -> tuple[List[MoodLog], int]:
    """Get paginated mood logs with optional date filtering."""
    query = select(MoodLog).where(MoodLog.user_id == user_id)

    if start_date:
        query = query.where(MoodLog.logged_at >= start_date)
    if end_date:
        query = query.where(MoodLog.logged_at <= end_date)

    # Count
    count_query = select(func.count(MoodLog.id)).where(MoodLog.user_id == user_id)
    if start_date:
        count_query = count_query.where(MoodLog.logged_at >= start_date)
    if end_date:
        count_query = count_query.where(MoodLog.logged_at <= end_date)
    count_result = await db.execute(count_query)
    total = count_result.scalar()

    # Fetch
    offset = (page - 1) * page_size
    result = await db.execute(
        query.order_by(desc(MoodLog.logged_at))
        .offset(offset)
        .limit(page_size)
    )
    logs = result.scalars().all()
    return logs, total


async def get_mood_stats(db: AsyncSession, user_id: str) -> dict:
    """Get mood statistics for a user."""
    result = await db.execute(
        select(MoodLog).where(MoodLog.user_id == user_id)
    )
    logs = result.scalars().all()

    if not logs:
        return {
            "total_logs": 0,
            "average_energy": None,
            "average_sleep": None,
            "average_stress": None,
            "most_common_mood": None,
            "mood_distribution": {},
        }

    # Calculate stats
    energy_vals = [l.energy_level for l in logs if l.energy_level is not None]
    sleep_vals = [l.sleep_quality for l in logs if l.sleep_quality is not None]
    stress_vals = [l.stress_level for l in logs if l.stress_level is not None]

    mood_counts = {}
    for log in logs:
        mood_str = log.mood.value if hasattr(log.mood, 'value') else str(log.mood)
        mood_counts[mood_str] = mood_counts.get(mood_str, 0) + 1

    most_common = max(mood_counts, key=mood_counts.get) if mood_counts else None

    return {
        "total_logs": len(logs),
        "average_energy": round(sum(energy_vals) / len(energy_vals), 1) if energy_vals else None,
        "average_sleep": round(sum(sleep_vals) / len(sleep_vals), 1) if sleep_vals else None,
        "average_stress": round(sum(stress_vals) / len(stress_vals), 1) if stress_vals else None,
        "most_common_mood": most_common,
        "mood_distribution": mood_counts,
    }


# ══════════════════════════════════════════════════════════════
#  Wellness Plan CRUD
# ══════════════════════════════════════════════════════════════

async def create_wellness_plan(
    db: AsyncSession,
    user_id: str,
    title: str = "My Wellness Plan",
    goals: Optional[list] = None,
) -> WellnessPlan:
    """Create a new wellness plan."""
    plan = WellnessPlan(
        user_id=user_id,
        title=title,
        goals=goals,
    )
    db.add(plan)
    await db.flush()
    return plan


async def get_wellness_plan(db: AsyncSession, user_id: str) -> Optional[WellnessPlan]:
    """Get the active wellness plan for a user."""
    result = await db.execute(
        select(WellnessPlan)
        .where(WellnessPlan.user_id == user_id, WellnessPlan.is_active == True)
        .order_by(desc(WellnessPlan.created_at))
    )
    return result.scalar_one_or_none()


async def update_wellness_plan(
    db: AsyncSession,
    plan_id: str,
    **kwargs
) -> Optional[WellnessPlan]:
    """Update a wellness plan."""
    result = await db.execute(select(WellnessPlan).where(WellnessPlan.id == plan_id))
    plan = result.scalar_one_or_none()
    if plan:
        for key, value in kwargs.items():
            if value is not None and hasattr(plan, key):
                setattr(plan, key, value)
        plan.updated_at = datetime.utcnow()
        await db.flush()
    return plan


# ══════════════════════════════════════════════════════════════
#  UserProfile CRUD (Memory Agent Cross-Session Persistence)
# ══════════════════════════════════════════════════════════════

async def get_user_profile(db: AsyncSession, user_id: str) -> Optional[UserProfile]:
    """Get the UserProfile (long-term memory) for a user."""
    result = await db.execute(select(UserProfile).where(UserProfile.user_id == user_id))
    return result.scalar_one_or_none()


async def upsert_user_profile(db: AsyncSession, user_id: str, memory_summary: str) -> UserProfile:
    """Create or update the UserProfile memory summary."""
    profile = await get_user_profile(db, user_id)
    if profile:
        profile.memory_summary = memory_summary
        profile.last_summarized_at = datetime.utcnow()
        profile.updated_at = datetime.utcnow()
    else:
        profile = UserProfile(
            user_id=user_id,
            memory_summary=memory_summary,
            last_summarized_at=datetime.utcnow()
        )
        db.add(profile)
    await db.flush()
    return profile
