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
from ai_core.llm.clients import get_memory_llm
from ai_core.prompts.memory import MEMORY_SUMMARY_PROMPT
from ai_core.config import SUMMARIZE_TRIGGER_TURNS
from ai_core.utils.metrics import timed_metadata
from ai_core.agents.memory.store import load_user_profile, save_user_profile


async def memory_agent(state: WellnessState) -> dict:
    history = state.get("chat_history", [])
    turn_count = len(history)

    existing_summary = state.get("memory_summary")
    user_id = state.get("user_id")
    if not existing_summary and user_id:
        existing_summary = await load_user_profile(user_id)

    last_summarized_at = state.get("metadata", {}).get("last_summarized_turn", 0)
    if turn_count - last_summarized_at < SUMMARIZE_TRIGGER_TURNS:
        # Even if we didn't re-summarize, if we loaded a summary from DB that wasn't in state, return it!
        if existing_summary and not state.get("memory_summary"):
            return {"memory_summary": existing_summary}
        return {}  # no-op; existing memory_summary passes through untouched

    with timed_metadata("memory_agent") as meta:
        new_turns = history[last_summarized_at:]
        new_turns_str = "\n".join(f"{m.type}: {m.content}" for m in new_turns)

        response = await get_memory_llm().ainvoke([
            SystemMessage(content=MEMORY_SUMMARY_PROMPT.format(
                existing_summary=existing_summary or "No prior summary.",
                new_turns=new_turns_str,
            ))
        ])
        meta["metadata"]["last_summarized_turn"] = turn_count

    new_summary = response.content
    if user_id and new_summary:
        await save_user_profile(user_id, new_summary)

    return {
        "memory_summary": new_summary,
        "metadata": meta["metadata"],
    }

