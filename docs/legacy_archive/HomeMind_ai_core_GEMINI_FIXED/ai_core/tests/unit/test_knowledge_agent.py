"""Unit tests for ai_core.agents.knowledge.knowledge.retrieve_knowledge"""

from __future__ import annotations

import pytest

from ai_core.agents.knowledge import knowledge as knowledge_module
from ai_core.rag.models import RetrievedDocument


def _sample_documents() -> list[RetrievedDocument]:
    return [
        RetrievedDocument(
            content="Deep breathing can reduce acute anxiety symptoms.",
            metadata={
                "filename": "anxiety_guide.pdf",
                "page": 2,
                "chunk_id": "anxiety_guide-2-0-abc123",
                "source": "rag/documents/anxiety_guide.pdf",
                "document_type": "pdf",
            },
            score=0.87,
        )
    ]


def test_retrieve_knowledge_returns_expected_contract(monkeypatch):
    monkeypatch.setattr(
        knowledge_module,
        "fetch_relevant_chunks",
        lambda query, top_k=None: _sample_documents(),
    )

    result = knowledge_module.retrieve_knowledge("how do I calm down when anxious?")

    assert isinstance(result, dict)
    assert "documents" in result
    assert len(result["documents"]) == 1

    doc = result["documents"][0]
    assert set(doc.keys()) == {"content", "metadata", "score"}
    assert doc["content"] == _sample_documents()[0].content
    assert doc["score"] == pytest.approx(0.87)
    assert doc["metadata"]["filename"] == "anxiety_guide.pdf"


def test_retrieve_knowledge_empty_query_returns_empty_documents():
    result = knowledge_module.retrieve_knowledge("")
    assert result == {"documents": []}


def test_retrieve_knowledge_non_string_query_returns_empty_documents():
    result = knowledge_module.retrieve_knowledge(None)  # type: ignore[arg-type]
    assert result == {"documents": []}


def test_retrieve_knowledge_handles_internal_failures_gracefully(monkeypatch):
    def _raise(*_args, **_kwargs):
        raise RuntimeError("simulated retrieval failure")

    monkeypatch.setattr(knowledge_module, "fetch_relevant_chunks", _raise)

    result = knowledge_module.retrieve_knowledge("valid query")

    assert result == {"documents": []}


def test_retrieve_knowledge_result_is_json_serializable(monkeypatch):
    import json

    monkeypatch.setattr(
        knowledge_module,
        "fetch_relevant_chunks",
        lambda query, top_k=None: _sample_documents(),
    )

    result = knowledge_module.retrieve_knowledge("query")
    serialized = json.dumps(result)  # must not raise
    assert "documents" in serialized
