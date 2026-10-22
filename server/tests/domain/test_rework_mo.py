"""Tests for rework_mo domain rules (no LLM)."""

from __future__ import annotations

from pathlib import Path

from flows.domain.rework_mo.analyze import (
    analyze_order,
    list_unique_orders,
    load_rework_mo_tables,
)


def test_load_and_list_orders(rework_mo_dir: Path) -> None:
    tables = load_rework_mo_tables(rework_mo_dir)
    orders = list_unique_orders(tables.qv)
    assert isinstance(orders, list)
    assert len(orders) >= 1


def test_analyze_first_order(rework_mo_dir: Path) -> None:
    tables = load_rework_mo_tables(rework_mo_dir)
    orders = list_unique_orders(tables.qv)
    result = analyze_order(tables, orders[0])
    assert result.order_number == orders[0]
    assert result.case_type
    assert isinstance(result.suggested_reason, str)
