"""
UCC Data Engineering Pipeline — Shared State & Base Agent

PipelineState flows between:
  Ingestion Agent -> Transformation Agent -> Quality Agent -> Reporting Agent
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class IngestionResult(BaseModel):
    """Output from Ingestion Agent (Agent 1)."""
    batch_id: str = ""
    source: str = ""
    format_detected: str = ""
    filing_count: int = 0
    parsed_filings: list[dict[str, Any]] = Field(default_factory=list)
    schema_valid: bool = False
    schema_errors: list[str] = Field(default_factory=list)
    parse_error_count: int = 0


class TransformationResult(BaseModel):
    """Output from Transformation Agent (Agent 2)."""
    normalized_entities: list[dict[str, Any]] = Field(default_factory=list)
    collateral_classifications: list[dict[str, Any]] = Field(default_factory=list)
    entity_resolutions: list[dict[str, Any]] = Field(default_factory=list)
    resolution_conflicts: list[dict[str, Any]] = Field(default_factory=list)
    low_confidence_resolutions: int = 0


class QualityResult(BaseModel):
    """Output from Quality Agent (Agent 3)."""
    checks_passed: int = 0
    checks_failed: int = 0
    quality_score: float = 0.0
    anomalies: list[dict[str, Any]] = Field(default_factory=list)
    scorecard: dict[str, Any] = Field(default_factory=dict)


class ReportingResult(BaseModel):
    """Output from Reporting Agent (Agent 4)."""
    risk_profiles: list[dict[str, Any]] = Field(default_factory=list)
    lien_summary: dict[str, Any] = Field(default_factory=dict)
    pii_redacted: bool = False
    redaction_count: int = 0
    report_generated: bool = False


class PipelineState(BaseModel):
    """Typed state flowing through all 4 agents."""
    pipeline_id: str = ""
    started_at: str = ""
    current_agent: str = ""
    agent_trace: list[dict[str, Any]] = Field(default_factory=list)
    raw_batch: dict[str, Any] = Field(default_factory=dict)
    ingestion: IngestionResult = Field(default_factory=IngestionResult)
    transformation: TransformationResult = Field(default_factory=TransformationResult)
    quality: QualityResult = Field(default_factory=QualityResult)
    reporting: ReportingResult = Field(default_factory=ReportingResult)
    halted: bool = False
    halt_reason: str = ""
    completed: bool = False


class BaseAgent:
    name: str = "BaseAgent"
    system_prompt: str = ""
    tool_schemas: list[dict] = []

    def execute_tool(self, tool_name: str, tool_input: dict) -> str:
        raise NotImplementedError

    def update_state(self, state: PipelineState, result_text: str) -> PipelineState:
        raise NotImplementedError

    def build_user_message(self, state: PipelineState) -> str:
        raise NotImplementedError
