"""
ai_core/agents/memory/node.py

memory_agent (Part 6): long-term memory maintenance via rolling summary,
not raw append. Only re-summarizes every SUMMARIZE_TRIGGER_TURNS turns to
keep cost proportional to value -- most turns this node is a cheap no-op.
Writes ONLY `memory_summary`, plus its own `last_summarized_turn` bookkeeping
key inside `metadata`.
"""
from langchain_core.messages import SystemMessage

from ai_core.state.schema import WellnessState
from ai_core.llm.clients import get_fast_llm
from ai_core.prompts.memory import MEMORY_SUMMARY_PROMPT
from ai_core.config import SUMMARIZE_TRIGGER_TURNS
from ai_core.utils.metrics import timed_metadata


async def memory_agent(state: WellnessState) -> dict:
    history = state.get("chat_history", [])
    turn_count = len(history)

    last_summarized_at = state.get("metadata", {}).get("last_summarized_turn", 0)
    if turn_count - last_summarized_at < SUMMARIZE_TRIGGER_TURNS:
        return {}  # no-op; existing memory_summary passes through untouched

    with timed_metadata("memory_agent") as meta:
        new_turns = history[last_summarized_at:]
        new_turns_str = "\n".join(f"{m.type}: {m.content}" for m in new_turns)

        response = await get_fast_llm().ainvoke([
            SystemMessage(content=MEMORY_SUMMARY_PROMPT.format(
                existing_summary=state.get("memory_summary") or "No prior summary.",
                new_turns=new_turns_str,
            ))
        ])
        meta["metadata"]["last_summarized_turn"] = turn_count

    return {
        "memory_summary": response.content,
        "metadata": meta["metadata"],
    }
