from __future__ import annotations

from typing import Annotated, Any, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class QvDmsState(TypedDict, total=False):
    messages: Annotated[list[BaseMessage], add_messages]
    data_dir: str
    inventory: dict[str, Any]
    cover_summary: dict[str, Any]
    period_analysis: dict[str, Any]
    narrative: dict[str, Any]
    html: str
    output_path: str
    output_xlsx: str
    output_html: str
