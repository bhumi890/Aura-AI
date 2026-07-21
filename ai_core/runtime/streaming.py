"""
ai_core/runtime/streaming.py

run_turn(): the actual per-turn execution wrapper, using astream per
Part 1's streaming design decision. thread_id = session_id ties this
run to the correct checkpointed state.

stream_mode="values" yields the full state after each node -- useful
while debugging. Switch to stream_mode="updates" for production, since
it's leaner over the wire and matches what a real client needs (diffs,
not the whole state object repeated every step).
"""
import pprint
from typing import AsyncGenerator


async def run_turn(
    app,
    user_id: str,
    session_id: str,
    user_message: str,
    stream_mode: str = "updates",
) -> AsyncGenerator[str, None]:
    from langchain_core.messages import HumanMessage
    from ai_core.agents.memory.store import load_user_profile

    config = {"configurable": {"thread_id": session_id}}

    # Check if existing checkpoint has memory_summary; if not, load from DB
    memory_summary = None
    try:
        current_state = await app.aget_state(config)
        if current_state and current_state.values:
            memory_summary = current_state.values.get("memory_summary")
    except Exception:
        pass

    if not memory_summary and user_id:
        memory_summary = await load_user_profile(user_id)

    initial_state = {
        "user_id": user_id,
        "session_id": session_id,
        "user_message": user_message,
        "chat_history": [HumanMessage(content=user_message)],
    }
    if memory_summary:
        initial_state["memory_summary"] = memory_summary

    async for chunk in app.astream(initial_state, config=config, stream_mode=stream_mode):

        if stream_mode == "updates" and isinstance(chunk, dict):
            for node_name, node_output in chunk.items():
                if isinstance(node_output, dict) and node_output.get("final_response"):
                    yield node_output["final_response"]
        elif stream_mode == "values" and isinstance(chunk, dict):
            if chunk.get("final_response"):
                yield chunk["final_response"]
