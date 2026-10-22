"""Thin graph nodes for Rework MO detective."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from flows.config.settings import get_settings
from flows.domain.rework_mo.analyze import (
    analyze_order,
    list_unique_orders,
    load_rework_mo_tables,
)
from flows.graphs.rework_mo_detective.prompts import SYSTEM_NARRATIVE, build_user_payload
from flows.graphs.rework_mo_detective.state import DetectiveState
from flows.llm.azure_apim import get_chat_model
from flows.schemas.rework_mo import OrderSummary


def resolve_data_dir(state: DetectiveState) -> Path:
    if state.get("data_dir"):
        return Path(state["data_dir"])
    return get_settings().rework_mo_data_dir()


def load_and_list_orders(state: DetectiveState) -> dict[str, Any]:
    data_dir = resolve_data_dir(state)
    tables = load_rework_mo_tables(data_dir)
    orders = list_unique_orders(tables.qv)
    lines = "\n".join(f"- {o}" for o in orders) or "（無工單）"
    msg = AIMessage(
        content=(
            f"📋 待分析工單清單（共 {len(orders)} 筆）\n"
            f"資料目錄：`{data_dir}`\n{lines}"
        )
    )
    return {"orders": orders, "data_dir": str(data_dir), "messages": [msg]}


def analyze_orders(state: DetectiveState) -> dict[str, Any]:
    data_dir = resolve_data_dir(state)
    tables = load_rework_mo_tables(data_dir)
    orders = state.get("orders") or list_unique_orders(tables.qv)
    limit = get_settings().flows_analysis_limit
    analyses = [analyze_order(tables, o).to_dict() for o in orders[:limit]]
    preview = json.dumps(analyses, ensure_ascii=False, indent=2)
    msg = AIMessage(
        content=(
            f"🔍 規則引擎分析完成（本輪 {len(analyses)}/{len(orders)} 筆）\n"
            f"```json\n{preview}\n```"
        )
    )
    return {"orders": orders, "analyses": analyses, "messages": [msg]}


def narrate_with_llm(state: DetectiveState) -> dict[str, Any]:
    analyses = state.get("analyses") or []
    if not analyses:
        return {"messages": [AIMessage(content="沒有可敘事的分析結果。")]}

    model = get_chat_model(temperature=0.2)
    structured = model.with_structured_output(OrderSummary)
    narratives: list[str] = []
    enriched: list[dict[str, Any]] = []

    for item in analyses:
        try:
            summary: OrderSummary = structured.invoke(
                [
                    SystemMessage(content=SYSTEM_NARRATIVE),
                    HumanMessage(content=build_user_payload(item)),
                ]
            )
            merged = {**item, "llm": summary.model_dump()}
            if summary.reason_draft.reason:
                merged["suggested_reason"] = summary.reason_draft.reason
            enriched.append(merged)
            narratives.append(
                f"### 工單 {summary.order_number}\n"
                f"{summary.narrative}\n"
                f"- Reason：{summary.reason_draft.reason}\n"
                f"- 改善：{summary.reason_draft.improvement}"
            )
        except Exception as exc:  # noqa: BLE001 — keep pipeline resilient
            fallback = {
                **item,
                "llm_error": f"{type(exc).__name__}: {exc}",
            }
            enriched.append(fallback)
            narratives.append(
                f"### 工單 {item.get('order_number')}\n"
                f"規則建議 Reason：{item.get('suggested_reason')}\n"
                f"（LLM 敘事失敗：{type(exc).__name__}）"
            )

    msg = AIMessage(content="📝 分析報告\n\n" + "\n\n".join(narratives))
    return {"analyses": enriched, "messages": [msg]}


def write_outputs(state: DetectiveState) -> dict[str, Any]:
    analyses = state.get("analyses") or []
    out_dir = get_settings().outputs_dir()
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "rework_mo_detective_mvp.json"
    payload = {
        "orders": state.get("orders") or [],
        "analyses": analyses,
    }
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    msg = AIMessage(content=f"✅ 已寫出結果：`{out_path}`")
    return {"output_path": str(out_path), "messages": [msg]}
