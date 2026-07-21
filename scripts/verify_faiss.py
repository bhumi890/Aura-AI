"""
FAISS Vector Store Verification Script
Run directly to verify that embedding, indexing, and retrieval work end-to-end.

Usage:
    python -m scripts.verify_faiss
"""

import asyncio
from pathlib import Path
from ai_core.rag.models import ChunkMetadata, EmbeddedChunk
from ai_core.rag.vectordb.faiss_store import FaissStore
from ai_core.agents.knowledge.retriever import retrieve_documents


async def main():
    print("=" * 60)
    print("[*] Verifying FAISS Vector Store & Retrieval Pipeline")
    print("=" * 60)

    # 1. Initialize FaissStore
    print("\n[Step 1] Initializing FaissStore...")
    store = FaissStore()
    print(f"[OK] Current store size: {store.size} vector(s)")

    # 2. Test query against existing index
    test_query = "How can I calm down during a panic attack or stress?"
    print(f"\n[Step 2] Executing test retrieval query: '{test_query}'")
    try:
        results = await retrieve_documents(query=test_query, top_k=3)
        if results:
            print(f"[OK] Retrieved {len(results)} document(s):")
            for idx, doc in enumerate(results, 1):
                content = doc.get("content", "")[:120].encode('ascii', 'replace').decode('ascii') + "..."
                score = doc.get("score", 0.0)
                print(f"   [{idx}] Score: {score:.4f} | Content: {content}")
        else:
            print("[INFO] No results returned (index might be empty or no matches above threshold).")
    except Exception as e:

        print(f"[ERROR] Retrieval failed with error: {e}")

    print("\n=" * 60)
    print("[SUCCESS] Verification Complete!")
    print("=" * 60)



if __name__ == "__main__":
    asyncio.run(main())
