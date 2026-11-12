"""排程建立參數與純驗證，對齊 Scheduler API 的週期數值。"""

from typing import Literal

from pydantic import BaseModel, Field, model_validator


class ScheduleDraft(BaseModel):
    """LLM 可指定的排程內容；使用者歸屬及服務網址不交給模型指定。"""

    title: str = Field(min_length=1, max_length=200)
    prompt: str = Field(min_length=1)
    kind: Literal["daily", "weekly", "monthly", "every_n_hours"]
    time_of_day: str = Field(default="09:00", pattern=r"^(?:[01]\d|2[0-3]):[0-5]\d$")
    weekday: int | None = Field(default=None, ge=0, le=6)
    day_of_month: int | None = Field(default=None, ge=1, le=31)
    interval_hours: int | None = Field(default=None, ge=1, le=168)
    auto_send_mail: bool = False

    @model_validator(mode="after")
    def validate_period(self) -> "ScheduleDraft":
        """明確指定週期必要欄位，不以猜測日期建立排程。"""
        if not self.title.strip() or not self.prompt.strip():
            raise ValueError("標題與執行內容不可空白。")
        required = {
            "weekly": self.weekday,
            "monthly": self.day_of_month,
            "every_n_hours": self.interval_hours,
        }
        if self.kind in required and required[self.kind] is None:
            raise ValueError(
                "每週需指定 weekday、每月需指定 day_of_month、每 N 小時需 interval_hours。"
            )
        return self

    def api_payload(self, user_id: str, api_url: str) -> dict[str, object]:
        """只產生個人 Demo 排程，服務網址由環境提供。"""
        return {
            "userId": user_id,
            "title": self.title.strip(),
            "prompt": self.prompt.strip(),
            "kind": {"daily": 0, "weekly": 1, "every_n_hours": 2, "monthly": 3}[self.kind],
            "timeOfDay": None if self.kind == "every_n_hours" else f"{self.time_of_day}:00",
            "weekday": self.weekday if self.kind == "weekly" else None,
            "dayOfMonth": self.day_of_month if self.kind == "monthly" else None,
            "intervalHours": self.interval_hours if self.kind == "every_n_hours" else None,
            "autoSendMail": self.auto_send_mail,
            "assistantId": "agent",
            "apiUrl": api_url,
        }

    def confirmation(self) -> dict[str, str]:
        """產生可讀的確認內容，明確標示自動寄信僅限受控測試。"""
        period = {
            "daily": "每日",
            "weekly": f"每週（星期日為 0）：{self.weekday}",
            "monthly": f"每月 {self.day_of_month} 日（無此日則月底）",
            "every_n_hours": f"每 {self.interval_hours} 小時",
        }[self.kind]
        return {
            "排程名稱": self.title,
            "執行內容": self.prompt,
            "週期": period,
            "時間": "固定間隔" if self.kind == "every_n_hours" else f"{self.time_of_day}（台北）",
            "信件自動發送": "開啟：僅內網測試模式自動寄送至核准信箱，否則需確認"
            if self.auto_send_mail
            else "關閉：寄信需確認",
        }
