from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from flows.graphs.rd_risk_dashboard.nodes import (
    load_data,
    narrate_dashboard,
    persist,
    scan_anomalies,
)
from flows.graphs.rd_risk_dashboard.state import RdRiskState


def build_graph():
    b = StateGraph(RdRiskState)
    b.add_node("load_data", load_data)
    b.add_node("scan", scan_anomalies)
    b.add_node("narrate", narrate_dashboard)
    b.add_node("persist", persist)
    b.add_edge(START, "load_data")
    b.add_edge("load_data", "scan")
    b.add_edge("scan", "narrate")
    b.add_edge("narrate", "persist")
    b.add_edge("persist", END)
    return b.compile()


graph = build_graph()
