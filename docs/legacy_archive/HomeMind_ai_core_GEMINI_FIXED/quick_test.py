"""
quick_test.py

Standalone smoke test for the ai_core LangGraph pipeline -- run this
BEFORE wiring anything into the FastAPI backend, to confirm the graph
compiles and executes end-to-end.

Usage:
    export GOOGLE_API_KEY="your-key-here"
    pip install -r requirements.txt
    python quick_test.py

Notes:
- Uses SQLite checkpointing by default (HOMEMIND_ENV is unset -> "development").
- If route_plan.needs_rag ends up True for your test message, this will
  currently raise NotImplementedError -- that's expected until
  agents/knowledge/retriever.py is filled in. Try a message unlikely to
  trigger RAG first (e.g. plain venting / check-in style) to confirm the
  rest of the pipeline works before wiring up retrieval.
"""
from dotenv import load_dotenv

load_dotenv()

import asyncio
import os
import uuid

from ai_core.runtime import build_app, run_turn


async def main():
    if not os.getenv("GOOGLE_API_KEY"):
        raise SystemExit(
            "GOOGLE_API_KEY is not set. Run:\n"
            "  export GOOGLE_API_KEY='your-key-here'\n"
            "before running this script."
        )

    print("Building graph + compiling with checkpointer...")
    app = await build_app()
    print("Graph compiled successfully.\n")

    user_id = "test-user-001"
    session_id = str(uuid.uuid4())  # fresh thread each run
    test_message = "I've been feeling lonely since I moved to college."

    print(f"session_id: {session_id}")
    print(f"user message: {test_message!r}\n")
    print("--- streaming response ---")

    full_response = ""
    async for chunk in run_turn(app, user_id, session_id, test_message):
        print(chunk, end="", flush=True)
        full_response += chunk

    print("\n--- end of response ---\n")

    if not full_response:
        print(
            "WARNING: no final_response was produced. This usually means "
            "the crisis short-circuit path was taken (check agents/safety/rules.py -- "
            "the placeholder implementation returns 'safe' for everything, so this "
            "would only happen once real rules are filled in), or an exception was "
            "swallowed upstream. Re-run with more verbose logging if this happens."
        )


if __name__ == "__main__":
    asyncio.run(main())
