"""Tests for qv_dms inventory (no LLM)."""

from __future__ import annotations

from pathlib import Path

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
