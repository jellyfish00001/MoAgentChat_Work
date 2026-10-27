"""Graph state for Rework MO detective (agent-chat compatible)."""

from __future__ import annotations

from typing import Annotated, Any, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class DetectiveState(TypedDict, total=False):
    messages: Annotated[list[BaseMessage], add_messages]
    data_dir: str
    orders: list[str]
    classifications: list[dict[str, Any]]
    analyses: list[dict[str, Any]]
    narratives: list[str]
    output_path: str
    output_xlsx: str
    output_txt: str
    error: str
