"""Shared graph path helpers (no LLM, no domain rules)."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any, Mapping


def resolve_data_dir(
    state: Mapping[str, Any],
    default_dir: Callable[[], Path],
) -> Path:
    """Prefer thread/state override so smokes can point at fixtures without settings edits."""
    raw = state.get("data_dir")
    if raw:
        return Path(str(raw))
    return default_dir()
