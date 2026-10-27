"""Compile qv_dms_pipeline graph."""

from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from flows.graphs.qv_dms_pipeline.nodes import (
    analyze_periods,
    cover_6501,
    cover_acct,
    cover_format,
    cover_init,
    cover_inv,
    cover_material_pivot,
    cover_mo,
    inventory_inputs,
    narrate_status,
    persist,
    render_html_node,
)
from flows.graphs.qv_dms_pipeline.state import QvDmsState


def build_graph():
    b = StateGraph(QvDmsState)
    b.add_node("inventory", inventory_inputs)
    b.add_node("cover_init", cover_init)
    b.add_node("cover_material_pivot", cover_material_pivot)
    b.add_node("cover_mo", cover_mo)
    b.add_node("cover_acct", cover_acct)
    b.add_node("cover_6501", cover_6501)
    b.add_node("cover_inv", cover_inv)
    b.add_node("cover_format", cover_format)
    b.add_node("analyze_periods", analyze_periods)
    b.add_node("narrate", narrate_status)
    b.add_node("render_html", render_html_node)
    b.add_node("persist", persist)

    b.add_edge(START, "inventory")
    b.add_edge("inventory", "cover_init")
    b.add_edge("cover_init", "cover_material_pivot")
    b.add_edge("cover_material_pivot", "cover_mo")
    b.add_edge("cover_mo", "cover_acct")
    b.add_edge("cover_acct", "cover_6501")
    b.add_edge("cover_6501", "cover_inv")
    b.add_edge("cover_inv", "cover_format")
    b.add_edge("cover_format", "analyze_periods")
    b.add_edge("analyze_periods", "narrate")
    b.add_edge("narrate", "render_html")
    b.add_edge("render_html", "persist")
    b.add_edge("persist", END)
    return b.compile()


graph = build_graph()
