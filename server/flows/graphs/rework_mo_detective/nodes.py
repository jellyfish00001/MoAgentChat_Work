"""Graph nodes for Rework MO detective — observable I/O."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from flows.config.settings import get_settings
from flows.domain.rework_mo.analyze import (
    analyze_order,
    apply_reasons_to_qv,
    list_unique_orders,
    load_rework_mo_tables,
)
from flows.graphs._observe import node_message, preview_list
from flows.graphs._paths import resolve_data_dir
from flows.graphs.rework_mo_detective.prompts import SYSTEM_NARRATIVE, build_user_payload
from flows.graphs.rework_mo_detective.state import DetectiveState
from flows.llm.azure_apim import get_chat_model
from flows.schemas.rework_mo import OrderSummary


def _data_dir(state: DetectiveState) -> Path:
    return resolve_data_dir(state, get_settings().rework_mo_data_dir)


def list_orders(state: DetectiveState) -> dict[str, Any]:
    data_dir = _data_dir(state)
    # Reload per node: LangGraph may resume mid-graph; avoid assuming in-memory tables in state.
    tables = load_rework_mo_tables(data_dir)
    orders = list_unique_orders(tables.qv)
    lines = "\n".join(f"| {o} |" for o in orders) or "| （無） |"
    md = (
        "🔎 **小侦探已为您锁定待分析的 Rework MO 工单清单：**\n"
        "| Order Number |\n| :--- |\n"
        f"{lines}"
    )
    msg = node_message(
        node="list_orders",
        kind="program",
        inputs={"data_dir": str(data_dir)},
        outputs={"order_count": len(orders), "orders": preview_list(orders)},
        note=md,
    )
    return {"orders": orders, "data_dir": str(data_dir), "messages": [msg]}


def classify_case_node(state: DetectiveState) -> dict[str, Any]:
    data_dir = _data_dir(state)
    tables = load_rework_mo_tables(data_dir)
    orders = state.get("orders") or list_unique_orders(tables.qv)
    limit = get_settings().flows_analysis_limit
    classifications: list[dict[str, Any]] = []
    for o in orders[:limit]:
        analysis = analyze_order(tables, o)
        classifications.append(
            {
                "order_number": analysis.order_number,
                "case_type": analysis.case_type.value,
                "movement_types": analysis.movement_types,
                "materials": analysis.materials,
                "notes": analysis.notes,
            }
        )
    msg = node_message(
        node="classify_case",
        kind="program",
        inputs={"orders": preview_list(orders), "limit": limit},
        outputs={"classifications": classifications},
    )
    return {"orders": orders, "classifications": classifications, "messages": [msg]}


def run_checks_node(state: DetectiveState) -> dict[str, Any]:
    data_dir = _data_dir(state)
    tables = load_rework_mo_tables(data_dir)
    orders = state.get("orders") or list_unique_orders(tables.qv)
    limit = get_settings().flows_analysis_limit
    analyses = [analyze_order(tables, o).to_dict() for o in orders[:limit]]
    msg = node_message(
        node="run_checks",
        kind="program",
        inputs={"order_count": len(orders[:limit])},
        outputs={
            "analyses_preview": [
                {
                    "order": a["order_number"],
                    "case": a["case_type"],
                    "finding_count": len((a.get("checks") or {}).get("findings") or []),
                    "suggested_reason": a.get("suggested_reason"),
                }
                for a in analyses
            ]
        },
    )
    return {"analyses": analyses, "messages": [msg]}


def apply_reasons_node(state: DetectiveState) -> dict[str, Any]:
    analyses = state.get("analyses") or []
    summary = [
        {
            "order": a.get("order_number"),
            "row_reasons": a.get("row_reasons"),
            "suggested_reason": a.get("suggested_reason"),
        }
        for a in analyses
    ]
    msg = node_message(
        node="apply_reasons",
        kind="program",
        inputs={"analysis_count": len(analyses)},
        outputs={"row_reason_summary": summary},
        note="Reason 碼由程式鎖定，供 persist 寫回 Excel",
    )
    return {"messages": [msg]}


def narrate_with_llm(state: DetectiveState) -> dict[str, Any]:
    analyses = state.get("analyses") or []
    if not analyses:
        return {
            "messages": [
                node_message(
                    node="narrate",
                    kind="llm",
                    outputs={"skipped": True},
                    note="無分析結果",
                )
            ]
        }

    model = get_chat_model(temperature=0.2)
    structured = model.with_structured_output(OrderSummary)
    narratives: list[str] = []
    enriched: list[dict[str, Any]] = []

    for item in analyses:
        locked_reason = str(item.get("suggested_reason") or "")
        try:
            summary: OrderSummary = structured.invoke(
                [
                    SystemMessage(content=SYSTEM_NARRATIVE),
                    HumanMessage(content=build_user_payload(item)),
                ]
            )
            # Reason codes are program-owned; keep LLM for narrative/confidence only.
            merged = {
                **item,
                "llm": {
                    **summary.model_dump(),
                    "reason_draft": {
                        "reason": locked_reason,
                        "confidence": summary.reason_draft.confidence,
                        "improvement": summary.reason_draft.improvement,
                    },
                },
            }
            enriched.append(merged)
            narratives.append(
                f"### 工單 {summary.order_number}\n"
                f"{summary.narrative}\n"
                f"- Reason（程式）：{locked_reason}\n"
                f"- 改善：{summary.reason_draft.improvement}"
            )
        except Exception as exc:  # noqa: BLE001 — degrade: pipeline still persists program Reasons
            enriched.append({**item, "llm_error": f"{type(exc).__name__}: {exc}"})
            narratives.append(
                f"### 工單 {item.get('order_number')}\n"
                f"Reason（程式）：{locked_reason}\n"
                f"（LLM 敘事失敗：{type(exc).__name__}）"
            )

    msg = node_message(
        node="narrate",
        kind="llm",
        inputs={"count": len(analyses)},
        outputs={"narrative_count": len(narratives)},
        note="\n\n".join(narratives)[:2000],
    )
    return {"analyses": enriched, "narratives": narratives, "messages": [msg]}


def persist(state: DetectiveState) -> dict[str, Any]:
    analyses = state.get("analyses") or []
    out_dir = get_settings().outputs_dir()
    out_dir.mkdir(parents=True, exist_ok=True)

    data_dir = _data_dir(state)
    tables = load_rework_mo_tables(data_dir)
    qv_out = apply_reasons_to_qv(tables.qv, analyses)
    xlsx_path = out_dir / "rework_mo_QV_Report-Material_reasons.xlsx"
    qv_out.to_excel(xlsx_path, index=False)

    json_path = out_dir / "rework_mo_detective.json"
    payload = {"orders": state.get("orders") or [], "analyses": analyses}
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    txt_path = out_dir / "rework_mo_所有工单_分析报告.txt"
    blocks = state.get("narratives") or []
    if not blocks:
        blocks = [
            f"{a.get('order_number')}: {a.get('case_type')} / {a.get('suggested_reason')}"
            for a in analyses
        ]
    txt_path.write_text("\n\n".join(blocks), encoding="utf-8")

    msg = node_message(
        node="persist",
        kind="program",
        outputs={
            "json": str(json_path),
            "xlsx": str(xlsx_path),
            "txt": str(txt_path),
        },
    )
    return {
        "output_path": str(json_path),
        "output_xlsx": str(xlsx_path),
        "output_txt": str(txt_path),
        "messages": [msg],
    }
