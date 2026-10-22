from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from flows.graphs.qv_dms_pipeline.nodes import (
    inventory_inputs,
    narrate_status,
    persist,
    plan_pipeline,
)
from flows.graphs.qv_dms_pipeline.state import QvDmsState


def build_graph():
    b = StateGraph(QvDmsState)
    b.add_node("inventory", inventory_inputs)
    b.add_node("plan", plan_pipeline)
    b.add_node("narrate", narrate_status)
    b.add_node("persist", persist)
    b.add_edge(START, "inventory")
    b.add_edge("inventory", "plan")
    b.add_edge("plan", "narrate")
    b.add_edge("narrate", "persist")
    b.add_edge("persist", END)
    return b.compile()


graph = build_graph()
