"""Compile the single-workbook FAA-29 backfill graph."""

from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from flows.graphs.qv_dms_pipeline.nodes import (
    cover_6501,
    cover_acct,
    cover_inv,
    cover_material,
    cover_mo,
    inventory_inputs,
    persist,
    respond,
)
from flows.graphs.qv_dms_pipeline.state import QvDmsState


def build_graph():
    builder = StateGraph(QvDmsState)
    builder.add_node("inventory", inventory_inputs)
    builder.add_node("cover_material", cover_material)
    builder.add_node("cover_mo", cover_mo)
    builder.add_node("cover_acct", cover_acct)
    builder.add_node("cover_6501", cover_6501)
    builder.add_node("cover_inv", cover_inv)
    builder.add_node("persist", persist)
    builder.add_node("respond", respond)
    builder.add_edge(START, "inventory")
    builder.add_conditional_edges(
        "inventory",
        lambda state: "respond" if state["status"] == "failed" else "cover_material",
        ["respond", "cover_material"],
    )
    builder.add_edge("cover_material", "cover_mo")
    builder.add_edge("cover_mo", "cover_acct")
    builder.add_edge("cover_acct", "cover_6501")
    builder.add_edge("cover_6501", "cover_inv")
    builder.add_edge("cover_inv", "persist")
    builder.add_edge("persist", "respond")
    builder.add_edge("respond", END)
    return builder.compile()


graph = build_graph()
