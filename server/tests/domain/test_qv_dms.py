"""Tests for qv_dms inventory + cover pipeline (no LLM)."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from flows.domain.qv_dms.cover import (
    build_material_pivot,
    match_and_fill_pcl500,
    run_cover_pipeline,
)
from flows.domain.qv_dms.inventory import REQUIRED_FILES, inventory_qv_dms


def test_inventory_required_present(qv_dms_dir: Path) -> None:
    inv = inventory_qv_dms(qv_dms_dir)
    assert inv.missing_required == []
    for name in REQUIRED_FILES:
        assert name in inv.present
    assert len(inv.pipeline_steps) >= 5


def test_inventory_missing_dir(tmp_path: Path) -> None:
    inv = inventory_qv_dms(tmp_path)
    assert set(inv.missing_required) == set(REQUIRED_FILES)
    assert inv.present == []


def test_cover_pipeline_runs(qv_dms_dir: Path) -> None:
    result = run_cover_pipeline(qv_dms_dir)
    assert "1.2_production_mo" in result.steps_done
    assert result.cover is not None
    assert len(result.cover) >= 1
    assert result.notes  # QV-02 skip note and/or step notes


def test_pivot_match_unit() -> None:
    material = pd.DataFrame(
        {
            "Reason": ["05.Rework MO-时间差", "Bom error"],
            "QV in Material(LC)": [10.0, -5.0],
        }
    )
    pivot = build_material_pivot(material)
    assert "時間差" in set(pivot["Reason"]) or any("時間" in str(r) for r in pivot["Reason"])
    cover = pd.DataFrame(
        {
            "Reason Code": ["時間差", "Bom error", "未分析"],
            "PCL500": [0, 0, 0],
        }
    )
    out, filled, unmatched, _ok = match_and_fill_pcl500(cover, pivot)
    assert filled >= 1
    assert float(out.loc[out["Reason Code"] == "Bom error", "PCL500"].iloc[0]) == -5.0
