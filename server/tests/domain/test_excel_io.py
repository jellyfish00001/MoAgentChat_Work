"""Tests for flows.domain.excel_io."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from flows.domain.excel_io import load_excel, require_columns


def test_load_excel_missing_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_excel(tmp_path / "nope.xlsx")


def test_require_columns_ok() -> None:
    df = pd.DataFrame({"Order": [1], "Qty": [2]})
    require_columns(df, ["Order"], label="demo")


def test_require_columns_missing() -> None:
    df = pd.DataFrame({"Qty": [2]})
    with pytest.raises(ValueError, match="missing columns"):
        require_columns(df, ["Order"], label="demo")
