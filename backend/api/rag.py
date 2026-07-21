"""
RAG & FAISS Verification API
Provides status, vector counts, and test retrieval queries.
"""

from fastapi import APIRouter
from ai_core.agents.knowledge.retriever import retrieve_documents
from ai_core.rag.vectordb.faiss_store import FaissStore

router = APIRouter(prefix="/api/rag", tags=["RAG"])


@router.get("/status")
async def get_rag_status():
    """
    Verify FAISS database storage and retrieval integration.
    Returns whether the index exists, how many vectors are stored, and runs a test search.
    """
    try:
        store = FaissStore()
        size = store.size
        is_indexed = (size > 0)
    except Exception as e:
        return {
            "status": "error",
            "message": f"Could not open FAISS store: {e}",
            "indexed": False,
            "vector_count": 0,
            "test_query_results": []
        }

    test_results = []
    if is_indexed:
        try:
            docs = await retrieve_documents(query="how to manage anxiety and breathing", top_k=2)
            test_results = [
                {"content": d.get("content", "")[:150] + "...", "score": d.get("score")}
                for d in (docs or [])
            ]
        except Exception as e:
            test_results = [{"error": str(e)}]

    return {
        "status": "healthy" if is_indexed else "empty",
        "indexed": is_indexed,
        "vector_count": size,
        "last_query_result_count": len(test_results),
        "test_query_results": test_results
    }
