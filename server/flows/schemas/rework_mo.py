"""Structured LLM outputs for Rework MO detective."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ReasonDraft(BaseModel):
    reason: str = Field(description="建議寫入 Reason 欄的簡短原因")
    confidence: float = Field(ge=0, le=1, description="對原因判斷的信心")
    improvement: str = Field(description="一句可落地的改善建議")


class OrderSummary(BaseModel):
    order_number: str
    narrative: str = Field(description="給使用者看的短報告（繁中）")
    reason_draft: ReasonDraft
