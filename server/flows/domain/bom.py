"""BOM existence helpers (no LLM)."""

from __future__ import annotations

import pandas as pd


def components_for_order(bom_df: pd.DataFrame, order_number: str) -> set[str]:
    order_col = _first_existing(bom_df, ["Order number", "Order Number", "Order"])
    component_col = _first_existing(bom_df, ["Component", "Material"])
    subset = bom_df[bom_df[order_col].astype(str).str.strip() == str(order_number).strip()]
    return {str(x).strip() for x in subset[component_col].dropna().tolist()}


def material_in_bom(bom_df: pd.DataFrame, order_number: str, material: str) -> bool:
    return str(material).strip() in components_for_order(bom_df, order_number)


def _first_existing(df: pd.DataFrame, candidates: list[str]) -> str:
    for name in candidates:
        if name in df.columns:
            return name
    raise ValueError(f"None of columns found: {candidates}; have={list(df.columns)}")
