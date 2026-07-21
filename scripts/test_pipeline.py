import asyncio
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ai_core.runtime import build_app
from ai_core.runtime.streaming import run_turn

async def test():
    print("Building AI app...")
    try:
        app = await build_app()
        print("App built successfully:", type(app))
    except Exception as e:
        print("BUILD FAILED:", e)
        import traceback
        traceback.print_exc()
        return

    print("Running turn...")
    try:
        async for chunk in run_turn(app, "test_user", "test_session", "I feel sad"):
            print(chunk, end="", flush=True)
        print("\nTurn completed successfully!")
    except Exception as e:
        print("\nRUN FAILED:", e)
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test())
