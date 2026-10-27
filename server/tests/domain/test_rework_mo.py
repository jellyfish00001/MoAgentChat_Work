"""Tests for rework_mo domain rules (no LLM)."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from flows.domain.rework_mo.analyze import (
    analyze_order,
    apply_reasons_to_qv,
    list_unique_orders,
    load_rework_mo_tables,
)
from flows.domain.rework_mo.classify import CaseType, classify_case
from flows.domain.movement_types import GOODS_ISSUE, GOODS_RECEIPT


def test_load_and_list_orders(rework_mo_dir: Path) -> None:
    tables = load_rework_mo_tables(rework_mo_dir)
    orders = list_unique_orders(tables.qv)
    assert isinstance(orders, list)
    assert len(orders) >= 1
    assert tables.material_names is not None
    assert tables.repair_bom is not None


def test_analyze_first_order(rework_mo_dir: Path) -> None:
    tables = load_rework_mo_tables(rework_mo_dir)
    orders = list_unique_orders(tables.qv)
    result = analyze_order(tables, orders[0])
    assert result.order_number == orders[0]
    assert result.case_type
    assert isinstance(result.suggested_reason, str)
    assert "findings" in result.checks
    assert result.row_reasons


def test_classify_case1_same_material() -> None:
    mov = pd.DataFrame(
        {
            "Movement type": [GOODS_ISSUE, GOODS_RECEIPT],
            "Material": ["A1", "A1"],
            "Posting Date": ["2026-01-05", "2026-02-01"],
            "Storage location": ["W10C", "W10C"],
        }
    )
    case, _ = classify_case(mov)
    assert case == CaseType.CASE_1_SAME_MATERIAL


def test_classify_case2_different_material() -> None:
    mov = pd.DataFrame(
        {
            "Movement type": [GOODS_ISSUE, GOODS_RECEIPT],
            "Material": ["A1", "B2"],
            "Posting Date": ["2026-01-05", "2026-01-10"],
            "Storage location": ["W10C", "W10C"],
        }
    )
    case, notes = classify_case(mov)
    assert case == CaseType.CASE_2_SUBSTITUTE
    assert any("RM-01" in n for n in notes)


def test_apply_reasons_to_qv(rework_mo_dir: Path) -> None:
    tables = load_rework_mo_tables(rework_mo_dir)
    orders = list_unique_orders(tables.qv)
    analysis = analyze_order(tables, orders[0]).to_dict()
    out = apply_reasons_to_qv(tables.qv, [analysis])
    assert "Reason" in out.columns
    mask = out["Order Number"].astype(str).str.strip() == orders[0]
    assert mask.any()
