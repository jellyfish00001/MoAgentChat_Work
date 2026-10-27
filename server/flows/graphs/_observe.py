"""Shared helpers for observable graph node messages (no LLM)."""

from __future__ import annotations

import json
from typing import Any

from langchain_core.messages import AIMessage


def node_message(
    *,
    node: str,
    kind: str,
    inputs: dict[str, Any] | None = None,
    outputs: dict[str, Any] | None = None,
    note: str = "",
) -> AIMessage:
    """Build a readable I/O summary for LangGraph / LangSmith."""
    payload = {
        "node": node,
        "kind": kind,  # "program" | "llm"
        "inputs": inputs or {},
        "outputs": outputs or {},
    }
    body = json.dumps(payload, ensure_ascii=False, indent=2, default=str)
    if len(body) > 4000:
        body = body[:4000] + "\n…(truncated)"
    header = f"[{kind}] `{node}`"
    if note:
        header = f"{header} — {note}"
    return AIMessage(content=f"{header}\n```json\n{body}\n```")


def preview_list(items: list[Any], *, limit: int = 20) -> list[Any]:
    return items[:limit]
