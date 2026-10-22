"""Tests for rd_risk domain rules (no LLM)."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from flows.domain.rd_risk.scan import RdTables, load_rd_tables, scan_rd_risks


def test_load_and_scan(rd_risk_dir: Path) -> None:
    tables = load_rd_tables(rd_risk_dir)
    result = scan_rd_risks(tables, sample_limit=10)
    assert result.order_count >= 1
    assert isinstance(result.inversion_orders, list)
    assert result.todo_checks


def test_load_missing_order_column_fails(rd_risk_dir: Path) -> None:
    tables = load_rd_tables(rd_risk_dir)
    bad = RdTables(
        header=pd.DataFrame({"Nope": [1]}),
        movements=tables.movements,
    )
    # scan assumes require_columns already ran; load path is what we protect
    with pytest.raises(ValueError, match="missing columns"):
        from flows.domain.excel_io import require_columns

        require_columns(bad.header, ["Order"], label="COOIS-Header")
