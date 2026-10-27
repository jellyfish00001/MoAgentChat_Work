"""Case classification for Rework MO (no LLM)."""

from __future__ import annotations

from enum import StrEnum

import pandas as pd

from flows.domain.movement_types import BYPRODUCT_RECEIPT, GOODS_ISSUE, GOODS_RECEIPT


class CaseType(StrEnum):
    CASE_1_SAME_MATERIAL = "情形一_A到A"
    CASE_2_SUBSTITUTE = "情形二_A到B"
    CASE_3_MULTI_OR_531 = "情形三_多物料或531"
    UNKNOWN = "未分類"


def movement_types_for_order(mov_rows: pd.DataFrame) -> set[str]:
    if mov_rows.empty or "Movement type" not in mov_rows.columns:
        return set()
    return {
        str(x).strip()
        for x in mov_rows["Movement type"].dropna().tolist()
        if str(x).strip()
    }


def materials_by_type(mov_rows: pd.DataFrame, mt: str) -> set[str]:
    if mov_rows.empty:
        return set()
    mt_col = "Movement type"
    mat_col = "Material" if "Material" in mov_rows.columns else None
    if mat_col is None:
        return set()
    subset = mov_rows[mov_rows[mt_col].astype(str).str.strip() == mt]
    return {
        str(m).strip()
        for m in subset[mat_col].dropna().tolist()
        if str(m).strip()
    }


def classify_case(mov_rows: pd.DataFrame) -> tuple[CaseType, list[str]]:
    """Return case type and notes (RM-01: substitute relation not verified)."""
    notes: list[str] = []
    types = movement_types_for_order(mov_rows)
    if not types:
        return CaseType.UNKNOWN, ["表 C 無移動類型"]

    if BYPRODUCT_RECEIPT in types or len(materials_by_type(mov_rows, GOODS_ISSUE)) >= 2:
        return CaseType.CASE_3_MULTI_OR_531, notes

    only_gi_gr = types <= {GOODS_ISSUE, GOODS_RECEIPT}
    if not only_gi_gr:
        # other movement types → case 3
        return CaseType.CASE_3_MULTI_OR_531, notes

    issue_mats = materials_by_type(mov_rows, GOODS_ISSUE)
    receipt_mats = materials_by_type(mov_rows, GOODS_RECEIPT)

    if not issue_mats or not receipt_mats:
        return CaseType.UNKNOWN, ["缺少 261 或 101 物料"]

    if issue_mats == receipt_mats and len(issue_mats) == 1:
        return CaseType.CASE_1_SAME_MATERIAL, notes

    if issue_mats != receipt_mats:
        notes.append("RM-01：替代關係未以 BOM Alt 驗證，僅依料號不同判情形二")
        return CaseType.CASE_2_SUBSTITUTE, notes

    return CaseType.CASE_3_MULTI_OR_531, notes


def is_bulk_location(storage: str) -> bool:
    s = str(storage or "").upper()
    return s.endswith("A") or s.endswith("B") or "*A" in s or "*B" in s
