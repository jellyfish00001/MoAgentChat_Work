from __future__ import annotations

from typing import Annotated, Any, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class RdRiskState(TypedDict, total=False):
    messages: Annotated[list[BaseMessage], add_messages]
    data_dir: str
    scan: dict[str, Any]
    output_path: str
