"""
Healthcare Pre-Authorization Multi-Agent Pipeline — Shared State & Base Agent (Solution)
Identical to the starter __init__.py.
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class IntakeResult(BaseModel):
    request_id: str = ""
    patient_name: str = ""
    patient_id: str = ""
    plan_id: str = ""
    cpt_code: str = ""
    diagnosis_codes: list[str] = Field(default_factory=list)
    provider_npi: str = ""
    facility_id: str = ""
    clinical_notes: str = ""
    validation_passed: bool = False
    validation_errors: list[str] = Field(default_factory=list)
    eligibility_confirmed: bool = False
    clinical_info_extracted: dict[str, Any] = Field(default_factory=dict)


class CriteriaResult(BaseModel):
    criteria_found: bool = False
    procedure_name: str = ""
    procedure_category: str = ""
    diagnosis_match: bool = False
    matched_diagnoses: list[str] = Field(default_factory=list)
    unmatched_diagnoses: list[str] = Field(default_factory=list)
    medical_necessity_score: float = 0.0
    criteria_details: dict[str, Any] = Field(default_factory=dict)
    network_status: str = ""
    benefit_covered: bool = False


class DecisionResult(BaseModel):
    determination: str = ""
    confidence: float = 0.0
    reason: str = ""
    conditions: list[str] = Field(default_factory=list)
    peer_review_required: bool = False
    hitl_triggered: bool = False
    hitl_decision: str = ""
    approval_validity_days: int = 0


class CommunicationResult(BaseModel):
    notification_drafted: bool = False
    letter_text: str = ""
    letter_format: str = ""
    communication_logged: bool = False
    log_entry: dict[str, Any] = Field(default_factory=dict)


class PipelineState(BaseModel):
    pipeline_id: str = ""
    started_at: str = ""
    current_agent: str = ""
    agent_trace: list[dict[str, Any]] = Field(default_factory=list)
    raw_request: dict[str, Any] = Field(default_factory=dict)
    intake: IntakeResult = Field(default_factory=IntakeResult)
    criteria: CriteriaResult = Field(default_factory=CriteriaResult)
    decision: DecisionResult = Field(default_factory=DecisionResult)
    communication: CommunicationResult = Field(default_factory=CommunicationResult)
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
