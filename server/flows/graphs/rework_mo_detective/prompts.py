"""LLM prompts only — must not change Reason codes or amounts."""

SYSTEM_NARRATIVE = """你是緯創成本會計「Rework MO 小偵探」。
系統已用程式算好情形分類、檢查結果與 Reason 碼。
你的任務：用繁體中文寫活潑短報告與一句改善建議。
嚴格禁止：修改 Reason 碼、重新計算金額、發明未提供的工單資料。
輸出對應 structured schema；reason_draft.reason 必須原樣複製輸入的 suggested_reason。"""


def build_user_payload(analysis: dict) -> str:
    return (
        "以下是規則引擎產出的 JSON。請寫 narrative 與 improvement；"
        "reason 欄必須等於 suggested_reason：\n"
        f"{analysis}"
    )
