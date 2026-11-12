"""排程工具確認流程；使用記憶體 graph 與 HTTP mock，不連 LLM 或 Scheduler。"""

import io
import json
from typing import TypedDict
from unittest.mock import Mock
from urllib.error import URLError

import pytest
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command

from flows.config import Settings
from flows.tools import schedule


class State(TypedDict):
    """工具測試的最小狀態。"""

    result: str


@pytest.fixture
def graph_and_http(monkeypatch):
    """建立工具 graph 並攔截 HTTP，確保測試不會建立真排程。"""
    settings = Settings(SCHEDULE_JOB_KEY="unit-test-key")
    monkeypatch.setattr(schedule, "get_settings", lambda: settings)
    http = Mock()
    http.return_value.__enter__ = Mock(return_value=io.StringIO('{"id":"created-id"}'))
    http.return_value.__exit__ = Mock(return_value=False)
    monkeypatch.setattr(schedule, "urlopen", http)

    def call_tool(state: State) -> dict[str, str]:
        """在真實 runnable context 內呼叫工具。"""
        return {
            "result": schedule.create_schedule.invoke(
                {
                    "title": "test",
                    "prompt": "query weather",
                    "kind": "daily",
                }
            )
        }

    builder = StateGraph(State)
    builder.add_node("tool", call_tool)
    builder.add_edge(START, "tool")
    builder.add_edge("tool", END)
    return builder.compile(checkpointer=InMemorySaver()), http


@pytest.mark.parametrize("decision,expected", [("approve", "created"), ("reject", "cancelled")])
def test_http_only_after_explicit_approval(graph_and_http, decision: str, expected: str) -> None:
    """待確認與拒絕不能寫入；核准後只呼叫一次且使用 context 歸屬。"""
    graph, http = graph_and_http
    config = {"configurable": {"thread_id": decision}, "metadata": {"user_id": "current-user"}}
    assert graph.invoke({}, config).get("__interrupt__")
    http.assert_not_called()
    result = graph.invoke(Command(resume={"decisions": [{"type": decision}]}), config)
    assert json.loads(result["result"])["status"] == expected
    if decision == "approve":
        http.assert_called_once()
        request = http.call_args.args[0]
        assert request.full_url.endswith("/api/internal/schedules/personal")
        payload = json.loads(request.data)
        assert payload["userId"] == "current-user"
        assert payload["autoSendMail"] is False
    else:
        http.assert_not_called()


@pytest.mark.parametrize("metadata", [{"source": "schedule", "user_id": "u"}, {}])
def test_rejects_recursive_schedule_and_missing_user(graph_and_http, metadata: dict) -> None:
    """排程遞迴與缺少歸屬都不確認、不寫入。"""
    graph, http = graph_and_http
    config = {"configurable": {"thread_id": "invalid"}, "metadata": metadata}
    result = graph.invoke({}, config)
    assert json.loads(result["result"])["status"] == "rejected"
    assert not result.get("__interrupt__")
    http.assert_not_called()


def test_http_error_is_not_reported_as_created(graph_and_http) -> None:
    """內部 API 失敗要回報 failed，不得假裝建立成功。"""
    graph, http = graph_and_http
    config = {"configurable": {"thread_id": "failed"}, "metadata": {"user_id": "u"}}
    graph.invoke({}, config)
    http.side_effect = URLError("unavailable")
    result = graph.invoke(Command(resume={"decisions": [{"type": "approve"}]}), config)
    assert json.loads(result["result"])["status"] == "failed"
