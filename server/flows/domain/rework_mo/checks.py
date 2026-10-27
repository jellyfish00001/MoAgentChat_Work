"""Six specialty checks for case 3 (and shared helpers). No LLM."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

import pandas as pd

from flows.domain.bom import components_for_order
from flows.domain.movement_types import (
    BYPRODUCT_RECEIPT,
    GOODS_ISSUE,
    GOODS_RECEIPT,
)
from flows.domain.rework_mo.classify import is_bulk_location


@dataclass
class CheckFinding:
    check: str
    material: str
    reason_code: str
    detail: str
    qv_row_hint: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class CheckResult:
    findings: list[CheckFinding] = field(default_factory=list)
    flags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "findings": [f.to_dict() for f in self.findings],
            "flags": self.flags,
        }


def _posting_dates(rows: pd.DataFrame) -> pd.Series:
    for col in ("Posting Date", "Posting date", "日期"):
        if col in rows.columns:
            return pd.to_datetime(rows[col], errors="coerce")
    return pd.Series(dtype="datetime64[ns]")


def last_101_date(mov_rows: pd.DataFrame) -> pd.Timestamp | None:
    receipts = mov_rows[
        mov_rows["Movement type"].astype(str).str.strip() == GOODS_RECEIPT
    ]
    dates = _posting_dates(receipts).dropna()
    if dates.empty:
        return None
    return dates.max()


def run_case12_cross_month(mov_rows: pd.DataFrame) -> CheckResult:
    """Case 1/2: whole-order cross-month between 261 and 101."""
    result = CheckResult()
    issues = mov_rows[mov_rows["Movement type"].astype(str).str.strip() == GOODS_ISSUE]
    receipts = mov_rows[
        mov_rows["Movement type"].astype(str).str.strip() == GOODS_RECEIPT
    ]
    i_dates = _posting_dates(issues).dropna()
    r_dates = _posting_dates(receipts).dropna()
    if i_dates.empty or r_dates.empty:
        result.flags.append("無法比較跨月（缺日期）")
        return result
    i_months = {(d.year, d.month) for d in i_dates}
    r_months = {(d.year, d.month) for d in r_dates}
    last_r = r_dates.max()
    last_month = (last_r.year, last_r.month)
    cross = any(m != last_month for m in i_months) or i_months != r_months
    code = "05.Rework MO-时间差" if cross else "未跨月，待确认"
    result.findings.append(
        CheckFinding(
            check="case12_cross_month",
            material="*",
            reason_code=code,
            detail=f"261 months={sorted(i_months)} 101 months={sorted(r_months)}",
        )
    )
    return result


def run_six_checks(
    mov_rows: pd.DataFrame,
    bom: pd.DataFrame,
    order: str,
    *,
    repair_bom: pd.DataFrame | None = None,
    material_names: pd.DataFrame | None = None,
) -> CheckResult:
    """Case 3 six specialty checks (pragmatic implementation)."""
    result = CheckResult()
    last101 = last_101_date(mov_rows)
    # include 531 in "latest move" for cross-month when present
    all_dates = _posting_dates(mov_rows).dropna()
    latest = all_dates.max() if not all_dates.empty else last101

    comps = set()
    try:
        comps = components_for_order(bom, order)
    except ValueError as exc:
        result.flags.append(f"BOM: {exc}")

    repair_comps: set[str] = set()
    if repair_bom is not None and not repair_bom.empty:
        try:
            repair_comps = components_for_order(repair_bom, order)
        except ValueError:
            # repair bom may key by machine header not order — keep empty
            pass

    dsca_map = _build_dsca_map(material_names)

    for _, row in mov_rows.iterrows():
        mt = str(row.get("Movement type", "")).strip()
        mat = str(row.get("Material", "")).strip()
        storage = str(row.get("Storage location", "") or "")
        if not mat or mt not in {GOODS_ISSUE, BYPRODUCT_RECEIPT, GOODS_RECEIPT}:
            continue
        dt_series = pd.to_datetime(pd.Series([row.get("Posting Date")]), errors="coerce")
        dt = dt_series.iloc[0] if not dt_series.empty else pd.NaT

        # 1. bulk cross-month
        if mt in {GOODS_ISSUE, BYPRODUCT_RECEIPT} and is_bulk_location(storage):
            if pd.notna(dt) and latest is not None and not pd.isna(latest):
                if (dt.year, dt.month) != (latest.year, latest.month):
                    result.findings.append(
                        CheckFinding(
                            check="cross_month_bulk",
                            material=mat,
                            reason_code="05.Rework MO-时间差",
                            detail=f"大發料跨月 storage={storage}",
                        )
                    )

        # 2. non-bulk 一領一退 (simplified: 261 without matching 531 qty/month)
        if mt == GOODS_ISSUE and not is_bulk_location(storage):
            if mat.startswith(("93", "95")):
                result.findings.append(
                    CheckFinding(
                        check="machine_layer",
                        material=mat,
                        reason_code="05.Rework MO",
                        detail="機台層不參與對沖",
                    )
                )
            else:
                matched = _find_matching_531(mov_rows, mat, dsca_map)
                if matched is None:
                    result.findings.append(
                        CheckFinding(
                            check="one_issue_one_return",
                            material=mat,
                            reason_code="05.Rework MO-跨月退料",
                            detail="找不到對應 531 對沖（含 DSCA）",
                        )
                    )
                else:
                    result.findings.append(
                        CheckFinding(
                            check="one_issue_one_return",
                            material=mat,
                            reason_code="05.Rework MO",
                            detail="找到 531 對沖",
                        )
                    )

        # 3. missrate — *A = 0; *B without ZPP329 → flag only (RM-03)
        if mt == GOODS_ISSUE and is_bulk_location(storage):
            if storage.upper().endswith("B"):
                result.flags.append(f"RM-03：{mat} 庫位*B 缺 ZPP329，未算超標金額")
            # *A: missrate 0 — qty vs BOM deferred to amount phase; flag presence
            if mat and comps and mat not in comps:
                result.findings.append(
                    CheckFinding(
                        check="missrate_bom_presence",
                        material=mat,
                        reason_code="",
                        detail="大發料不在 BOM Component（金額超標待補 Qty）",
                    )
                )

        # 4. BOM compliance
        if mt == GOODS_ISSUE and comps and mat not in comps:
            result.findings.append(
                CheckFinding(
                    check="bom_compliance",
                    material=mat,
                    reason_code="",
                    detail="261 不在表 B Component",
                )
            )
        if mt == BYPRODUCT_RECEIPT:
            target = repair_comps or comps
            if target and mat not in target:
                result.findings.append(
                    CheckFinding(
                        check="bom_compliance",
                        material=mat,
                        reason_code="",
                        detail="531 不在维修261Bom／表 B",
                    )
                )

        # 5. inversion: 261/531 after last 101
        if mt in {GOODS_ISSUE, BYPRODUCT_RECEIPT} and last101 is not None and pd.notna(dt):
            if dt > last101:
                result.findings.append(
                    CheckFinding(
                        check="inversion",
                        material=mat,
                        reason_code="",
                        detail=f"{mt} 晚於最後 101 ({last101.date()})",
                    )
                )

    # 6. diversion risk flag if many BOM misses
    bom_misses = [f for f in result.findings if f.check == "bom_compliance"]
    if len(bom_misses) >= 2:
        result.flags.append("挪料風險：多筆發退料不在 BOM，需人工複核")

    return result


def _build_dsca_map(material_names: pd.DataFrame | None) -> dict[str, str]:
    if material_names is None or material_names.empty:
        return {}
    item_col = next(
        (c for c in ("ITEM", "Item", "Material") if c in material_names.columns),
        None,
    )
    dsca_col = next(
        (c for c in ("DSCA", "Material Description") if c in material_names.columns),
        None,
    )
    if not item_col or not dsca_col:
        return {}
    out: dict[str, str] = {}
    for _, row in material_names.iterrows():
        item = str(row[item_col]).strip()
        dsca = str(row[dsca_col]).strip()
        if item:
            out[item] = dsca
    return out


def _find_matching_531(
    mov_rows: pd.DataFrame,
    material: str,
    dsca_map: dict[str, str],
) -> pd.Series | None:
    returns = mov_rows[
        mov_rows["Movement type"].astype(str).str.strip() == BYPRODUCT_RECEIPT
    ]
    if returns.empty:
        return None
    exact = returns[returns["Material"].astype(str).str.strip() == material]
    if not exact.empty:
        return exact.iloc[0]
    target_dsca = dsca_map.get(material, "")
    if not target_dsca:
        return None
    for _, row in returns.iterrows():
        m = str(row.get("Material", "")).strip()
        if dsca_map.get(m) == target_dsca:
            return row
    return None
