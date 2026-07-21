"""
ai_core/agents/supervisor/entry.py

supervisor_entry (Part 5): cheap, fast intent classification. Runs after
the safety node has already cleared the message as non-crisis -- this
node NEVER makes safety judgments itself. Writes only `route_plan`,
which downstream conditional edges (graph/edges.py) use to decide fan-out.
"""
from typing import Literal
from pydantic import BaseModel, Field
from langchain_core.messages import SystemMessage

from ai_core.state.schema import WellnessState
from ai_core.llm.clients import get_fast_llm
from ai_core.prompts.supervisor_entry import SUPERVISOR_ENTRY_PROMPT
from ai_core.config import ENTRY_HISTORY_WINDOW
from ai_core.utils.metrics import timed_metadata


class IntentClassification(BaseModel):
    intent: Literal[
        "venting", "seeking_advice", "check_in",
        "information_seeking", "crisis_adjacent", "small_talk"
    ] = Field(description="Primary intent of the user's message")
    needs_rag: bool = Field(
        description="True only if the user is asking something that needs "
                    "external knowledge (coping techniques, factual info about "
                    "conditions, exercises) rather than just conversational support"
    )
    needs_wellness_plan: bool = Field(
        description="True if the user is asking for or would benefit from a "
                    "structured activity/plan recommendation"
    )


async def supervisor_entry(state: WellnessState) -> dict:
    with timed_metadata("supervisor_entry") as meta:
        recent = state.get("chat_history", [])[-ENTRY_HISTORY_WINDOW:]
        recent_str = "\n".join(f"{m.type}: {m.content}" for m in recent)

        structured_llm = get_fast_llm().with_structured_output(IntentClassification)
        result = await structured_llm.ainvoke([
            SystemMessage(content=SUPERVISOR_ENTRY_PROMPT.format(
                recent_history=recent_str,
                user_message=state["user_message"],
            ))
        ])
        meta["metadata"]["supervisor_entry_intent"] = result.intent

    return {
        "route_plan": {
            "intent": result.intent,
            "needs_rag": result.needs_rag,
            "needs_wellness_plan": result.needs_wellness_plan,
        },
        "metadata": meta["metadata"],
    }
