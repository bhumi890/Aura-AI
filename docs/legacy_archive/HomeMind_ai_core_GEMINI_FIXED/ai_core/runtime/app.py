"""
ai_core/runtime/app.py

build_app(): compiles the graph with the checkpointer attached. This is
the object backend/ code should import -- backend should never reach
into ai_core.agents or ai_core.graph directly. runtime/ is the only
public seam between ai_core and the rest of the system.
"""
from ai_core.graph.builder import build_graph
from ai_core.graph.checkpointer import get_checkpointer


async def build_app():
    graph = build_graph()
    checkpointer = await get_checkpointer()
    return graph.compile(checkpointer=checkpointer)
