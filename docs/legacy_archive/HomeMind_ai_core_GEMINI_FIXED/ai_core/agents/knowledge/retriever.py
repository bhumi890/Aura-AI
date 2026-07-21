"""
ai_core/agents/knowledge/retriever.py

Bridge between rag_node (node.py, in this same package) and the Knowledge
Agent's public contract, defined in knowledge.py (also in this package):

    ai_core.agents.knowledge.knowledge.retrieve_knowledge(query: str) -> dict
    {"documents": [{"content": str, "metadata": dict, "score": float}, ...]}

This shape already matches WellnessState.retrieved_documents exactly
(List[Dict[str, Any]]) -- no reshaping needed. This file only adapts the
calling convention (sync -> async) so node.py's `await retrieve_documents(...)`
call works without blocking the event loop.

Retrieval itself is fully local/offline (sentence-transformers embeddings
+ a FAISS index on disk, under ai_core/rag/) -- no external API call
happens in this step. Only supervisor_final (LLM synthesis) requires
network access, per the project's hybrid online/offline design.

top_k note: the underlying RAG pipeline (ai_core/rag/) controls its own
top_k via the TOP_K env var (see .env.example / ai_core/rag/config.py) as
its single source of truth. ai_core.config.RAG_TOP_K is kept for backward
compatibility with node.py's call signature but is not forwarded --
adjust TOP_K in .env if you need to change result count.
"""
import asyncio
from typing import List, Dict, Any

from ai_core.agents.knowledge.knowledge import retrieve_knowledge


async def retrieve_documents(query: str, top_k: int = 3) -> List[Dict[str, Any]]:
    """
    Retrieve relevant document chunks for `query` via the Knowledge Agent.

    retrieve_knowledge() is synchronous and does CPU-bound work (embedding
    the query + FAISS similarity search), so it's run in a worker thread
    via asyncio.to_thread to avoid blocking the event loop the rest of the
    LangGraph pipeline (and any concurrently-running parallel nodes) is
    running on.

    On any internal failure, the Knowledge Agent itself already returns
    {"documents": []} rather than raising (see ai_core/agents/knowledge/
    knowledge.py's contract) -- so this function does not need its own
    try/except; a failed retrieval simply yields no documents, and
    supervisor_final synthesizes without RAG grounding for that turn.
    """
    result = await asyncio.to_thread(retrieve_knowledge, query)
    return result.get("documents", [])
