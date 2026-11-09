"""Rework MO detective — orchestrate classify / checks / row reasons (no LLM)."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

import pandas as pd

from flows.domain.movement_types import GOODS_ISSUE, GOODS_RECEIPT
from flows.domain.rework_mo.checks import CheckResult, run_case12_cross_month, run_six_checks
from flows.domain.rework_mo.classify import CaseType, classify_case, materials_by_type
from flows.domain.rework_mo.tables import ReworkMoTables, list_unique_orders, load_rework_mo_tables

# re-exports for tests / package
__all__ = [
    "CaseType",
    "OrderAnalysis",
    "analyze_order",
    "apply_reasons_to_qv",
    "list_unique_orders",
    "load_rework_mo_tables",
    "ReworkMoTables",
]


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
    checks: dict[str, Any] = field(default_factory=dict)
    row_reasons: list[dict[str, str]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["case_type"] = self.case_type.value
        return data


def analyze_order(tables: ReworkMoTables, order_number: str) -> OrderAnalysis:
    order = str(order_number).strip()
    qv_rows = tables.qv[tables.qv["Order Number"].astype(str).str.strip() == order]
    mov_col = "Order" if "Order" in tables.movements.columns else "Order Number"
    mov_rows = tables.movements[tables.movements[mov_col].astype(str).str.strip() == order].copy()

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

    mt_list = sorted(
        {
            str(x).strip()
            for x in mov_rows.get("Movement type", pd.Series(dtype=str)).dropna().tolist()
            if str(x).strip()
        }
    )

    case, case_notes = classify_case(mov_rows)
    notes = list(case_notes)

    if case in (CaseType.CASE_1_SAME_MATERIAL, CaseType.CASE_2_SUBSTITUTE):
        check_result = run_case12_cross_month(mov_rows)
    else:
        check_result = run_six_checks(
            mov_rows,
            tables.bom,
            order,
            repair_bom=tables.repair_bom,
            material_names=tables.material_names,
        )

    notes.extend(check_result.flags)
    suggested, row_reasons, cross = _derive_reasons(case, check_result, qv_rows, mov_rows)
    bom_missing = [
        f.material for f in check_result.findings if f.check == "bom_compliance" and f.material
    ]

    return OrderAnalysis(
        order_number=order,
        header_material=header,
        case_type=case,
        materials=materials,
        movement_types=mt_list,
        cross_month=cross,
        bom_missing_materials=sorted(set(bom_missing)),
        notes=notes,
        suggested_reason=suggested,
        checks=check_result.to_dict(),
        row_reasons=row_reasons,
    )


def apply_reasons_to_qv(
    qv: pd.DataFrame,
    analyses: list[dict[str, Any]],
) -> pd.DataFrame:
    """Apply row-level / order-level reasons onto a QV copy (program owns Reason)."""
    out = qv.copy()
    if "Reason" not in out.columns:
        out["Reason"] = ""
    out["Reason"] = out["Reason"].astype(str)

    for item in analyses:
        order = str(item.get("order_number", "")).strip()
        if not order:
            continue
        mask = out["Order Number"].astype(str).str.strip() == order
        row_reasons: list[dict[str, str]] = item.get("row_reasons") or []
        if row_reasons:
            for rr in row_reasons:
                mat = str(rr.get("material", "")).strip()
                code = str(rr.get("reason_code", "")).strip()
                if not code:
                    continue
                if mat and mat != "*" and "Material" in out.columns:
                    m2 = mask & (out["Material"].astype(str).str.strip() == mat)
                    out.loc[m2, "Reason"] = code
                else:
                    out.loc[mask, "Reason"] = code
        else:
            code = str(item.get("suggested_reason", "")).strip()
            if code:
                out.loc[mask, "Reason"] = code
    return out


def _derive_reasons(
    case: CaseType,
    check_result: CheckResult,
    qv_rows: pd.DataFrame,
    mov_rows: pd.DataFrame,
) -> tuple[str, list[dict[str, str]], bool]:
    row_reasons: list[dict[str, str]] = []
    cross = False

    if case in (CaseType.CASE_1_SAME_MATERIAL, CaseType.CASE_2_SUBSTITUTE):
        code = "未跨月，待确认"
        for f in check_result.findings:
            if f.reason_code:
                code = f.reason_code
                cross = "时间差" in code or "時間差" in code
        # mark all issue/receipt related qv rows
        mats = materials_by_type(mov_rows, GOODS_ISSUE) | materials_by_type(mov_rows, GOODS_RECEIPT)
        if not mats:
            row_reasons.append({"material": "*", "reason_code": code})
        else:
            for m in mats:
                row_reasons.append({"material": m, "reason_code": code})
        return code, row_reasons, cross

    # case 3: prefer finding reason codes; default Rework MO
    codes = [f.reason_code for f in check_result.findings if f.reason_code]
    for f in check_result.findings:
        if f.reason_code:
            row_reasons.append({"material": f.material, "reason_code": f.reason_code})
            if "时间差" in f.reason_code or "時間差" in f.reason_code:
                cross = True
    suggested = codes[0] if codes else "05.Rework MO"
    if not row_reasons:
        row_reasons.append({"material": "*", "reason_code": suggested})
    return suggested, row_reasons, cross
