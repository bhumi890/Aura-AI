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


async def load_user_profile(user_id: str) -> Optional[str]:
    """
    Placeholder. Wire this to Postgres (or another store) if long-term
    memory needs to persist across sessions, not just within one thread's
    checkpointed state.
    """
    raise NotImplementedError("Wire this to your persistence layer.")


async def save_user_profile(user_id: str, summary: str) -> None:
    """Placeholder -- see load_user_profile."""
    raise NotImplementedError("Wire this to your persistence layer.")
