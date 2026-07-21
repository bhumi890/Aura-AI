"""
ai_core/utils/metrics.py

Timing helpers so nodes don't each reinvent a timer. Populates the
`metadata` field using namespaced keys (per Part 7's collision-avoidance
guidance) so parallel writers never stomp on each other.
"""
import time
from contextlib import contextmanager
from typing import Dict, Generator


@contextmanager
def timed_metadata(node_name: str) -> Generator[Dict[str, dict], None, None]:
    """
    Usage:
        with timed_metadata("emotion_node") as meta:
            ... do work ...
        return {"emotion": ..., "metadata": meta["metadata"]}
    """
    start = time.perf_counter()
    holder = {"metadata": {}}
    try:
        yield holder
    finally:
        elapsed_ms = round((time.perf_counter() - start) * 1000, 1)
        holder["metadata"][f"{node_name}_ms"] = elapsed_ms
