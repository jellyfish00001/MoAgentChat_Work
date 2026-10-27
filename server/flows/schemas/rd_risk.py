"""Structured LLM outputs for rd_risk_dashboard (narrative only)."""

from __future__ import annotations

from pydantic import BaseModel, Field


class DashboardBrief(BaseModel):
    headline: str = Field(description="一句話總標題")
    risks: list[str] = Field(description="前 3–5 個風險要點（勿重算金額）")
    actions: list[str] = Field(description="可落地管理行動")
