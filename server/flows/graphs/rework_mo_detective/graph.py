"""Compile Rework MO detective graph."""

from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from flows.graphs.rework_mo_detective.nodes import (
    analyze_orders,
    load_and_list_orders,
    narrate_with_llm,
    write_outputs,
)
from flows.graphs.rework_mo_detective.state import DetectiveState


def build_graph():
    builder = StateGraph(DetectiveState)
    builder.add_node("list_orders", load_and_list_orders)
    builder.add_node("analyze", analyze_orders)
    builder.add_node("narrate", narrate_with_llm)
    builder.add_node("persist", write_outputs)

    builder.add_edge(START, "list_orders")
    builder.add_edge("list_orders", "analyze")
    builder.add_edge("analyze", "narrate")
    builder.add_edge("narrate", "persist")
    builder.add_edge("persist", END)
    return builder.compile()


graph = build_graph()
