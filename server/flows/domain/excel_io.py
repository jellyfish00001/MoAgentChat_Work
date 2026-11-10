"""Excel loading helpers (no LLM)."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


def load_excel(path: Path, *, sheet_name: str | int = 0) -> pd.DataFrame:
    if not path.is_file():
        raise FileNotFoundError(f"Excel not found: {path}")
    return pd.read_excel(path, sheet_name=sheet_name, engine="openpyxl")


def ensure_string_columns(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    out = df.copy()
    for col in columns:
        if col in out.columns:
            out[col] = out[col].astype(str).str.strip()
    return out


def require_columns(df: pd.DataFrame, required: list[str], *, label: str) -> None:
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"{label} missing columns: {missing}; have={list(df.columns)}")
