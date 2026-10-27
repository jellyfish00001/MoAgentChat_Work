"""Tests for rd_risk domain rules (no LLM)."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from flows.domain.rd_risk.html_report import render_rd_dashboard
from flows.domain.rd_risk.scan import RdTables, load_rd_tables, scan_rd_risks


def test_load_and_scan(rd_risk_dir: Path) -> None:
    tables = load_rd_tables(rd_risk_dir)
    assert tables.bom is not None
    assert tables.missrate is not None
    result = scan_rd_risks(tables, sample_limit=10)
    assert result.order_count >= 1
    assert isinstance(result.inversion_orders, list)
    assert "order_total" in result.kpi
    assert isinstance(result.missrate_anomalies, list)
    assert isinstance(result.kpi_overdue, list)


def test_render_html_smoke(rd_risk_dir: Path) -> None:
    tables = load_rd_tables(rd_risk_dir)
    result = scan_rd_risks(tables, sample_limit=5)
    html = render_rd_dashboard(result.to_dict(), narrative={"headline": "T", "risks": ["a"], "actions": ["b"]})
    assert "工單總數" in html
    assert "流程倒置" in html


def test_load_missing_order_column_fails(rd_risk_dir: Path) -> None:
    tables = load_rd_tables(rd_risk_dir)
    bad = RdTables(
        header=pd.DataFrame({"Nope": [1]}),
        movements=tables.movements,
        bom=tables.bom,
        missrate=tables.missrate,
    )
    with pytest.raises(ValueError, match="missing columns"):
        from flows.domain.excel_io import require_columns

        require_columns(bad.header, ["Order"], label="COOIS-Header")
