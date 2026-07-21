"""
ai_core/agents/memory/store.py

Optional dedicated long-term memory persistence layer, separate from the
per-thread PostgresSaver/SqliteSaver checkpointing (which is session-scoped
via thread_id). Use this if the team decides to persist a per-user profile
that outlives a single session/thread -- e.g. a `user_profiles` table keyed
on user_id rather than session_id.

Kept separate from node.py so storage/backend concerns (which DB, which
schema) can change without touching the summarization logic itself.
"""
from typing import Optional
from backend.database.connection import async_session
from backend.database.crud import get_user_profile, upsert_user_profile
from ai_core.rag.logging_utils import get_logger

logger = get_logger(__name__)


async def load_user_profile(user_id: str) -> Optional[str]:
    """
    Load stored rolling memory summary for user_id from the database.
    """
    try:
        async with async_session() as db:
            profile = await get_user_profile(db, user_id)
            if profile and profile.memory_summary:
                return profile.memory_summary
    except Exception as e:
        logger.warning("Failed to load user profile for %s: %s", user_id, e)
    return None


async def save_user_profile(user_id: str, summary: str) -> None:
    """
    Persist rolling memory summary for user_id to the database.
    """
    if not user_id or not summary:
        return
    try:
        async with async_session() as db:
            await upsert_user_profile(db, user_id, summary)
            await db.commit()
            logger.info("Persisted memory profile for user %s (%d chars)", user_id, len(summary))
    except Exception as e:
        logger.warning("Failed to save user profile for %s: %s", user_id, e)

