"""
ai_core/agents/knowledge/node.py

RAG node. Only invoked when route_plan.needs_rag is True (conditional
retrieval per Part 1). Writes ONLY `retrieved_documents`.

NOTE: this overlaps with the M3 team's RAG/Knowledge ownership -- treat
this file as the integration seam. The actual retrieval implementation
lives in retriever.py so it can be swapped independently of this node
wrapper.
"""
from ai_core.state.schema import WellnessState
from ai_core.agents.knowledge.retriever import retrieve_documents
from ai_core.config import RAG_TOP_K
from ai_core.utils.metrics import timed_metadata


async def rag_node(state: WellnessState) -> dict:
    with timed_metadata("rag_node") as meta:
        docs = await retrieve_documents(
            query=state["user_message"],
            top_k=RAG_TOP_K,
        )

    return {
        "retrieved_documents": docs,
        "metadata": meta["metadata"],
    }
