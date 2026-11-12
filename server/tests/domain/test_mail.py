"""flows.domain.mail 的純規則測試。"""

from __future__ import annotations

from flows.domain.mail import (
    MAX_RECIPIENTS,
    check_recipients,
    check_test_recipients,
    is_unattended_run,
    merge_edited_fields,
    normalize_addresses,
    parse_domains,
)

ALLOWED = {"wistron.com"}


def test_is_unattended_run_only_matches_schedule_source() -> None:
    """排程來源需要阻擋；一般對話與缺少來源仍使用確認流程。"""
    assert is_unattended_run({"source": "schedule", "schedule_id": "123"})
    assert not is_unattended_run({"source": "chat"})
    assert not is_unattended_run({})
    assert not is_unattended_run(None)


def test_test_restriction_checks_exact_addresses_and_cc() -> None:
    """同網域其他人也不可寄；大小寫可不同，副本不得繞過。"""
    permitted = "wits.johnnyho@wistron.com,JohnnyHo@wits.com"
    assert check_test_recipients(["Wits.JohnnyHo@wistron.com"], [], permitted) is None
    assert check_test_recipients(["JohnnyHo@wits.com"], ["other@wits.com"], permitted)
    assert check_test_recipients(["other@wistron.com"], [], permitted)
    assert check_test_recipients(["JohnnyHo@wits.com"], [], "")


def test_parse_domains_trims_and_lowercases() -> None:
    """網域設定去空白、轉小寫、忽略空項目。"""
    assert parse_domains(" Wistron.com, ,wiwynn.com ") == {"wistron.com", "wiwynn.com"}
    assert parse_domains("") == set()


def test_normalize_addresses_accepts_list_string_and_none() -> None:
    """list、逗號／分號字串、None 都整理成乾淨的 list。"""
    assert normalize_addresses([" a@wistron.com ", ""]) == ["a@wistron.com"]
    assert normalize_addresses("a@wistron.com; b@wistron.com,") == [
        "a@wistron.com",
        "b@wistron.com",
    ]
    assert normalize_addresses(None) == []


def test_check_recipients_ok() -> None:
    """允許網域（不分大小寫）通過。"""
    assert check_recipients(["a@Wistron.COM"], ["b@wistron.com"], ALLOWED) is None


def test_check_recipients_requires_to() -> None:
    """沒有收件人要擋。"""
    assert check_recipients([], ["b@wistron.com"], ALLOWED) == "沒有收件人。"


def test_check_recipients_rejects_invalid_and_foreign_domain() -> None:
    """格式錯誤與不在白名單的網域（含副本）都要擋。"""
    assert "不是有效的 email" in check_recipients(["not-an-email"], [], ALLOWED)
    assert "不在允許的網域" in check_recipients(["a@wistron.com"], ["x@gmail.com"], ALLOWED)
    for address in (
        "a\n@wistron.com",
        "a@wistron.com\n",
        "a<b>@wistron.com",
        "a@wistron.com;b@wistron.com",
    ):
        assert check_recipients([address], [], ALLOWED)


def test_check_recipients_rejects_when_no_domain_allowed() -> None:
    """白名單空白時一律拒絕，不可預設放行。"""
    assert "不在允許的網域" in check_recipients(["a@wistron.com"], [], set())


def test_check_recipients_limits_total_count() -> None:
    """收件人加副本超過上限要擋。"""
    to = [f"u{i}@wistron.com" for i in range(MAX_RECIPIENTS)]
    assert check_recipients(to, [], ALLOWED) is None
    assert "超過" in check_recipients(to, ["extra@wistron.com"], ALLOWED)


def test_merge_edited_fields_restores_types_and_drops_unknown_keys() -> None:
    """確認畫面回傳的 JSON 字串轉回 list，多塞的欄位丟掉，沒改的保留原值。"""
    fields = {"to": ["a@wistron.com"], "cc": [], "subject": "Hi", "body": "x"}
    edited = {"to": '["b@wistron.com"]', "cc": "c@wistron.com", "subject": "Hello", "evil": 1}
    assert merge_edited_fields(fields, edited) == {
        "to": ["b@wistron.com"],
        "cc": "c@wistron.com",
        "subject": "Hello",
        "body": "x",
    }
