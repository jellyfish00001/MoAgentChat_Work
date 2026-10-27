from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from flows.config.settings import get_settings
from flows.domain.rd_risk.html_report import render_rd_dashboard
from flows.domain.rd_risk.scan import load_rd_tables, scan_rd_risks
from flows.graphs._observe import node_message
from flows.graphs.rd_risk_dashboard.prompts import SYSTEM
from flows.graphs.rd_risk_dashboard.state import RdRiskState
from flows.llm.azure_apim import get_chat_model
from flows.schemas.rd_risk import DashboardBrief


def _data_dir(state: RdRiskState) -> Path:
    if state.get("data_dir"):
        return Path(state["data_dir"])
    return get_settings().rd_risk_data_dir()


def load_data(state: RdRiskState) -> dict[str, Any]:
    data_dir = _data_dir(state)
    tables = load_rd_tables(data_dir)
    msg = node_message(
        node="load_data",
        kind="program",
        inputs={"data_dir": str(data_dir)},
        outputs={
            "header_rows": len(tables.header),
            "movement_rows": len(tables.movements),
            "has_bom": tables.bom is not None,
            "has_missrate": tables.missrate is not None,
        },
    )
    return {"data_dir": str(data_dir), "messages": [msg]}


def scan_all(state: RdRiskState) -> dict[str, Any]:
    settings = get_settings()
    tables = load_rd_tables(_data_dir(state))
    result = scan_rd_risks(tables, sample_limit=settings.flows_rd_sample_limit)
    payload = result.to_dict()
    msg = node_message(
        node="scan_all",
        kind="program",
        inputs={"sample_limit": settings.flows_rd_sample_limit},
        outputs={
            "order_count": result.order_count,
            "inversions": len(result.inversion_orders),
            "missrate": len(result.missrate_anomalies),
            "misuse": len(result.misuse_anomalies),
            "kpi_overdue": len(result.kpi_overdue),
            "dismantle": len(result.dismantle_anomalies),
            "kpi": result.kpi,
        },
    )
    return {"scan": payload, "kpi": result.kpi, "messages": [msg]}


def aggregate_kpi(state: RdRiskState) -> dict[str, Any]:
    kpi = state.get("kpi") or (state.get("scan") or {}).get("kpi") or {}
    msg = node_message(
        node="aggregate_kpi",
        kind="program",
        inputs={},
        outputs={"kpi": kpi},
    )
    return {"kpi": kpi, "messages": [msg]}


def narrate_dashboard(state: RdRiskState) -> dict[str, Any]:
    scan = state.get("scan") or {}
    narrative: dict[str, Any] = {}
    try:
        model = get_chat_model(temperature=0.2)
        structured = model.with_structured_output(DashboardBrief)
        brief: DashboardBrief = structured.invoke(
            [
                SystemMessage(content=SYSTEM),
                HumanMessage(content=json.dumps(scan, ensure_ascii=False)[:12000]),
            ]
        )
        narrative = brief.model_dump()
        scan = {**scan, "llm": narrative}
        note = narrative.get("headline", "")
    except Exception as exc:  # noqa: BLE001
        note = f"LLM 摘要失敗：{type(exc).__name__}: {exc}"
        narrative = {"headline": "規則掃描結果（無 LLM）", "risks": scan.get("notes") or [], "actions": []}
    msg = node_message(
        node="narrate",
        kind="llm",
        outputs={"narrative": narrative},
        note=str(note),
    )
    return {"scan": scan, "narrative": narrative, "messages": [msg]}


def render_html(state: RdRiskState) -> dict[str, Any]:
    scan = state.get("scan") or {}
    narrative = state.get("narrative") or scan.get("llm")
    html = render_rd_dashboard(scan, narrative=narrative)
    msg = node_message(
        node="render_html",
        kind="program",
        outputs={"html_chars": len(html)},
    )
    return {"html": html, "messages": [msg]}


def persist(state: RdRiskState) -> dict[str, Any]:
    out_dir = get_settings().outputs_dir()
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "rd_risk_dashboard.json"
    html_path = out_dir / "rd_risk_dashboard.html"
    json_path.write_text(
        json.dumps(state.get("scan") or {}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    html_path.write_text(state.get("html") or "", encoding="utf-8")
    msg = node_message(
        node="persist",
        kind="program",
        outputs={"json": str(json_path), "html": str(html_path)},
    )
    return {
        "output_path": str(json_path),
        "output_html": str(html_path),
        "messages": [msg],
    }
