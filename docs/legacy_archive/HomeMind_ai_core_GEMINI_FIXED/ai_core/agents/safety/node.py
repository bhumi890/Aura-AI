"""
ai_core/agents/safety/node.py

The mandatory, unconditional safety node (Part 1 / Part 7). This node runs
on EVERY turn, first, before any other node -- it cannot be bypassed by any
routing logic. Its output (safety_status) is the one field with the
strictest write discipline in the whole schema: no other node may ever
write to it.
"""
from ai_core.state.schema import WellnessState
from ai_core.agents.safety.rules import classify_safety
from ai_core.utils.logging import get_logger
from ai_core.utils.metrics import timed_metadata

logger = get_logger("safety_node")


async def safety_node(state: WellnessState) -> dict:
    with timed_metadata("safety_node") as meta:
        status = classify_safety(state.get("user_message", ""))
        logger.info("safety_status=%s session_id=%s", status, state.get("session_id"))

    return {
        "safety_status": status,
        "metadata": meta["metadata"],
    }


async def crisis_response_node(state: WellnessState) -> dict:
    """
    Dedicated response path for safety_status == "crisis". Bypasses
    emotion, memory, RAG, and both supervisors entirely (Part 1's
    short-circuit design). Uses a fixed, carefully reviewed response
    template rather than free-form LLM generation.

    NOTE: the actual crisis resource content (hotline numbers, escalation
    copy) should be owned and reviewed by the safety team (M5) and kept
    up to date -- do not let this drift out of sync with current,
    verified crisis resources.
    """
    response_text = (
        "It sounds like you're going through something really difficult right now. "
        "I want to make sure you get support that's equipped to help. "
        "Please consider reaching out to a crisis line or someone you trust right away."
    )

    return {
        "final_response": response_text,
        "metadata": {"crisis_path_triggered": True},
    }
