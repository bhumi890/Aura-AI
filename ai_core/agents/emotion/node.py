"""
ai_core/agents/emotion/node.py

Emotion detection node. Runs in parallel with memory_agent and
(conditionally) rag_node, fanned out from supervisor_entry's route_plan.
Writes ONLY `emotion` and `emotion_confidence`.
"""
from typing import Literal
from pydantic import BaseModel, Field
from langchain_core.messages import SystemMessage

from ai_core.state.schema import WellnessState
from ai_core.llm.clients import get_emotion_llm
from ai_core.prompts.emotion import EMOTION_DETECTION_PROMPT
from ai_core.utils.metrics import timed_metadata


class EmotionResult(BaseModel):
    label: str = Field(description="Primary emotion label, e.g. 'anxious', 'content'")
    confidence: float = Field(ge=0.0, le=1.0)


async def emotion_node(state: WellnessState) -> dict:
    with timed_metadata("emotion_node") as meta:
        recent = state.get("chat_history", [])[-6:]
        recent_str = "\n".join(f"{m.type}: {m.content}" for m in recent)

        structured_llm = get_emotion_llm().with_structured_output(EmotionResult)
        result = await structured_llm.ainvoke([
            SystemMessage(content=EMOTION_DETECTION_PROMPT.format(
                recent_history=recent_str,
                user_message=state["user_message"],
            ))
        ])

    return {
        "emotion": result.label,
        "emotion_confidence": result.confidence,
        "metadata": meta["metadata"],
    }
