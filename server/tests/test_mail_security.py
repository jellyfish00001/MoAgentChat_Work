"""寄信安全回歸：真實 HITL graph，寄信與網路出口全部 mock。"""

import json
from typing import TypedDict
from unittest.mock import Mock

import pytest
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command

from flows.config import Settings
from flows.tools import mail, mail_senders

TO = "Wits.JohnnyHo@wistron.com"
PERMITTED = "wits.johnnyho@wistron.com,JohnnyHo@wits.com"


class State(TypedDict):
    """最小工具 graph 狀態。"""

    result: str


@pytest.fixture
def context(monkeypatch):
    """不讀取 .env；禁止任何測試接觸真實寄信端點。"""
    settings = Settings(
        _env_file=None,
        MAIL_BACKEND="logic_app",
        MAIL_ALLOWED_DOMAINS="wistron.com,wits.com",
        MAIL_LOGIC_APP_URL="https://invalid.example.test/mail",
        MAIL_TEST_MODE=True,
        MAIL_TEST_RECIPIENTS=PERMITTED,
    )
    sender = Mock()
    network = Mock(side_effect=AssertionError("測試不得呼叫真實網路"))
    monkeypatch.setitem(mail.SENDERS, "logic_app", sender)
    monkeypatch.setattr(mail_senders, "urlopen", network)
    monkeypatch.setattr(mail, "get_settings", lambda: settings)

    def call_tool(state: State) -> dict[str, str]:
        """使用 LangGraph 真實 configurable 與 interrupt 機制。"""
        return {"result": mail.send_mail.invoke({"to": [TO], "subject": "test", "body": "test"})}

    builder = StateGraph(State)
    builder.add_node("tool", call_tool)
    builder.add_edge(START, "tool")
    builder.add_edge("tool", END)
    graph = builder.compile(checkpointer=InMemorySaver())
    return settings, sender, network, graph


def run_config():
    """連舊版的所有授權旗標也不能恢復免確認分支。"""
    flags = {
        "source": "schedule",
        "schedule_auto_send_mail": True,
        "schedule_mail_authorized": True,
    }
    return {"configurable": {"thread_id": "test-thread", **flags}, "metadata": flags}


@pytest.mark.parametrize("source", ["schedule", "chat", None])
def test_forged_and_legacy_flags_always_require_confirmation(context, source):
    """無論入口、來源或舊 thread 授權，工具本身均要求確認。"""
    _, sender, _, graph = context
    config = run_config()
    config["metadata"]["source"] = source
    result = graph.invoke({}, config)
    assert result.get("__interrupt__")
    sender.assert_not_called()


def test_manual_mail_approval_and_rejection(context):
    """既有核准／取消流程維持正常，不核准不寄。"""
    _, sender, _, graph = context
    config = run_config()
    assert graph.invoke({}, config).get("__interrupt__")
    sender.assert_not_called()
    result = graph.invoke(Command(resume={"decisions": [{"type": "approve"}]}), config)
    assert json.loads(result["result"])["status"] == "sent"
    sender.assert_called_once()
    assert graph.invoke({}, config).get("__interrupt__")
    result = graph.invoke(Command(resume={"decisions": [{"type": "reject"}]}), config)
    assert json.loads(result["result"])["status"] == "cancelled"
    sender.assert_called_once()


@pytest.mark.parametrize(
    "response",
    [
        {"decisions": []},
        {"decisions": ["approve"]},
        {"decisions": [{"type": "unexpected"}]},
        {"decisions": [{"type": "edit"}]},
        {"decisions": [{"type": "edit", "edited_action": {"args": []}}]},
    ],
)
def test_invalid_confirmation_is_explicitly_rejected(context, response):
    """畸形回覆不冒稱使用者取消，也不執行寄送。"""
    _, sender, _, graph = context
    config = run_config()
    assert graph.invoke({}, config).get("__interrupt__")
    result = graph.invoke(Command(resume=response), config)
    assert json.loads(result["result"])["status"] == "rejected"
    sender.assert_not_called()


def test_empty_resume_mapping_keeps_waiting_without_sending(context):
    """LangGraph 把空 mapping 視為沒有提供 interrupt 回覆，不應誤寄。"""
    _, sender, _, graph = context
    config = run_config()
    assert graph.invoke({}, config).get("__interrupt__")
    assert graph.invoke(Command(resume={}), config).get("__interrupt__")
    sender.assert_not_called()


@pytest.mark.parametrize(
    "edit",
    [
        {"to": ["other@wistron.com"]},
        {"cc": ["other@wits.com"]},
        {"to": [123]},
        {"to": '{"email":"other@wits.com"}'},
        {"subject": {"unexpected": True}},
    ],
)
def test_edited_recipient_or_invalid_fields_never_send(context, edit):
    """確認後改成非測試信箱、非字串欄位也不可寄。"""
    _, sender, _, graph = context
    config = run_config()
    assert graph.invoke({}, config).get("__interrupt__")
    result = graph.invoke(
        Command(
            resume={
                "decisions": [
                    {
                        "type": "edit",
                        "edited_action": {"args": edit},
                    }
                ]
            }
        ),
        config,
    )
    assert json.loads(result["result"])["status"] == "rejected"
    sender.assert_not_called()


@pytest.mark.parametrize(
    "to,cc",
    [
        (["other@wistron.com"], []),
        ([TO], ["other@wits.com"]),
        ([TO], [123]),
    ],
)
def test_initial_invalid_recipients_never_send(context, to, cc):
    """清單外的人直接拒絕，不必進入確認。"""
    settings, sender, _, _ = context
    result = json.loads(mail.run_send_mail(settings, to, "test", "test", cc))
    assert result["status"] == "rejected"
    sender.assert_not_called()


@pytest.mark.parametrize(
    "to,cc",
    [
        (["other@wistron.com"], []),
        ([TO], ["other@wits.com"]),
        ([TO], ["x@gmail.com"]),
    ],
)
def test_direct_sender_cannot_bypass_test_restriction(context, to, cc):
    """最終真實寄信出口也檢查，不只依賴工具層。"""
    settings, _, network, _ = context
    with pytest.raises(mail_senders.MailError):
        mail_senders.send_logic_app(settings, to, cc, "test", "test")
    network.assert_not_called()


def test_dry_run_does_not_log_private_mail_content(context, caplog):
    """一般日誌不留下信箱、主旨或薪資內容。"""
    settings, _, _, _ = context
    mail_senders.send_dry_run(settings, [TO], [], "private-subject", "private-salary")
    assert TO not in caplog.text
    assert "private-subject" not in caplog.text
    assert "private-salary" not in caplog.text


@pytest.mark.parametrize("auto", [True, False])
def test_restricted_test_mode_obeys_schedule_switch(context, auto):
    """僅測試模式可免確認；排程開關關閉仍會中斷。"""
    settings, sender, _, graph = context
    settings.app_env = "test"
    settings.test_schedule_auto_mail = True
    config = run_config()
    config["configurable"]["schedule_auto_send_mail"] = auto
    result = graph.invoke({}, config)
    if auto:
        assert not result.get("__interrupt__")
        assert json.loads(result["result"])["status"] == "sent"
        sender.assert_called_once()
    else:
        assert result.get("__interrupt__")
        sender.assert_not_called()


def test_chat_still_requires_review_in_test_mode(context):
    """測試環境也不允許一般聊天自動寄信。"""
    settings, sender, _, graph = context
    settings.app_env = "test"
    settings.test_schedule_auto_mail = True
    config = run_config()
    config["metadata"]["source"] = "chat"
    assert graph.invoke({}, config).get("__interrupt__")
    sender.assert_not_called()


@pytest.mark.parametrize(
    "overrides",
    [
        {"APP_ENV": "production"},
        {"MAIL_TEST_MODE": False},
        {"MAIL_TEST_RECIPIENTS": ""},
        {"MAIL_TEST_RECIPIENTS": "other@wistron.com"},
    ],
)
def test_unsafe_test_mode_configuration_fails_startup(overrides):
    """錯誤部署設定直接拒絕，不能降級成不受限制的實發。"""
    from pydantic import ValidationError

    values = {
        "APP_ENV": "qas",
        "TEST_SCHEDULE_AUTO_MAIL": True,
        "MAIL_TEST_MODE": True,
        "MAIL_TEST_RECIPIENTS": PERMITTED,
        **overrides,
    }
    with pytest.raises(ValidationError):
        Settings(_env_file=None, **values)


def test_automatic_test_mail_still_rejects_nonapproved_recipient(context):
    """免確認分支也不能繞過收件人限制。"""
    settings, sender, _, _ = context
    settings.app_env = "test"
    settings.test_schedule_auto_mail = True
    result = json.loads(
        mail.run_send_mail(settings, [TO], "test", "test", ["other@wistron.com"], True)
    )
    assert result["status"] == "rejected"
    sender.assert_not_called()
