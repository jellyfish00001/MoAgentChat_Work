"""寄信方式（IO）：dry_run 只寫 log，logic_app POST 到 Azure Logic App。"""

from __future__ import annotations

import json
import logging
from collections.abc import Callable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from flows.config import Settings

logger = logging.getLogger(__name__)

Sender = Callable[[Settings, list[str], list[str], str, str], None]


class MailError(RuntimeError):
    """寄信失敗（連線或 Logic App 回錯），訊息可直接回給 LLM／使用者。"""


def send_dry_run(settings: Settings, to: list[str], cc: list[str], subject: str, body: str) -> None:
    """不寄出，只把信件內容印在 log（本機測試用）。"""
    logger.warning(
        "[mail dry_run] 沒有真的寄出\nTo: %s\nCc: %s\nSubject: %s\n\n%s",
        ", ".join(to),
        ", ".join(cc),
        subject,
        body,
    )


def send_logic_app(
    settings: Settings, to: list[str], cc: list[str], subject: str, body: str
) -> None:
    """POST 到 Logic App 寄信；2xx 只代表收到，實際寄出要看 Logic App run history。"""
    # 1. 欄位對應目前 Logic App 的 schema；沒有副本欄位，cc 併進收件人
    payload = {
        "DataFactoryName": subject,
        "EmailTo": ";".join(to + cc),
        "ErrorMessage": body,
        "PipelineName": "AI Agent",
    }
    request = Request(
        settings.mail_logic_app_url.strip(),
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    # 2. 呼叫並把 HTTP／連線錯誤轉成 MailError，避免例外打斷整個對話
    try:
        with urlopen(request, timeout=30):
            pass
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise MailError(f"Logic App 寄信失敗（HTTP {exc.code}）：{detail}") from exc
    except URLError as exc:
        raise MailError(f"連不到 Logic App：{exc.reason}") from exc


SENDERS: dict[str, Sender] = {"dry_run": send_dry_run, "logic_app": send_logic_app}

# 各寄信方式啟動時必填的設定（Settings 欄位名 → 環境變數名）
REQUIRED_SETTINGS: dict[str, tuple[tuple[str, str], ...]] = {
    "dry_run": (("mail_allowed_domains", "MAIL_ALLOWED_DOMAINS"),),
    "logic_app": (
        ("mail_allowed_domains", "MAIL_ALLOWED_DOMAINS"),
        ("mail_logic_app_url", "MAIL_LOGIC_APP_URL"),
    ),
}
