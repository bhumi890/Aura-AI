"""
ai_core/agents/supervisor/final.py

supervisor_final (Part 5): expensive synthesis. Runs once at the end of
the turn as the join point after the parallel emotion/memory/RAG fan-out
(and optional wellness_plan node). Writes ONLY `final_response` -- no
other node in the graph may write this field.
"""
from typing import Optional, List, Dict, Any
from langchain_core.messages import SystemMessage

from ai_core.state.schema import WellnessState
from ai_core.llm.clients import get_synthesis_llm
from ai_core.prompts.supervisor_final import SUPERVISOR_FINAL_PROMPT
from ai_core.config import FINAL_HISTORY_WINDOW
from ai_core.llm.models import SYNTHESIS_MODEL
from ai_core.utils.metrics import timed_metadata


def _format_docs(docs: Optional[List[Dict[str, Any]]]) -> str:
    if not docs:
        return "none"
    return "\n".join(f"- {d.get('content', '')[:200]}" for d in docs[:3])


async def supervisor_final(state: WellnessState) -> dict:
    with timed_metadata("supervisor_final") as meta:
        system = SUPERVISOR_FINAL_PROMPT.format(
            emotion=state.get("emotion", "unknown"),
            emotion_confidence=state.get("emotion_confidence", "n/a"),
            memory_summary=state.get("memory_summary") or "none available",
            retrieved_documents=_format_docs(state.get("retrieved_documents")),
            recommended_activity=state.get("recommended_activity") or "none",
            wellness_plan=state.get("wellness_plan") or "none",
        )

        messages = [SystemMessage(content=system)] + state.get("chat_history", [])[-FINAL_HISTORY_WINDOW:]
        print("\n===== FINAL STATE =====")
        print("Emotion:", state.get("emotion"))
        print("Memory:", state.get("memory_summary"))
        print("Documents:", state.get("retrieved_documents"))
        print("Wellness:", state.get("wellness_plan"))
        print("=======================\n")
        response = await get_synthesis_llm().ainvoke(messages)
        meta["metadata"]["supervisor_final_model"] = SYNTHESIS_MODEL

    return {
        "final_response": response.content,
        "metadata": meta["metadata"],
    }
