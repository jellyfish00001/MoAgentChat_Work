from __future__ import annotations

from pathlib import Path
from typing import Any
from uuid import uuid4

from langchain_core.messages import AIMessage

from flows.config.settings import get_settings
from flows.domain.qv_dms.workbook import (
    SHEETS,
    DmsInputError,
    aggregate_sheet,
    compare_golden,
    finalize_workbook,
    inspect_workbook,
    save_summary,
)
from flows.graphs._observe import node_message
from flows.graphs._paths import resolve_data_dir
from flows.graphs.qv_dms_pipeline.state import QvDmsState


def inventory_inputs(state: QvDmsState) -> dict[str, Any]:
    data_dir = resolve_data_dir(state, get_settings().qv_dms_data_dir)
    raw = state.get("input_xlsx")
    source = Path(raw) if raw else data_dir / "faa29_sprint2" / "202610 輸入檔.xlsx"
    if not raw and data_dir.name == "faa29_sprint2":
        source = data_dir / "202610 輸入檔.xlsx"
    try:
        layout = inspect_workbook(source)
    except DmsInputError as exc:
        return {
            "status": "failed",
            "error": str(exc),
            "output_xlsx": "",
            "output_path": "",
            "download_url": "",
            "stages": [],
            "cover_summary": {},
            "golden_comparison": {},
        }
    run_id = str(uuid4())
    root = (
        Path(state["output_dir"])
        if state.get("output_dir")
        else (get_settings().outputs_dir() / "qv_dms")
    )
    work_dir = root / run_id
    work_dir.mkdir(parents=True)
    golden = state.get("golden_xlsx", "")
    fixture_golden = source.with_name("202610 標準答案.xlsx")
    if not golden and source.name == "202610 輸入檔.xlsx" and fixture_golden.is_file():
        golden = str(fixture_golden)
    return {
        "status": "processing",
        "error": "",
        "input_xlsx": str(source),
        "layout": layout,
        "run_id": run_id,
        "work_dir": str(work_dir),
        "stages": [],
        "output_xlsx": "",
        "output_path": "",
        "download_url": "",
        "golden_comparison": {},
        "resolved_golden": golden,
        "messages": [
            node_message(
                node="inventory",
                kind="program",
                outputs={"input": source.name, "period": layout["period"], "pcs": layout["pcs"]},
            )
        ],
    }


def _aggregate(state: QvDmsState, name: str) -> dict[str, Any]:
    stage = aggregate_sheet(
        Path(state["input_xlsx"]),
        name,
        state["layout"],
        Path(state["work_dir"]) / f"trace-{SHEETS.index(name)}.csv",
    )
    return {
        "stages": [*state["stages"], stage],
        "messages": [
            node_message(
                node=name,
                kind="program",
                outputs={
                    key: stage[key] for key in ("row_count", "warning_count", "ignored_count")
                },
            )
        ],
    }


def cover_material(state: QvDmsState) -> dict[str, Any]:
    return _aggregate(state, "材料分析")


def cover_mo(state: QvDmsState) -> dict[str, Any]:
    return _aggregate(state, "生產工單")


def cover_acct(state: QvDmsState) -> dict[str, Any]:
    return _aggregate(state, "會計調整")


def cover_6501(state: QvDmsState) -> dict[str, Any]:
    return _aggregate(state, "65011201")


def cover_inv(state: QvDmsState) -> dict[str, Any]:
    return _aggregate(state, "庫存調整單")


def persist(state: QvDmsState) -> dict[str, Any]:
    destination = Path(state["work_dir"]) / "Cover_updated.xlsx"
    try:
        summary = finalize_workbook(
            Path(state["input_xlsx"]), destination, state["layout"], state["stages"]
        )
    except DmsInputError as exc:
        return {"status": "failed", "error": str(exc), "output_xlsx": "", "download_url": ""}
    finally:
        for stage in state["stages"]:
            Path(stage["trace_path"]).unlink(missing_ok=True)
    comparison = {}
    if state.get("resolved_golden"):
        comparison = compare_golden(
            destination, Path(state["resolved_golden"]), state["layout"]["total_col"]
        )
    status = "warning" if summary["warning_count"] else "success"
    if comparison and not comparison["passed"]:
        status = "golden_mismatch"
    summary.update(
        {
            "period": state["layout"]["period"],
            "status": status,
            "source": state["input_xlsx"],
            "golden_comparison": comparison,
        }
    )
    summary_path = destination.with_name("validation.json")
    save_summary(summary_path, summary)
    return {
        "status": status,
        "cover_summary": summary,
        "golden_comparison": comparison,
        "output_xlsx": str(destination),
        "output_path": str(summary_path),
        "download_url": f"/qv-dms-files/{state['run_id']}/Cover_updated.xlsx",
    }


def respond(state: QvDmsState) -> dict[str, Any]:
    status = state["status"]
    if status == "failed":
        message = f"❌ 回填失敗：{state['error']}"
    elif status == "golden_mismatch":
        differences = state["golden_comparison"]["differences"]
        message = (
            f"🔎 驗收失敗：回填規則與 {state['layout']['period']} 標準答案不一致，"
            f"差異 {len(differences)} 格；未宣告驗收成功。\n"
            + "\n".join(
                f"- {d['cell']}：實算 {d['actual']}；答案 {d['expected']}；差異 {d['difference']}"
                for d in differences
            )
            + f"\n[下載對帳用活頁簿（含追溯，非已驗收報表）]({state['download_url']})"
        )
    else:
        count = state["cover_summary"]["warning_count"]
        message = (
            f"⚠️ 回填完成，但發現 {count:,} 筆資料未定義或無效，詳見追溯頁簽。"
            if status == "warning"
            else f"✅ 回填成功：{state['layout']['period']}。"
        )
        message += f"\n[下載更新後活頁簿及金額追溯明細]({state['download_url']})"
    return {"messages": [AIMessage(content=message)]}
