"""Load Rework MO Excel tables (no LLM)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from flows.domain.excel_io import ensure_string_columns, load_excel, require_columns


@dataclass
class ReworkMoTables:
    qv: pd.DataFrame
    bom: pd.DataFrame
    movements: pd.DataFrame
    material_names: pd.DataFrame | None
    repair_bom: pd.DataFrame | None
    qv_path: Path
    data_dir: Path


def load_rework_mo_tables(data_dir: Path) -> ReworkMoTables:
    qv_path = _find_file(data_dir, ["QV_Report-Material.xlsx", "QV_Report-material.xlsx"])
    bom_path = _find_file(data_dir, ["Bom List.xlsx"])
    mov_path = _find_file(data_dir, ["工单物料领用.xlsx"])

    qv = load_excel(qv_path)
    bom = load_excel(bom_path)
    movements = load_excel(mov_path)

    qv = ensure_string_columns(
        qv,
        ["Order Number", "Material", "Material Number For Order", "Reason"],
    )
    bom = ensure_string_columns(bom, ["Order number", "Order Number", "Component"])
    movements = ensure_string_columns(
        movements,
        ["Order", "Material", "Movement type", "Posting Date", "Storage location"],
    )
    require_columns(qv, ["Order Number"], label="QV_Report")

    names_path = data_dir / "物料名称.xlsx"
    repair_path = data_dir / "维修261Bom List.xlsx"
    material_names = None
    repair_bom = None
    if names_path.is_file():
        material_names = ensure_string_columns(
            load_excel(names_path),
            ["ITEM", "Item", "Material", "DSCA", "Material Description"],
        )
    if repair_path.is_file():
        repair_bom = ensure_string_columns(
            load_excel(repair_path),
            ["Order number", "Order Number", "Component", "BOM Header"],
        )

    return ReworkMoTables(
        qv=qv,
        bom=bom,
        movements=movements,
        material_names=material_names,
        repair_bom=repair_bom,
        qv_path=qv_path,
        data_dir=data_dir,
    )


def list_unique_orders(qv: pd.DataFrame) -> list[str]:
    require_columns(qv, ["Order Number"], label="QV_Report")
    orders = (
        qv["Order Number"].dropna().astype(str).str.strip().loc[lambda s: s != ""].unique().tolist()
    )
    return sorted(orders)


def _find_file(data_dir: Path, names: list[str]) -> Path:
    for name in names:
        path = data_dir / name
        if path.is_file():
            return path
    raise FileNotFoundError(f"None of {names} found under {data_dir}")
