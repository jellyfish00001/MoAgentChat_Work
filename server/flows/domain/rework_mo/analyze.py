"""Rework MO detective — pure rule engine (MVP skeleton)."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any

import pandas as pd

from flows.domain.bom import components_for_order, material_in_bom
from flows.domain.excel_io import ensure_string_columns, load_excel, require_columns
from flows.domain.movement_types import BYPRODUCT_RECEIPT, GOODS_ISSUE, GOODS_RECEIPT


class CaseType(StrEnum):
    CASE_1_SAME_MATERIAL = "情形一_A到A"
    CASE_2_SUBSTITUTE = "情形二_A到B"
    CASE_3_MULTI_OR_531 = "情形三_多物料或531"
    UNKNOWN = "未分類"


@dataclass
class OrderAnalysis:
    order_number: str
    header_material: str | None
    case_type: CaseType
    materials: list[str] = field(default_factory=list)
    movement_types: list[str] = field(default_factory=list)
    cross_month: bool = False
    bom_missing_materials: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    suggested_reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["case_type"] = self.case_type.value
        return data


@dataclass
class ReworkMoTables:
    qv: pd.DataFrame
    bom: pd.DataFrame
    movements: pd.DataFrame


def load_rework_mo_tables(data_dir: Path) -> ReworkMoTables:
    qv_path = _find_file(data_dir, ["QV_Report-Material.xlsx", "QV_Report-material.xlsx"])
    bom_path = _find_file(data_dir, ["Bom List.xlsx"])
    mov_path = _find_file(data_dir, ["工单物料领用.xlsx"])

    qv = load_excel(qv_path)
    bom = load_excel(bom_path)
    movements = load_excel(mov_path)

    qv = ensure_string_columns(qv, ["Order Number", "Material", "Material Number For Order"])
    bom = ensure_string_columns(bom, ["Order number", "Order Number", "Component"])
    movements = ensure_string_columns(
        movements,
        ["Order", "Material", "Movement type", "Posting Date"],
    )

    require_columns(qv, ["Order Number"], label="QV_Report")
    return ReworkMoTables(qv=qv, bom=bom, movements=movements)


def list_unique_orders(qv: pd.DataFrame) -> list[str]:
    require_columns(qv, ["Order Number"], label="QV_Report")
    orders = (
        qv["Order Number"]
        .dropna()
        .astype(str)
        .str.strip()
        .loc[lambda s: s != ""]
        .unique()
        .tolist()
    )
    return sorted(orders)


def analyze_order(tables: ReworkMoTables, order_number: str) -> OrderAnalysis:
    order = str(order_number).strip()
    qv_rows = tables.qv[tables.qv["Order Number"].astype(str).str.strip() == order]
    mov_col_order = "Order" if "Order" in tables.movements.columns else "Order Number"
    mov_rows = tables.movements[
        tables.movements[mov_col_order].astype(str).str.strip() == order
    ]

    materials = sorted(
        {
            str(m).strip()
            for m in qv_rows.get("Material", pd.Series(dtype=str)).dropna().tolist()
            if str(m).strip()
        }
    )
    header = None
    if "Material Number For Order" in qv_rows.columns and not qv_rows.empty:
        header = str(qv_rows["Material Number For Order"].iloc[0]).strip() or None

    mt_col = "Movement type" if "Movement type" in mov_rows.columns else None
    movement_types: list[str] = []
    if mt_col is not None:
        movement_types = sorted(
            {str(x).strip() for x in mov_rows[mt_col].dropna().tolist() if str(x).strip()}
        )

    case = _classify_case(materials, movement_types)
    cross_month = _detect_cross_month(mov_rows)
    bom_missing = _bom_missing(tables.bom, order, materials, header)

    notes: list[str] = []
    if cross_month:
        notes.append("偵測到可能跨月投退料（不同月份 Posting Date）")
    if bom_missing:
        notes.append(f"BOM 找不到料號: {', '.join(bom_missing)}")
    if BYPRODUCT_RECEIPT in movement_types:
        notes.append("含 531 副產品／換下件入庫")

    suggested = _suggest_reason(case, cross_month, bom_missing, movement_types)

    return OrderAnalysis(
        order_number=order,
        header_material=header,
        case_type=case,
        materials=materials,
        movement_types=movement_types,
        cross_month=cross_month,
        bom_missing_materials=bom_missing,
        notes=notes,
        suggested_reason=suggested,
    )


def _classify_case(materials: list[str], movement_types: list[str]) -> CaseType:
    if BYPRODUCT_RECEIPT in movement_types or len(materials) > 2:
        return CaseType.CASE_3_MULTI_OR_531
    if len(materials) <= 1:
        # A→A style when issue/receipt focus on same material set
        if set(movement_types) <= {GOODS_ISSUE, GOODS_RECEIPT, ""} or not movement_types:
            return CaseType.CASE_1_SAME_MATERIAL
        return CaseType.CASE_1_SAME_MATERIAL
    if len(materials) == 2:
        return CaseType.CASE_2_SUBSTITUTE
    return CaseType.UNKNOWN


def _detect_cross_month(mov_rows: pd.DataFrame) -> bool:
    date_col = None
    for candidate in ("Posting Date", "Posting date", "日期"):
        if candidate in mov_rows.columns:
            date_col = candidate
            break
    if date_col is None or mov_rows.empty:
        return False
    dates = pd.to_datetime(mov_rows[date_col], errors="coerce").dropna()
    if dates.empty:
        return False
    months = {(d.year, d.month) for d in dates}
    return len(months) > 1


def _bom_missing(
    bom_df: pd.DataFrame,
    order: str,
    materials: list[str],
    header: str | None,
) -> list[str]:
    # Fail loudly if BOM columns are missing (require_columns / components_for_order).
    comps = components_for_order(bom_df, order)
    missing: list[str] = []
    for mat in materials:
        if header and mat == header:
            continue
        if not material_in_bom(bom_df, order, mat) and mat not in comps:
            missing.append(mat)
    return missing


def _suggest_reason(
    case: CaseType,
    cross_month: bool,
    bom_missing: list[str],
    movement_types: list[str],
) -> str:
    parts: list[str] = []
    if cross_month:
        parts.append("跨月投料/時間差")
    if case == CaseType.CASE_2_SUBSTITUTE:
        parts.append("替代料")
    elif case == CaseType.CASE_1_SAME_MATERIAL:
        parts.append("Rework MO-時間差")
    elif case == CaseType.CASE_3_MULTI_OR_531:
        parts.append("Rework MO-多物料/531")
    if bom_missing:
        parts.append("BOM 差異")
    if BYPRODUCT_RECEIPT in movement_types and "531" not in "".join(parts):
        parts.append("531未退庫風險")
    return "；".join(parts) if parts else "Rework MO-待人工確認"


def _find_file(data_dir: Path, names: list[str]) -> Path:
    for name in names:
        path = data_dir / name
        if path.is_file():
            return path
    raise FileNotFoundError(f"None of {names} found under {data_dir}")
