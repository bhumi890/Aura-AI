"""
ai_core/state/schema.py

The single source of truth for shared pipeline state (Part 4).
Every node reads from and writes to WellnessState. No other file should
redefine or duplicate these field names.
"""
from typing import TypedDict, Optional, List, Dict, Any, Literal, Annotated
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

from ai_core.state.reducers import merge_metadata


class RoutePlan(TypedDict):
    """
    Transient routing artifact produced by supervisor_entry (Part 5).
    Not one of the 13 canonical user-facing fields -- internal scratch
    state used only to drive conditional edges.
    """
    intent: str
    needs_rag: bool
    needs_wellness_plan: bool


class WellnessState(TypedDict, total=False):
    """
    Shared state contract for the HomeMind LangGraph pipeline.

    total=False: not every field is populated on every turn (e.g. the
    crisis short-circuit path never touches retrieved_documents).
    Nodes MUST use state.get(field, default) rather than state[field].
    """

    # -- Identity & session --------------------------------------------
    user_id: str
    session_id: str

    # -- Conversation memory --------------------------------------------
    chat_history: Annotated[List[BaseMessage], add_messages]
    user_message: str

    # -- Routing (Part 5) -------------------------------------------------
    route_plan: Optional[RoutePlan]

    # -- Emotion analysis -----------------------------------------------
    emotion: Optional[str]
    emotion_confidence: Optional[float]

    # -- Long-term memory & retrieval -------------------------------------
    memory_summary: Optional[str]
    retrieved_documents: Optional[List[Dict[str, Any]]]

    # -- Safety (gatekeeper field -- written ONLY by the safety node) -----
    safety_status: Literal["safe", "at_risk", "crisis", "unknown"]

    # -- Wellness output --------------------------------------------------
    recommended_activity: Optional[str]
    wellness_plan: Optional[Dict[str, Any]]

    # -- Final output (written ONLY by supervisor_final) -------------------
    final_response: Optional[str]

    # -- Cross-cutting telemetry (multi-writer, merge reducer) -------------
    metadata: Annotated[Dict[str, Any], merge_metadata]
