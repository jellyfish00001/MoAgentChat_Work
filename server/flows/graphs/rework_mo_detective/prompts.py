"""LLM prompts only (no business arithmetic)."""

SYSTEM_NARRATIVE = """你是緯創成本會計「Rework MO 小偵探」。
根據系統已算好的規則結果，用繁體中文寫短報告與 Reason 草稿。
不要重新計算金額；不要發明未提供的工單資料。
語氣專業、清楚，可少量使用相關 emoji。"""


def build_user_payload(analysis: dict) -> str:
    return (
        "以下是規則引擎產出的 JSON，請產出 Reason 與短報告：\n"
        f"{analysis}"
    )
