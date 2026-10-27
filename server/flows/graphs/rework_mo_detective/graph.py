"""Compile Rework MO detective graph."""

from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from flows.graphs.rework_mo_detective.nodes import (
    apply_reasons_node,
    classify_case_node,
    list_orders,
    narrate_with_llm,
    persist,
    run_checks_node,
)
from flows.graphs.rework_mo_detective.state import DetectiveState


def build_graph():
    builder = StateGraph(DetectiveState)
    builder.add_node("list_orders", list_orders)
    builder.add_node("classify_case", classify_case_node)
    builder.add_node("run_checks", run_checks_node)
    builder.add_node("apply_reasons", apply_reasons_node)
    builder.add_node("narrate", narrate_with_llm)
    builder.add_node("persist", persist)

    builder.add_edge(START, "list_orders")
    builder.add_edge("list_orders", "classify_case")
    builder.add_edge("classify_case", "run_checks")
    builder.add_edge("run_checks", "apply_reasons")
    builder.add_edge("apply_reasons", "narrate")
    builder.add_edge("narrate", "persist")
    builder.add_edge("persist", END)
    return builder.compile()


graph = build_graph()
