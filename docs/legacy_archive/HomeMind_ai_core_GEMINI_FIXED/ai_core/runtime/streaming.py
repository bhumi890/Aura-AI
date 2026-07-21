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
    stream_mode: str = "values",
) -> AsyncGenerator[str, None]:
    config = {"configurable": {"thread_id": session_id}}

    initial_state = {
        "user_id": user_id,
        "session_id": session_id,
        "user_message": user_message,
    }

    async for chunk in app.astream(initial_state, config=config, stream_mode=stream_mode):
        if chunk.get("final_response"):
            yield chunk["final_response"]
