"""Agent 建立排程的純參數驗證。"""

import pytest
from pydantic import ValidationError

from flows.domain.schedule import ScheduleDraft


def test_monthly_payload_has_personal_owner_and_no_auto_mail_by_default() -> None:
    """個人歸屬由呼叫端提供，預設不授權寄信。"""
    draft = ScheduleDraft(title="月報", prompt="整理報告", kind="monthly", day_of_month=31)
    payload = draft.api_payload("current-user", "http://agent:2024")
    assert payload["kind"] == 3
    assert payload["dayOfMonth"] == 31
    assert payload["userId"] == "current-user"
    assert payload["autoSendMail"] is False
    assert payload["assistantId"] == "agent"
    assert payload["apiUrl"] == "http://agent:2024"
    assert payload["timeOfDay"] == "09:00:00"


@pytest.mark.parametrize("kind", ["weekly", "monthly", "every_n_hours"])
def test_period_requires_explicit_day_or_interval(kind: str) -> None:
    """不能用空日期或空間隔猜測週期。"""
    with pytest.raises(ValidationError):
        ScheduleDraft(title="x", prompt="y", kind=kind)


def test_weekly_and_interval_map_existing_kinds() -> None:
    """週日值零不可當作缺少；固定間隔不帶時刻。"""
    weekly = ScheduleDraft(title="x", prompt="y", kind="weekly", weekday=0)
    assert weekly.api_payload("u", "url")["weekday"] == 0
    interval = ScheduleDraft(title="x", prompt="y", kind="every_n_hours", interval_hours=3)
    assert interval.api_payload("u", "url")["timeOfDay"] is None


def test_auto_mail_confirmation_discloses_pending_authorization() -> None:
    """確認內容須說明自動寄信僅限內網測試。"""
    draft = ScheduleDraft(title="x", prompt="y", kind="daily", auto_send_mail=True)
    assert "僅內網測試模式" in draft.confirmation()["信件自動發送"]
    assert draft.api_payload("user", "http://agent:2024")["autoSendMail"] is True


@pytest.mark.parametrize("time", ["24:00", "09:99", "9am"])
def test_invalid_clock_rejected(time: str) -> None:
    """拒絕非法時間而非默默改成預設。"""
    with pytest.raises(ValidationError):
        ScheduleDraft(title="x", prompt="y", kind="daily", time_of_day=time)
