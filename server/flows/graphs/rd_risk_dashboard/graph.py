"""Compile rd_risk_dashboard graph."""

from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from flows.graphs.rd_risk_dashboard.nodes import (
    aggregate_kpi,
    load_data,
    narrate_dashboard,
    persist,
    render_html,
    scan_all,
)
from flows.graphs.rd_risk_dashboard.state import RdRiskState


def build_graph():
    b = StateGraph(RdRiskState)
    b.add_node("load_data", load_data)
    b.add_node("scan_all", scan_all)
    b.add_node("aggregate_kpi", aggregate_kpi)
    b.add_node("narrate", narrate_dashboard)
    b.add_node("render_html", render_html)
    b.add_node("persist", persist)

    b.add_edge(START, "load_data")
    b.add_edge("load_data", "scan_all")
    b.add_edge("scan_all", "aggregate_kpi")
    b.add_edge("aggregate_kpi", "narrate")
    b.add_edge("narrate", "render_html")
    b.add_edge("render_html", "persist")
    b.add_edge("persist", END)
    return b.compile()


graph = build_graph()
