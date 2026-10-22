from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from flows.config.settings import get_settings
from flows.domain.qv_dms.inventory import inventory_qv_dms
from flows.graphs.qv_dms_pipeline.prompts import SYSTEM
from flows.graphs.qv_dms_pipeline.state import QvDmsState
from flows.llm.azure_apim import get_chat_model
from flows.schemas.qv_dms import PipelineAdvice


def _data_dir(state: QvDmsState) -> Path:
    if state.get("data_dir"):
        return Path(state["data_dir"])
    return get_settings().qv_dms_data_dir()


def inventory_inputs(state: QvDmsState) -> dict[str, Any]:
    data_dir = _data_dir(state)
    inv = inventory_qv_dms(data_dir).to_dict()
    msg = AIMessage(
        content=(
            f"📋 QV DMS 輸入盤點：`{data_dir}`\n"
            f"- 已找到：{', '.join(inv['present']) or '無'}\n"
            f"- 缺必要檔：{', '.join(inv['missing_required']) or '無'}\n"
            f"- 缺當期材料分析（常見）：{', '.join(inv['missing_optional']) or '無'}"
        )
    )
    return {"data_dir": str(data_dir), "inventory": inv, "messages": [msg]}


def plan_pipeline(state: QvDmsState) -> dict[str, Any]:
    inv = state.get("inventory") or inventory_qv_dms(_data_dir(state)).to_dict()
    steps = "\n".join(f"- {s}" for s in inv.get("pipeline_steps") or [])
    msg = AIMessage(content=f"🗺️ 完整流水線步驟（規格）\n{steps}")
    return {"inventory": inv, "messages": [msg]}


def narrate_status(state: QvDmsState) -> dict[str, Any]:
    inv = state.get("inventory") or {}
    model = get_chat_model(temperature=0.2)
    structured = model.with_structured_output(PipelineAdvice)
    try:
        advice: PipelineAdvice = structured.invoke(
            [
                SystemMessage(content=SYSTEM),
                HumanMessage(content=json.dumps(inv, ensure_ascii=False)),
            ]
        )
        body = (
            f"{advice.summary}\n\n"
            f"- 可開始 Cover：{'是' if advice.can_start_cover else '否'}\n"
            f"- 阻礙：{', '.join(advice.blockers) or '無'}\n"
            f"- 下一步：\n"
            + "\n".join(f"  - {a}" for a in advice.next_actions)
        )
        inv = {**inv, "llm": advice.model_dump()}
    except Exception as exc:  # noqa: BLE001
        body = f"LLM 規劃失敗：{type(exc).__name__}: {exc}"
    return {"inventory": inv, "messages": [AIMessage(content=body)]}


def persist(state: QvDmsState) -> dict[str, Any]:
    out_dir = get_settings().outputs_dir()
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "qv_dms_pipeline_mvp.json"
    path.write_text(
        json.dumps(state.get("inventory") or {}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return {
        "output_path": str(path),
        "messages": [AIMessage(content=f"✅ 已寫出：`{path}`")],
    }
