from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from flows.config.settings import get_settings
from flows.domain.excel_io import load_excel
from flows.domain.qv_dms.cover import (
    analyze_period_top3,
    build_material_pivot,
    fill_65011201,
    fill_accounting,
    fill_inventory_adj,
    fill_production_mo,
    load_cover,
    match_and_fill_pcl500,
    render_qv_html,
)
from flows.domain.qv_dms.inventory import inventory_qv_dms
from flows.graphs._observe import node_message
from flows.graphs._paths import resolve_data_dir
from flows.graphs.qv_dms_pipeline.prompts import SYSTEM
from flows.graphs.qv_dms_pipeline.state import QvDmsState
from flows.llm.azure_apim import get_chat_model
from flows.schemas.qv_dms import PipelineAdvice


def _data_dir(state: QvDmsState) -> Path:
    return resolve_data_dir(state, get_settings().qv_dms_data_dir)


def _working_cover_path() -> Path:
    out = get_settings().outputs_dir()
    out.mkdir(parents=True, exist_ok=True)
    return out / "_qv_cover_working.xlsx"


def inventory_inputs(state: QvDmsState) -> dict[str, Any]:
    data_dir = _data_dir(state)
    inv = inventory_qv_dms(data_dir).to_dict()
    msg = node_message(
        node="inventory",
        kind="program",
        inputs={"data_dir": str(data_dir)},
        outputs=inv,
    )
    return {"data_dir": str(data_dir), "inventory": inv, "messages": [msg]}


def cover_init(state: QvDmsState) -> dict[str, Any]:
    data_dir = _data_dir(state)
    cover = load_cover(data_dir)
    path = _working_cover_path()
    cover.to_excel(path, index=False)
    summary = {"cover_working": str(path), "rows": len(cover), "steps_done": ["cover_init"]}
    msg = node_message(
        node="cover_init",
        kind="program",
        outputs=summary,
    )
    return {"cover_summary": summary, "messages": [msg]}


def cover_material_pivot(state: QvDmsState) -> dict[str, Any]:
    data_dir = _data_dir(state)
    path = _working_cover_path()
    cover = load_excel(path) if path.is_file() else load_cover(data_dir)
    summary = dict(state.get("cover_summary") or {})
    notes: list[str] = list(summary.get("notes") or [])
    steps = list(summary.get("steps_done") or [])
    mat_path = data_dir / "材料分析.xlsx"
    if not mat_path.is_file():
        notes.append("QV-02：缺當期材料分析.xlsx，跳過 1.1")
        steps.append("1.1_skipped")
    else:
        pivot = build_material_pivot(load_excel(mat_path))
        cover, filled, unmatched, ok = match_and_fill_pcl500(cover, pivot)
        cover.to_excel(path, index=False)
        summary.update(
            {
                "filled_count": filled,
                "unmatched_reasons": unmatched,
                "validation_ok": ok,
            }
        )
        steps.append("1.1_material_pivot")
        notes.append(f"回填 {filled} 筆；validation_ok={ok}")
    summary["notes"] = notes
    summary["steps_done"] = steps
    msg = node_message(node="cover_material_pivot", kind="program", outputs=summary)
    return {"cover_summary": summary, "messages": [msg]}


def cover_mo(state: QvDmsState) -> dict[str, Any]:
    return _cover_step(
        state,
        step="1.2_production_mo",
        filename="生產工單.xlsx",
        fn=fill_production_mo,
        node="cover_mo",
    )


def cover_acct(state: QvDmsState) -> dict[str, Any]:
    return _cover_step(
        state,
        step="1.3_accounting",
        filename="會計調整.xlsx",
        fn=fill_accounting,
        node="cover_acct",
    )


def cover_6501(state: QvDmsState) -> dict[str, Any]:
    return _cover_step(
        state,
        step="1.4_65011201",
        filename="65011201.xlsx",
        fn=fill_65011201,
        node="cover_6501",
    )


def cover_inv(state: QvDmsState) -> dict[str, Any]:
    return _cover_step(
        state,
        step="1.5_inventory",
        filename="庫存調整單.xlsx",
        fn=fill_inventory_adj,
        node="cover_inv",
    )


def _cover_step(
    state: QvDmsState,
    *,
    step: str,
    filename: str,
    fn,
    node: str,
) -> dict[str, Any]:
    data_dir = _data_dir(state)
    path = _working_cover_path()
    cover = load_excel(path) if path.is_file() else load_cover(data_dir)
    summary = dict(state.get("cover_summary") or {})
    notes = list(summary.get("notes") or [])
    steps = list(summary.get("steps_done") or [])
    src = data_dir / filename
    if src.is_file():
        cover, step_notes = fn(cover, load_excel(src))
        cover.to_excel(path, index=False)
        notes.extend(step_notes)
        steps.append(step)
    else:
        notes.append(f"缺 {filename}，跳過 {step}")
    summary["notes"] = notes
    summary["steps_done"] = steps
    msg = node_message(node=node, kind="program", outputs={"step": step, "notes_tail": notes[-3:]})
    return {"cover_summary": summary, "messages": [msg]}


def cover_format(state: QvDmsState) -> dict[str, Any]:
    summary = dict(state.get("cover_summary") or {})
    notes = list(summary.get("notes") or [])
    steps = list(summary.get("steps_done") or [])
    steps.append("1.6_format_keep_values")
    notes.append("QV-03：寫入通知草稿（不實發）")
    out_dir = get_settings().outputs_dir()
    draft = out_dir / "qv_dms_notify_draft.txt"
    draft.write_text(
        "QV DMS Cover 已更新（本機草稿，未發送 Email/Teams）\n"
        + "\n".join(summary.get("steps_done") or []),
        encoding="utf-8",
    )
    summary["notes"] = notes
    summary["steps_done"] = steps
    summary["notify_draft"] = str(draft)
    msg = node_message(node="cover_format", kind="program", outputs=summary)
    return {"cover_summary": summary, "messages": [msg]}


def analyze_periods(state: QvDmsState) -> dict[str, Any]:
    data_dir = _data_dir(state)
    result: dict[str, Any] = {}
    cur = data_dir / "材料分析.xlsx"
    prev = data_dir / "材料分析-previous.xlsx"
    if cur.is_file():
        result["current"] = analyze_period_top3(load_excel(cur), label="current")
    else:
        result["current"] = {"skipped": True, "reason": "缺當期材料分析"}
    if prev.is_file():
        result["previous"] = analyze_period_top3(load_excel(prev), label="previous")
    else:
        result["previous"] = {"skipped": True}
    msg = node_message(node="analyze_periods", kind="program", outputs=result)
    return {"period_analysis": result, "messages": [msg]}


def narrate_status(state: QvDmsState) -> dict[str, Any]:
    payload = {
        "inventory": state.get("inventory"),
        "cover_summary": state.get("cover_summary"),
        "period_analysis": state.get("period_analysis"),
    }
    narrative: dict[str, Any] = {}
    try:
        model = get_chat_model(temperature=0.2)
        structured = model.with_structured_output(PipelineAdvice)
        advice: PipelineAdvice = structured.invoke(
            [
                SystemMessage(content=SYSTEM),
                HumanMessage(content=json.dumps(payload, ensure_ascii=False, default=str)[:12000]),
            ]
        )
        narrative = advice.model_dump()
    except Exception as exc:  # noqa: BLE001 — Cover/HTML already done by program steps
        narrative = {
            "can_start_cover": True,
            "blockers": [],
            "next_actions": ["檢查 outputs 中的 Cover 與 HTML"],
            "summary": f"LLM 失敗，僅保留程式結果：{type(exc).__name__}",
        }
    msg = node_message(node="narrate", kind="llm", outputs=narrative)
    return {"narrative": narrative, "messages": [msg]}


def render_html_node(state: QvDmsState) -> dict[str, Any]:
    html = render_qv_html(state.get("cover_summary") or {}, state.get("narrative"))
    msg = node_message(node="render_html", kind="program", outputs={"html_chars": len(html)})
    return {"html": html, "messages": [msg]}


def persist(state: QvDmsState) -> dict[str, Any]:
    out_dir = get_settings().outputs_dir()
    out_dir.mkdir(parents=True, exist_ok=True)
    working = _working_cover_path()
    xlsx_path = out_dir / "qv_dms_Cover_updated.xlsx"
    if working.is_file():
        xlsx_path.write_bytes(working.read_bytes())
    html_path = out_dir / "qv_dms_pipeline.html"
    html_path.write_text(state.get("html") or "", encoding="utf-8")
    json_path = out_dir / "qv_dms_pipeline.json"
    json_path.write_text(
        json.dumps(
            {
                "inventory": state.get("inventory"),
                "cover_summary": state.get("cover_summary"),
                "period_analysis": state.get("period_analysis"),
                "narrative": state.get("narrative"),
            },
            ensure_ascii=False,
            indent=2,
            default=str,
        ),
        encoding="utf-8",
    )
    msg = node_message(
        node="persist",
        kind="program",
        outputs={"json": str(json_path), "xlsx": str(xlsx_path), "html": str(html_path)},
    )
    return {
        "output_path": str(json_path),
        "output_xlsx": str(xlsx_path),
        "output_html": str(html_path),
        "messages": [msg],
    }
