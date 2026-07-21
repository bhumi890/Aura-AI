"""
ai_core/agents/wellness_plan/node.py

Wellness plan / activity recommendation node. Only invoked when
route_plan.needs_wellness_plan is True. Writes `recommended_activity`
and `wellness_plan`. Runs after the emotion/memory/RAG fan-out has
completed, since recommendations are conditioned on emotion + memory
context, not just the raw message.

Uses the fast/cheap model (Haiku) with structured output -- this is a
bounded, well-defined generation task, same tier as emotion detection
and intent classification, not a job that needs the synthesis model.
"""
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from langchain_core.messages import SystemMessage

from ai_core.state.schema import WellnessState
from ai_core.llm.clients import get_fast_llm
from ai_core.prompts.wellness_plan import WELLNESS_PLAN_PROMPT
from ai_core.utils.metrics import timed_metadata


class WellnessPlanResult(BaseModel):
    activity: str = Field(description="One short, concrete activity, doable in under 10 minutes")
    rationale: str = Field(description="One short sentence on why this fits the user's current moment")
    steps: List[str] = Field(
        default_factory=list,
        description="2-4 short, simple steps to actually do the activity. Empty list if not needed.",
    )
    duration_minutes: Optional[int] = Field(
        default=None, description="Rough estimated time to complete, in minutes"
    )


# Fallback used only if the LLM call itself fails -- keeps the node from
# crashing the whole turn if the model call errors out transiently.
_FALLBACK_ACTIVITY = "a short mindful pause -- take three slow breaths before continuing"


async def wellness_plan_node(state: WellnessState) -> dict:
    with timed_metadata("wellness_plan_node") as meta:
        emotion = state.get("emotion") or "neutral"
        emotion_confidence = state.get("emotion_confidence")
        memory_summary = state.get("memory_summary") or "none available"
        user_message = state.get("user_message", "")

        try:
            structured_llm = get_fast_llm().with_structured_output(WellnessPlanResult)
            result = await structured_llm.ainvoke([
                SystemMessage(content=WELLNESS_PLAN_PROMPT.format(
                    emotion=emotion,
                    emotion_confidence=emotion_confidence if emotion_confidence is not None else "n/a",
                    memory_summary=memory_summary,
                    user_message=user_message,
                ))
            ])
            activity = result.activity
            plan: Dict[str, Any] = {
                "activity": result.activity,
                "rationale": result.rationale,
                "steps": result.steps,
                "duration_minutes": result.duration_minutes,
                "based_on_emotion": emotion,
            }
            meta["metadata"]["wellness_plan_source"] = "llm"
        except Exception as exc:
            # Degrade gracefully rather than failing the whole turn --
            # a missed wellness suggestion is not worth breaking the response.
            activity = _FALLBACK_ACTIVITY
            plan = {
                "activity": activity,
                "rationale": "general fallback suggestion",
                "steps": [],
                "duration_minutes": 1,
                "based_on_emotion": emotion,
            }
            meta["metadata"]["wellness_plan_source"] = "fallback"
            meta["metadata"]["wellness_plan_error"] = str(exc)

    return {
        "recommended_activity": activity,
        "wellness_plan": plan,
        "metadata": meta["metadata"],
    }
