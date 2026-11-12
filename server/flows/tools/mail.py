"""寄信工具 send_mail：寄出前一定先讓使用者確認（HITL），收件人只能是允許的網域。

規則在 flows.domain.mail，寄信方式在 flows.tools.mail_senders；這裡只負責串接。
"""

from __future__ import annotations

import json
from typing import Any

from langchain_core.tools import BaseTool, tool
from langgraph.types import interrupt

from flows.config import Settings, get_settings
from flows.domain.mail import (
    check_recipients,
    merge_edited_fields,
    normalize_addresses,
    parse_domains,
)
from flows.tools.mail_senders import REQUIRED_SETTINGS, SENDERS, MailError

MAIL_PROMPT = (
    "使用者要求寄信時用 send_mail，系統會先讓使用者確認內容，不需要另外在對話中詢問。"
    "不知道收件人 email 時要先問使用者，不要自己猜。"
    "status 是 dry_run 時，要告訴使用者目前是測試模式，信沒有真的寄出。"
    "status 是 sent 時，只代表 Logic App 已受理請求，不能保證信件已送達，請提醒使用者查收。"
)


def _result(status: str, **extra: Any) -> str:
    """組 tool 回傳的 JSON 字串（保留中文）。"""
    return json.dumps({"status": status, **extra}, ensure_ascii=False)


def request_approval(fields: dict[str, Any]) -> dict[str, Any] | None:
    """以 agent-chat-ui 的 HITL 格式中斷等使用者確認；核准回傳欄位（可能被改過），拒絕回傳 None。"""
    response = interrupt(
        {
            "action_requests": [
                {
                    "name": "send_mail",
                    "args": fields,
                    "description": "確認要寄出這封信嗎？可以先修改收件人、主旨或內容。",
                }
            ],
            "review_configs": [
                {"action_name": "send_mail", "allowed_decisions": ["approve", "edit", "reject"]}
            ],
        }
    )

    decisions = response.get("decisions") if isinstance(response, dict) else None
    decision = decisions[0] if isinstance(decisions, list) and decisions else {}
    if decision.get("type") == "approve":
        return dict(fields)
    if decision.get("type") == "edit":
        edited = (decision.get("edited_action") or {}).get("args") or {}
        return merge_edited_fields(fields, edited)
    return None


def run_send_mail(
    settings: Settings, to: list[str], subject: str, body: str, cc: list[str] | None
) -> str:
    """寄信流程本體：檢查 → 使用者確認 → 再檢查 → 寄出；設定由呼叫端注入方便測試。"""
    allowed = parse_domains(settings.mail_allowed_domains)

    # 1. 先檢查 LLM 給的收件人，不合規就不必打擾使用者
    to, cc = normalize_addresses(to), normalize_addresses(cc)
    if error := check_recipients(to, cc, allowed):
        return _result("rejected", error=error)

    # 2. 中斷等使用者 Approve／Edit／Reject
    approved = request_approval({"to": to, "cc": cc, "subject": subject, "body": body})
    if approved is None:
        return _result("cancelled", error="使用者取消寄信")

    # 3. 使用者可能在確認畫面改了收件人，要再檢查一次
    to, cc = normalize_addresses(approved["to"]), normalize_addresses(approved["cc"])
    if error := check_recipients(to, cc, allowed):
        return _result("rejected", error=error)

    # 4. 依 MAIL_BACKEND 寄出
    backend = settings.mail_backend.strip()
    try:
        SENDERS[backend](settings, to, cc, str(approved["subject"]), str(approved["body"]))
    except MailError as exc:
        return _result("failed", error=str(exc))
    return _result("dry_run" if backend == "dry_run" else "sent", to=to, cc=cc)


@tool
def send_mail(to: list[str], subject: str, body: str, cc: list[str] | None = None) -> str:
    """Send an email. The user will be asked to review and approve it before it is sent.

    Args:
        to: Recipient email addresses.
        subject: Email subject.
        body: Plain text email body.
        cc: Optional CC email addresses.
    """
    # LangChain 以 docstring 當 tool 描述給 LLM，故維持英文；流程見 run_send_mail
    return run_send_mail(get_settings(), to, subject, body, cc)


def load_mail_tools(settings: Settings | None = None) -> list[BaseTool]:
    """沒設定 MAIL_BACKEND 就不開寄信；有設定就檢查必填設定，缺了在啟動時報錯。"""
    settings = settings or get_settings()
    backend = settings.mail_backend.strip()
    if not backend:
        return []
    if backend not in SENDERS:
        raise RuntimeError(f"MAIL_BACKEND 只能是 {', '.join(SENDERS)}，目前是「{backend}」")
    missing = [
        env_name
        for field, env_name in REQUIRED_SETTINGS[backend]
        if not str(getattr(settings, field)).strip()
    ]
    if missing:
        raise RuntimeError("缺少寄信用的環境變數：" + ", ".join(missing))
    return [send_mail]
