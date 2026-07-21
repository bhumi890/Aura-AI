"""
ai_core/graph/edges.py

Conditional-edge functions -- the actual "coordination" logic (Part 7).
Kept separate from node code: nodes produce data, these functions make
routing decisions based on that data. This separation means routing logic
can be unit-tested independently of the LLM calls inside nodes.
"""
from ai_core.state.schema import WellnessState


def route_after_safety(state: WellnessState) -> str:
    """
    The one non-negotiable gate. No routing logic anywhere else in the
    graph can override this -- crisis always short-circuits past both
    supervisors and every other node.
    """
    status = state.get("safety_status", "unknown")
    if status == "crisis":
        return "crisis_response"
    return "supervisor_entry"


def route_after_entry(state: WellnessState) -> list[str]:
    """
    Fan-out targets. emotion_node and memory_agent always run;
    rag_node only runs if supervisor_entry flagged it as needed via
    route_plan.needs_rag.
    """
    branches = ["emotion_node", "memory_agent"]
    if state.get("route_plan", {}).get("needs_rag"):
        branches.append("rag_node")
    return branches


def route_after_fanout(state: WellnessState) -> str:
    """
    Join point after the parallel fan-out. Only reached once every
    activated parallel branch has completed (LangGraph enforces this
    structurally). Decides whether wellness_plan_node runs before
    final synthesis.
    """
    if state.get("route_plan", {}).get("needs_wellness_plan"):
        return "wellness_plan_node"
    return "supervisor_final"
