"""Rework&Dismantle risk scan — pure rules (MVP skeleton)."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import pandas as pd

from flows.domain.excel_io import ensure_string_columns, load_excel, require_columns
from flows.domain.movement_types import GOODS_ISSUE, GOODS_RECEIPT


@dataclass
class RdScanResult:
    order_count: int
    type_counts: dict[str, int]
    inversion_orders: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    todo_checks: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class RdTables:
    header: pd.DataFrame
    movements: pd.DataFrame


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
    header = ensure_string_columns(header, ["Order", "Order Type", "Type"])
    movements = ensure_string_columns(
        movements,
        ["Order", "Movement type", "Posting Date"],
    )
    return RdTables(header=header, movements=movements)


def scan_rd_risks(tables: RdTables, *, sample_limit: int = 50) -> RdScanResult:
    order_col = "Order"
    type_col = None
    for c in ("Order Type", "Type", "Order type"):
        if c in tables.header.columns:
            type_col = c
            break

    orders = (
        tables.header[order_col]
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

    inversions: list[str] = []
    mov = tables.movements
    mov_order = "Order"
    mt_col = "Movement type"
    date_col = "Posting Date"

    for order in orders[:sample_limit]:
        rows = mov[mov[mov_order].astype(str).str.strip() == order]
        if rows.empty:
            continue
        dates = pd.to_datetime(rows[date_col], errors="coerce")
        rows = rows.assign(_dt=dates).dropna(subset=["_dt"])
        receipts = rows[rows[mt_col].astype(str).str.strip() == GOODS_RECEIPT]
        issues = rows[rows[mt_col].astype(str).str.strip() == GOODS_ISSUE]
        if receipts.empty or issues.empty:
            continue
        last_101 = receipts["_dt"].max()
        late_261 = issues[issues["_dt"] > last_101]
        if not late_261.empty:
            inversions.append(order)

    notes = [
        f"COOIS 工單數：{len(orders)}",
        f"抽樣檢查流程倒置：前 {min(sample_limit, len(orders))} 筆，命中 {len(inversions)}",
    ]
    todos = [
        "異常調帳（Missrate / ZPP329）",
        "物料挪用（主料語意 + BOM）",
        "超期 KPI Days",
        "拆解異常",
        "其他具名異常",
        "對齊完整看板（後續）",
    ]
    return RdScanResult(
        order_count=len(orders),
        type_counts=type_counts,
        inversion_orders=inversions,
        notes=notes,
        todo_checks=todos,
    )
