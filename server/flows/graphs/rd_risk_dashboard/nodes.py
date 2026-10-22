from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from flows.config.settings import get_settings
from flows.domain.rd_risk.scan import load_rd_tables, scan_rd_risks
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
    msg = AIMessage(
        content=(
            f"📂 已載入 R&D 資料目錄：`{data_dir}`\n"
            f"- COOIS 列數：{len(tables.header)}\n"
            f"- 領退料列數：{len(tables.movements)}"
        )
    )
    return {"data_dir": str(data_dir), "messages": [msg]}


def scan_anomalies(state: RdRiskState) -> dict[str, Any]:
    settings = get_settings()
    tables = load_rd_tables(_data_dir(state))
    result = scan_rd_risks(tables, sample_limit=settings.flows_rd_sample_limit)
    payload = result.to_dict()
    preview = json.dumps(payload, ensure_ascii=False, indent=2)
    msg = AIMessage(
        content=(
            f"🔍 風險掃描（MVP）\n"
            f"- 工單數：{result.order_count}\n"
            f"- 流程倒置候選：{len(result.inversion_orders)}\n"
            f"- 待補檢查：{', '.join(result.todo_checks[:3])}…\n"
            f"```json\n{preview[:2500]}\n```"
        )
    )
    return {"scan": payload, "messages": [msg]}


def narrate_dashboard(state: RdRiskState) -> dict[str, Any]:
    scan = state.get("scan") or {}
    model = get_chat_model(temperature=0.2)
    structured = model.with_structured_output(DashboardBrief)
    try:
        brief: DashboardBrief = structured.invoke(
            [
                SystemMessage(content=SYSTEM),
                HumanMessage(content=json.dumps(scan, ensure_ascii=False)),
            ]
        )
        body = (
            f"## {brief.headline}\n\n"
            f"### 風險\n"
            + "\n".join(f"- {r}" for r in brief.risks)
            + "\n\n### 行動\n"
            + "\n".join(f"- {a}" for a in brief.actions)
        )
        scan = {**scan, "llm": brief.model_dump()}
    except Exception as exc:  # noqa: BLE001
        body = f"LLM 摘要失敗：{type(exc).__name__}: {exc}\n規則 notes：{scan.get('notes')}"
    return {"scan": scan, "messages": [AIMessage(content=body)]}


def persist(state: RdRiskState) -> dict[str, Any]:
    out_dir = get_settings().outputs_dir()
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "rd_risk_dashboard_mvp.json"
    path.write_text(
        json.dumps(state.get("scan") or {}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return {
        "output_path": str(path),
        "messages": [AIMessage(content=f"✅ 已寫出：`{path}`")],
    }
