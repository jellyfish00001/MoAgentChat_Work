"""Demo 個人排程工具：人工確認後呼叫有 Job Key 保護的內部 API。"""

import json
import logging
from typing import Literal
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from langchain_core.tools import tool
from langgraph.config import get_config
from langgraph.types import interrupt
from pydantic import ValidationError

from flows.config import get_settings
from flows.domain.schedule import ScheduleDraft

logger = logging.getLogger(__name__)

SCHEDULE_PROMPT = (
    "你可以使用 create_schedule 幫使用者建立個人排程，包括每日、每週、每月、每 N 小時。"
    "理解完整對話（如『照剛才內容每個月跑一次』），將未來要執行的內容寫成獨立完整 prompt，"
    "不要在 prompt 包含再次建立排程的指令。時間預設台北 09:00；每週或每月日期不明時先詢問。"
    "自動寄信預設關閉，只有使用者明確要求才設 true，工具會顯示確認卡，"
    "不要先另外問是否建立，直接呼叫工具。只有工具回傳 created 才能說已建立，"
    "並說明側欄排程可查看；failed 或 rejected 必須回報原因，不要假裝成功。"
)


@tool
def create_schedule(
    title: str,
    prompt: str,
    kind: Literal["daily", "weekly", "monthly", "every_n_hours"],
    time_of_day: str = "09:00",
    weekday: int | None = None,
    day_of_month: int | None = None,
    interval_hours: int | None = None,
    auto_send_mail: bool = False,
) -> str:
    """Create a personal recurring schedule after user approval.

    Args:
        title: Short schedule title.
        prompt: Complete standalone instruction to execute in future runs.
        kind: daily, weekly, monthly, or every_n_hours.
        time_of_day: Taipei wall-clock time in HH:mm, default 09:00.
        weekday: Required for weekly; Sunday=0 through Saturday=6.
        day_of_month: Required for monthly; 1-31, clamped to month end.
        interval_hours: Required for every_n_hours; 1-168.
        auto_send_mail: False unless the user explicitly requested automatic mail.
    """
    config = get_config()
    metadata = config.get("metadata") or {}
    settings = get_settings()
    if metadata.get("source") == "schedule":
        return json.dumps(
            {"status": "rejected", "error": "排程執行中不能建立其他排程。"}, ensure_ascii=False
        )
    user_id = metadata.get("user_id")
    if not isinstance(user_id, str) or not user_id.strip():
        return json.dumps(
            {"status": "rejected", "error": "缺少目前使用者，請重新整理 Demo 後再試。"},
            ensure_ascii=False,
        )
    if not settings.schedule_job_key:
        return json.dumps(
            {"status": "failed", "error": "尚未設定排程內部連線金鑰 SCHEDULE_JOB_KEY。"},
            ensure_ascii=False,
        )
    try:
        draft = ScheduleDraft(
            title=title,
            prompt=prompt,
            kind=kind,
            time_of_day=time_of_day,
            weekday=weekday,
            day_of_month=day_of_month,
            interval_hours=interval_hours,
            auto_send_mail=auto_send_mail,
        )
    except ValidationError as exc:
        return json.dumps({"status": "rejected", "error": str(exc)}, ensure_ascii=False)

    response = interrupt(
        {
            "action_requests": [
                {
                    "name": "create_schedule",
                    "args": draft.confirmation(),
                    "description": "確認建立此排程？開啟自動寄信即授權後續執行寄送。",
                }
            ],
            "review_configs": [
                {"action_name": "create_schedule", "allowed_decisions": ["approve", "reject"]}
            ],
        }
    )
    decisions = response.get("decisions") if isinstance(response, dict) else None
    if (
        not decisions
        or not isinstance(decisions, list)
        or not isinstance(decisions[0], dict)
        or decisions[0].get("type") != "approve"
    ):
        return json.dumps(
            {"status": "cancelled", "error": "使用者取消建立排程。"}, ensure_ascii=False
        )

    request = Request(
        settings.scheduler_api_url.rstrip("/") + "/api/internal/schedules/personal",
        data=json.dumps(draft.api_payload(user_id, settings.langgraph_api_url)).encode("utf-8"),
        headers={"Content-Type": "application/json", "X-Job-Key": settings.schedule_job_key},
        method="POST",
    )
    try:
        with urlopen(request, timeout=30) as result:
            schedule = json.load(result)
    except (HTTPError, URLError, TimeoutError) as exc:
        logger.error("Scheduler create failed: %s", exc)
        return json.dumps({"status": "failed", "error": f"排程建立失敗：{exc}"}, ensure_ascii=False)
    return json.dumps({"status": "created", "schedule": schedule}, ensure_ascii=False)
