"""Structured LLM outputs for qv_dms_pipeline (narrative only)."""

from __future__ import annotations

from pydantic import BaseModel, Field


class PipelineAdvice(BaseModel):
    can_start_cover: bool
    blockers: list[str] = Field(default_factory=list)
    next_actions: list[str] = Field(default_factory=list)
    summary: str
