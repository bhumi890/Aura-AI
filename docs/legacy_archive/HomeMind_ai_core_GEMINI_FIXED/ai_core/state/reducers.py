"""
ai_core/state/reducers.py

Reducer functions for WellnessState fields with genuine concurrent
writers. Kept separate from schema.py so reducers can be unit-tested
in isolation and new reducers don't require touching the schema file.

Only two fields need reducers: chat_history (uses LangGraph's built-in
add_messages) and metadata (uses merge_metadata below). Every other
field has exactly one canonical writer and uses plain overwrite.
"""
from typing import Dict, Any, Optional


def merge_metadata(existing: Optional[Dict[str, Any]], new: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Shallow-merge two metadata dicts. New keys win on conflict; existing
    keys not touched by `new` survive. This is what allows the parallel
    emotion / memory / RAG fan-out to each write telemetry into `metadata`
    in the same superstep without clobbering each other.

    Naming discipline note: namespace your keys per node (e.g. "emotion_ms",
    "memory_ms") rather than generic keys ("duration_ms") to avoid
    accidental collisions between parallel writers.
    """
    if existing is None:
        existing = {}
    if new is None:
        return existing
    return {**existing, **new}
