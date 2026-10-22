"""Structured LLM outputs for qv_dms_pipeline."""

from __future__ import annotations

from pydantic import BaseModel


class PipelineAdvice(BaseModel):
    can_start_cover: bool
    blockers: list[str]
    next_actions: list[str]
    summary: str
