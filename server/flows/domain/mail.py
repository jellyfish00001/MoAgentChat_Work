"""寄信的純規則：收件人整理與檢查、確認畫面回傳值還原（無 LLM，可 pytest）。"""

from __future__ import annotations

import json
import re
from typing import Any

MAX_RECIPIENTS = 20
EMAIL_PATTERN = re.compile(r"^[^@\s]+@([^@\s]+\.[^@\s]+)$")


def parse_domains(raw: str) -> set[str]:
    """把逗號分隔的網域設定轉成小寫集合；空白項目忽略。"""
    return {domain.strip().lower() for domain in raw.split(",") if domain.strip()}


def normalize_addresses(addresses: list[str] | str | None) -> list[str]:
    """收件人統一成 list；使用者在確認畫面可能改成逗號或分號隔開的字串。"""
    if isinstance(addresses, str):
        addresses = re.split(r"[,;]", addresses)
    return [address.strip() for address in addresses or [] if address.strip()]


def check_recipients(
    to: list[str],
    cc: list[str],
    allowed_domains: set[str],
    max_recipients: int = MAX_RECIPIENTS,
) -> str | None:
    """檢查收件人是否可寄；有問題回傳錯誤說明，沒問題回傳 None。"""
    if not to:
        return "沒有收件人。"
    if len(to) + len(cc) > max_recipients:
        return f"收件人加副本超過 {max_recipients} 人。"
    for address in to + cc:
        match = EMAIL_PATTERN.match(address)
        if not match:
            return f"「{address}」不是有效的 email。"
        if match.group(1).lower() not in allowed_domains:
            return f"「{address}」不在允許的網域（{', '.join(sorted(allowed_domains))}）。"
    return None


def restore_edited_value(original: Any, edited: Any) -> Any:
    """把確認畫面改過的值轉回原型別：前端會把 list 顯示成 JSON 字串送回。"""
    if isinstance(original, list) and isinstance(edited, str):
        try:
            return json.loads(edited)
        except json.JSONDecodeError:
            # 收件人也可以用逗號隔開，交給 normalize_addresses 處理
            return edited
    return edited


def merge_edited_fields(fields: dict[str, Any], edited: dict[str, Any]) -> dict[str, Any]:
    """只接受原本就有的欄位，避免前端多塞的值被當成寄信參數。"""
    return {
        key: restore_edited_value(value, edited.get(key, value)) for key, value in fields.items()
    }


def is_unattended_run(metadata: dict[str, Any] | None) -> bool:
    """排程觸發的執行沒有人能按確認；由 run metadata 的 source 判斷。"""
    return (metadata or {}).get("source") == "schedule"
