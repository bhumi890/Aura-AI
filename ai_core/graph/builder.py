"""
ai_core/graph/builder.py

build_graph(): node registration and topology (Part 7). This file is the
visual representation of the whole pipeline's shape -- safety gate,
two-supervisor pattern, parallel fan-out/fan-in, conditional RAG and
wellness plan.
"""
from langgraph.graph import StateGraph, END

from ai_core.state.schema import WellnessState
from ai_core.agents.safety import safety_node, crisis_response_node
from ai_core.agents.supervisor import supervisor_entry, supervisor_final
from ai_core.agents.emotion import emotion_node
from ai_core.agents.memory import memory_agent
from ai_core.agents.knowledge import rag_node
from ai_core.agents.wellness_plan import wellness_plan_node
from ai_core.graph.edges import route_after_safety, route_after_entry, route_after_fanout


def build_graph() -> StateGraph:
    graph = StateGraph(WellnessState)

    # -- Register nodes --
    graph.add_node("safety_node", safety_node)
    graph.add_node("crisis_response", crisis_response_node)
    graph.add_node("supervisor_entry", supervisor_entry)
    graph.add_node("emotion_node", emotion_node)
    graph.add_node("memory_agent", memory_agent)
    graph.add_node("rag_node", rag_node)
    graph.add_node("wellness_plan_node", wellness_plan_node)
    graph.add_node("supervisor_final", supervisor_final)

    # -- Entry point: safety runs on EVERY turn, unconditionally, first --
    graph.set_entry_point("safety_node")

    # -- Safety gate: crisis short-circuit vs. normal path --
    graph.add_conditional_edges(
        "safety_node",
        route_after_safety,
        {
            "crisis_response": "crisis_response",
            "supervisor_entry": "supervisor_entry",
        },
    )
    graph.add_edge("crisis_response", END)  # crisis path skips everything else

    # -- Fan-out: supervisor_entry's route_plan decides which branches run --
    graph.add_conditional_edges(
        "supervisor_entry",
        route_after_entry,
        ["emotion_node", "memory_agent", "rag_node"],
    )

    # -- Fan-in: all activated parallel branches converge here --
    for branch in ["emotion_node", "memory_agent", "rag_node"]:
        graph.add_conditional_edges(
            branch,
            route_after_fanout,
            {
                "wellness_plan_node": "wellness_plan_node",
                "supervisor_final": "supervisor_final",
            },
        )

    graph.add_edge("wellness_plan_node", "supervisor_final")
    graph.add_edge("supervisor_final", END)

    return graph
