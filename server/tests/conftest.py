"""Shared pytest fixtures — domain tests never call the LLM."""

from __future__ import annotations

from pathlib import Path

import pytest

SERVER_ROOT = Path(__file__).resolve().parents[1]
TESTDATA = SERVER_ROOT / "testdata"


@pytest.fixture(scope="session")
def testdata_root() -> Path:
    assert TESTDATA.is_dir(), f"missing testdata: {TESTDATA}"
    return TESTDATA


@pytest.fixture(scope="session")
def rework_mo_dir(testdata_root: Path) -> Path:
    path = testdata_root / "rework_mo"
    assert path.is_dir()
    return path


@pytest.fixture(scope="session")
def rd_risk_dir(testdata_root: Path) -> Path:
    path = testdata_root / "rd_risk"
    assert path.is_dir()
    return path


@pytest.fixture(scope="session")
def qv_dms_dir(testdata_root: Path) -> Path:
    path = testdata_root / "qv_dms"
    assert path.is_dir()
    return path
