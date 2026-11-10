"""Rework&Dismantle risk scan — six anomaly types (no LLM).

Kept as one module so KPI thresholds and anomaly detectors share loaders;
split only if a step needs independent versioning (see .cursor/temp/open-decisions.md D2).
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import pandas as pd

from flows.domain.bom import components_for_order
from flows.domain.excel_io import ensure_string_columns, load_excel, require_columns
from flows.domain.movement_types import GOODS_ISSUE, GOODS_ISSUE_REVERSAL, GOODS_RECEIPT

# Order types (F721) — from customer KB
REWORK_TYPES = {
    "ZARW",
    "ZCPR",
    "ZMPR",
    "ZNPR",
    "ZNRW",
    "ZPRR",
    "ZSUR",
    "ZVRW",
}
DISMANTLE_TYPES = {"ZBDD", "ZMPD", "ZMPE", "ZPRD", "ZPRE"}

# KPI days: Matl group B/C → PCBA else FA
KPI_DAYS = {
    ("Normal MO", "FA"): 3.42,
    ("Normal MO", "PCBA"): 4.52,
    ("Rework MO", "FA"): 5.50,
    ("Rework MO", "PCBA"): 7.50,
    ("Dismantle MO", "FA"): 14.0,
    ("Dismantle MO", "PCBA"): 14.0,
}


@dataclass
class RdScanResult:
    order_count: int
    type_counts: dict[str, int]
    rework_count: int = 0
    dismantle_count: int = 0
    inversion_orders: list[dict[str, Any]] = field(default_factory=list)
    missrate_anomalies: list[dict[str, Any]] = field(default_factory=list)
    misuse_anomalies: list[dict[str, Any]] = field(default_factory=list)
    kpi_overdue: list[dict[str, Any]] = field(default_factory=list)
    dismantle_anomalies: list[dict[str, Any]] = field(default_factory=list)
    other_anomalies: list[dict[str, Any]] = field(default_factory=list)
    kpi: dict[str, Any] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class RdTables:
    header: pd.DataFrame
    movements: pd.DataFrame
    bom: pd.DataFrame | None
    missrate: pd.DataFrame | None


def load_rd_tables(data_dir: Path) -> RdTables:
    header_path = data_dir / "COOIS-Header.xlsx"
    mov_path = data_dir / "工单物料领用.xlsx"
    header = load_excel(header_path)
    movements = load_excel(mov_path)
    require_columns(header, ["Order"], label="COOIS-Header")
    require_columns(
        movements,
        ["Order", "Movement type", "Posting Date"],
        label="工单物料领用",
    )
    header = ensure_string_columns(
        header,
        ["Order", "Order Type", "Type", "Matl group", "System Status"],
    )
    movements = ensure_string_columns(
        movements,
        ["Order", "Material", "Movement type", "Posting Date", "Storage location"],
    )

    bom = None
    bom_path = data_dir / "Bom List.xlsx"
    if bom_path.is_file():
        bom = ensure_string_columns(
            load_excel(bom_path),
            ["Order number", "Order Number", "Component", "BOM Header"],
        )

    missrate = None
    mr_path = data_dir / "ZPP329-Missrate設定.csv"
    if mr_path.is_file():
        missrate = pd.read_csv(mr_path)
        missrate = ensure_string_columns(
            missrate,
            ["Material P/N", "Material", "Pickup miss Rate (%)"],
        )

    return RdTables(header=header, movements=movements, bom=bom, missrate=missrate)


def _type_col(header: pd.DataFrame) -> str | None:
    for c in ("Order Type", "Type", "Order type"):
        if c in header.columns:
            return c
    return None


def _order_type(header_row: pd.Series, type_col: str | None) -> str:
    if not type_col:
        return ""
    return str(header_row.get(type_col, "")).strip().upper()


def _bucket(order_type: str) -> str:
    if order_type in DISMANTLE_TYPES:
        return "Dismantle MO"
    if order_type in REWORK_TYPES:
        return "Rework MO"
    return "Normal MO"


def _pcba_or_fa(matl_group: str) -> str:
    g = str(matl_group or "").strip().upper()
    if g in {"B", "C"}:
        return "PCBA"
    return "FA"


def scan_rd_risks(tables: RdTables, *, sample_limit: int = 50) -> RdScanResult:
    type_col = _type_col(tables.header)
    orders = (
        tables.header["Order"]
        .dropna()
        .astype(str)
        .str.strip()
        .loc[lambda s: s != ""]
        .unique()
        .tolist()
    )
    type_counts: dict[str, int] = {}
    if type_col:
        vc = tables.header[type_col].astype(str).str.strip().value_counts()
        type_counts = {str(k): int(v) for k, v in vc.items()}

    rework_count = 0
    dismantle_count = 0
    header_by_order: dict[str, pd.Series] = {}
    for _, row in tables.header.iterrows():
        o = str(row["Order"]).strip()
        if not o:
            continue
        header_by_order[o] = row
        ot = _order_type(row, type_col)
        b = _bucket(ot)
        if b == "Rework MO":
            rework_count += 1
        elif b == "Dismantle MO":
            dismantle_count += 1

    inversions: list[dict[str, Any]] = []
    missrate_anoms: list[dict[str, Any]] = []
    misuse: list[dict[str, Any]] = []
    kpi_overdue: list[dict[str, Any]] = []
    dismantle_anoms: list[dict[str, Any]] = []
    other: list[dict[str, Any]] = []
    notes: list[str] = [
        f"COOIS 工單數：{len(orders)}",
        f"抽樣上限：{sample_limit}",
    ]
    if tables.bom is None:
        notes.append("缺 Bom List.xlsx — 調帳／挪用／拆解受限")
    if tables.missrate is None:
        notes.append("缺 ZPP329 — 異常調帳無法完整判斷")

    missrate_map = _missrate_map(tables.missrate)
    sample = orders[:sample_limit]

    for order in sample:
        hrow = header_by_order.get(order)
        ot = _order_type(hrow, type_col) if hrow is not None else ""
        bucket = _bucket(ot)
        mov = tables.movements[tables.movements["Order"].astype(str).str.strip() == order]

        inv = _scan_inversion(order, ot, mov)
        if inv:
            inversions.append(inv)

        if tables.bom is not None and tables.missrate is not None:
            missrate_anoms.extend(_scan_missrate(order, mov, tables.bom, missrate_map, hrow))
        elif tables.bom is not None and is_bulk_rows(mov):
            notes.append(f"{order}: 大發料存在但缺 Miss Rate（RD 不得假設 0%）")

        if bucket == "Rework MO" and tables.bom is not None:
            misuse.extend(_scan_misuse(order, ot, mov, tables.bom))

        if hrow is not None:
            kpi_row = _scan_kpi(order, ot, hrow, bucket)
            if kpi_row:
                kpi_overdue.append(kpi_row)

        if bucket == "Dismantle MO" and tables.bom is not None:
            dismantle_anoms.extend(_scan_dismantle(order, ot, mov, tables.bom))

    # RD-01: no invented "other" names
    anomalous_orders = {
        *(x["order"] for x in inversions),
        *(x["order"] for x in missrate_anoms),
        *(x["order"] for x in misuse),
        *(x["order"] for x in kpi_overdue),
        *(x["order"] for x in dismantle_anoms),
    }
    abnormal_amount = (
        sum(float(x.get("amount") or 0) for x in missrate_anoms)
        + sum(float(x.get("amount") or 0) for x in misuse)
        + sum(float(x.get("amount") or 0) for x in dismantle_anoms)
    )
    kpi = {
        "order_total": len(orders),
        "rework_count": rework_count,
        "rework_pct": round(100 * rework_count / len(orders), 2) if orders else 0,
        "dismantle_count": dismantle_count,
        "dismantle_pct": round(100 * dismantle_count / len(orders), 2) if orders else 0,
        "abnormal_order_count": len(anomalous_orders),
        "material_abnormal_amount": round(abnormal_amount, 2),
        "compliance_rate": (
            round(100 * (len(orders) - len(anomalous_orders)) / len(orders), 2) if orders else 0
        ),
    }

    return RdScanResult(
        order_count=len(orders),
        type_counts=type_counts,
        rework_count=rework_count,
        dismantle_count=dismantle_count,
        inversion_orders=inversions,
        missrate_anomalies=missrate_anoms,
        misuse_anomalies=misuse,
        kpi_overdue=kpi_overdue,
        dismantle_anomalies=dismantle_anoms,
        other_anomalies=other,
        kpi=kpi,
        notes=notes,
    )


def is_bulk_rows(mov: pd.DataFrame) -> bool:
    if "Storage location" not in mov.columns:
        return False
    for s in mov["Storage location"].dropna().astype(str):
        u = s.upper()
        if u.endswith("A") or u.endswith("B"):
            return True
    return False


def _missrate_map(df: pd.DataFrame | None) -> dict[str, float]:
    if df is None or df.empty:
        return {}
    pn = next((c for c in ("Material P/N", "Material") if c in df.columns), None)
    rate = next(
        (c for c in ("Pickup miss Rate (%)", "Miss Rate", "missrate") if c in df.columns),
        None,
    )
    if not pn or not rate:
        return {}
    out: dict[str, float] = {}
    for _, row in df.iterrows():
        key = str(row[pn]).strip()
        try:
            out[key] = float(row[rate]) / (100.0 if float(row[rate]) > 1 else 1.0)
        except (TypeError, ValueError):
            continue
    return out


def _scan_inversion(order: str, order_type: str, mov: pd.DataFrame) -> dict[str, Any] | None:
    if mov.empty:
        return None
    dates = pd.to_datetime(mov["Posting Date"], errors="coerce")
    rows = mov.assign(_dt=dates).dropna(subset=["_dt"])
    receipts = rows[rows["Movement type"].astype(str).str.strip() == GOODS_RECEIPT]
    issues = rows[rows["Movement type"].astype(str).str.strip() == GOODS_ISSUE]
    if receipts.empty or issues.empty:
        return None
    last_101 = receipts["_dt"].max()
    late = issues[issues["_dt"] > last_101]
    if late.empty:
        return None
    sample = late.iloc[0]
    return {
        "order": order,
        "order_type": order_type,
        "material": str(sample.get("Material", "")),
        "qty": sample.get("Quantity in unit of entry (ERFME)"),
        "amount": sample.get("Amt.in Loc.Cur. (WAERS)"),
        "date_101": str(last_101.date()),
        "date_261": str(sample["_dt"].date()),
    }


def _scan_missrate(
    order: str,
    mov: pd.DataFrame,
    bom: pd.DataFrame,
    missrate_map: dict[str, float],
    hrow: pd.Series | None,
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    try:
        comps = components_for_order(bom, order)
    except ValueError:
        return out
    order_qty = 1.0
    if hrow is not None:
        for c in ("Order quantity (GMEIN)", "Order quantity", "Target Qty"):
            if c in hrow.index and pd.notna(hrow[c]):
                try:
                    order_qty = float(hrow[c])
                    break
                except (TypeError, ValueError):
                    pass

    qty_col = next(
        (
            c
            for c in (
                "Quantity in unit of entry (ERFME)",
                "Quantity",
                "Qty",
            )
            if c in mov.columns
        ),
        None,
    )
    amt_col = next(
        (c for c in ("Amt.in Loc.Cur. (WAERS)", "Amount") if c in mov.columns),
        None,
    )
    # BOM qty per
    bom_qty: dict[str, float] = {}
    order_col = next(
        (c for c in ("Order number", "Order Number", "Order") if c in bom.columns),
        None,
    )
    comp_col = next((c for c in ("Component", "Material") if c in bom.columns), None)
    qty_per = next((c for c in ("Qty per", "Qty Per", "Qty") if c in bom.columns), None)
    if order_col and comp_col and qty_per:
        sub = bom[bom[order_col].astype(str).str.strip() == order]
        for _, r in sub.iterrows():
            bom_qty[str(r[comp_col]).strip()] = float(r[qty_per] or 0)

    for mt in (GOODS_ISSUE, GOODS_ISSUE_REVERSAL):
        subset = mov[mov["Movement type"].astype(str).str.strip() == mt]
        for _, row in subset.iterrows():
            storage = str(row.get("Storage location", "") or "")
            if not (storage.upper().endswith("A") or storage.upper().endswith("B")):
                continue
            mat = str(row.get("Material", "")).strip()
            if mat not in comps:
                continue
            if mat not in missrate_map:
                continue  # cannot assume 0%
            limit = bom_qty.get(mat, 0) * order_qty * (1 + missrate_map[mat])
            actual = float(row[qty_col]) if qty_col and pd.notna(row.get(qty_col)) else 0
            if actual > limit and limit >= 0:
                unit = 0.0
                if amt_col and qty_col and actual:
                    try:
                        unit = abs(float(row[amt_col]) / actual)
                    except (TypeError, ValueError, ZeroDivisionError):
                        unit = 0.0
                excess = actual - limit
                out.append(
                    {
                        "order": order,
                        "material": mat,
                        "movement_type": mt,
                        "actual_qty": actual,
                        "limit_qty": limit,
                        "excess": excess,
                        "amount": round(excess * unit, 2),
                    }
                )
    return out


def _scan_misuse(
    order: str,
    order_type: str,
    mov: pd.DataFrame,
    bom: pd.DataFrame,
) -> list[dict[str, Any]]:
    """RD-02: exclude header / single 261+101 as main materials."""
    out: list[dict[str, Any]] = []
    try:
        comps = components_for_order(bom, order)
    except ValueError:
        return out

    issues = mov[mov["Movement type"].astype(str).str.strip() == GOODS_ISSUE]
    receipts = mov[mov["Movement type"].astype(str).str.strip() == GOODS_RECEIPT]
    main: set[str] = set()
    if len(issues) == 1 and len(receipts) == 1:
        main.add(str(issues.iloc[0].get("Material", "")).strip())
        main.add(str(receipts.iloc[0].get("Material", "")).strip())

    # BOM header as main
    header_col = next((c for c in ("BOM Header",) if c in bom.columns), None)
    order_col = next(
        (c for c in ("Order number", "Order Number", "Order") if c in bom.columns),
        None,
    )
    if header_col and order_col:
        sub = bom[bom[order_col].astype(str).str.strip() == order]
        for h in sub[header_col].dropna().astype(str):
            main.add(h.strip())

    amt_col = next(
        (c for c in ("Amt.in Loc.Cur. (WAERS)", "Amount") if c in mov.columns),
        None,
    )
    for mt in (GOODS_ISSUE, GOODS_ISSUE_REVERSAL):
        subset = mov[mov["Movement type"].astype(str).str.strip() == mt]
        for _, row in subset.iterrows():
            mat = str(row.get("Material", "")).strip()
            if not mat or mat in main or mat in comps:
                continue
            amt = float(row[amt_col]) if amt_col and pd.notna(row.get(amt_col)) else 0
            out.append(
                {
                    "order": order,
                    "order_type": order_type,
                    "material": mat,
                    "description": str(row.get("Material Description", "")),
                    "amount": amt,
                    "judge": "不在Rework BOM範圍",
                }
            )
    return out


def _scan_kpi(
    order: str,
    order_type: str,
    hrow: pd.Series,
    bucket: str,
) -> dict[str, Any] | None:
    create_col = next(
        (c for c in ("Create date", "Created on", "建立日") if c in hrow.index),
        None,
    )
    close_col = next(
        (c for c in ("Close date", "Close Date", "結案日") if c in hrow.index),
        None,
    )
    if not create_col:
        return None
    create = pd.to_datetime(hrow.get(create_col), errors="coerce")
    close = pd.to_datetime(hrow.get(close_col), errors="coerce") if close_col else pd.NaT
    if pd.isna(create):
        return None
    end = close if pd.notna(close) else pd.Timestamp.now()
    days = (end - create).days
    matl = str(hrow.get("Matl group", "") or "")
    kind = _pcba_or_fa(matl)
    limit = KPI_DAYS.get((bucket, kind))
    if limit is None:
        return {
            "order": order,
            "order_type": order_type,
            "matl_group": matl,
            "actual_days": days,
            "kpi_days": None,
            "status": "KPI 未定義",
        }
    if days <= limit:
        return None
    if pd.isna(close):
        status = "尚未結案且超期"
    else:
        status = "已結案但超期"
    if "System Status" not in hrow.index:
        status = status + "（System Status 欄缺失，以 Close date 近似）"
    return {
        "order": order,
        "order_type": order_type,
        "matl_group": matl,
        "actual_days": days,
        "kpi_days": limit,
        "status": status,
    }


def _scan_dismantle(
    order: str,
    order_type: str,
    mov: pd.DataFrame,
    bom: pd.DataFrame,
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    try:
        comps = components_for_order(bom, order)
    except ValueError:
        return out
    returns = mov[mov["Movement type"].astype(str).str.strip() == "531"]
    for _, row in returns.iterrows():
        mat = str(row.get("Material", "")).strip()
        desc = str(row.get("Material Description", "") or "")
        if _is_excluded_keypart_desc(desc):
            continue
        if mat and mat not in comps:
            out.append(
                {
                    "order": order,
                    "order_type": order_type,
                    "material": mat,
                    "description": desc,
                    "remark": "拆解料號不在BOM中",
                    "amount": 0,
                }
            )
    return out


def _is_excluded_keypart_desc(desc: str) -> bool:
    lower = desc.lower()
    for token in (
        "charger",
        "bracket",
        "holder",
        "mylar",
        "socket",
        "kbc",
        "flash",
    ):
        if token in lower:
            return True
    return False
