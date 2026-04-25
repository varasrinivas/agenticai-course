"""
Healthcare Pre-Authorization Multi-Agent Pipeline — Shared State & Base Agent

This module defines:
1. PipelineState — the typed Pydantic model that flows between all 4 agents
2. BaseAgent — abstract base class for all agents in the pipeline
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Pipeline State — typed object that flows between agents
# ---------------------------------------------------------------------------

class IntakeResult(BaseModel):
    """Output produced by the Intake Agent (Agent 1)."""
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
    """Output produced by the Clinical Criteria Agent (Agent 2)."""
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
    """Output produced by the Decision Agent (Agent 3)."""
    determination: str = ""  # APPROVED, DENIED, PENDED
    confidence: float = 0.0
    reason: str = ""
    conditions: list[str] = Field(default_factory=list)
    peer_review_required: bool = False
    hitl_triggered: bool = False
    hitl_decision: str = ""  # approved, rejected, or empty
    approval_validity_days: int = 0


class CommunicationResult(BaseModel):
    """Output produced by the Communication Agent (Agent 4)."""
    notification_drafted: bool = False
    letter_text: str = ""
    letter_format: str = ""  # approval, denial, pended
    communication_logged: bool = False
    log_entry: dict[str, Any] = Field(default_factory=dict)


class PipelineState(BaseModel):
    """
    The typed state object that flows through all 4 agents.

    Each agent reads from prior stages and writes to its own result field.
    The coordinator passes this object between agents.
    """
    # --- Metadata ---
    pipeline_id: str = ""
    started_at: str = ""
    current_agent: str = ""
    agent_trace: list[dict[str, Any]] = Field(default_factory=list)

    # --- Raw input ---
    raw_request: dict[str, Any] = Field(default_factory=dict)

    # --- Agent outputs ---
    intake: IntakeResult = Field(default_factory=IntakeResult)
    criteria: CriteriaResult = Field(default_factory=CriteriaResult)
    decision: DecisionResult = Field(default_factory=DecisionResult)
    communication: CommunicationResult = Field(default_factory=CommunicationResult)

    # --- Pipeline control ---
    halted: bool = False
    halt_reason: str = ""
    completed: bool = False


# ---------------------------------------------------------------------------
# Base Agent — abstract class that all 4 agents inherit
# ---------------------------------------------------------------------------

class BaseAgent:
    """
    Abstract base class for pipeline agents.

    Subclasses must define:
        - name: str
        - system_prompt: str
        - tool_schemas: list[dict]
        - execute_tool(name, input) -> str
        - update_state(state, result_text) -> PipelineState
    """

    name: str = "BaseAgent"
    system_prompt: str = ""
    tool_schemas: list[dict] = []

    def execute_tool(self, tool_name: str, tool_input: dict) -> str:
        """Execute a tool by name. Must be overridden by subclasses."""
        raise NotImplementedError

    def update_state(self, state: PipelineState, result_text: str) -> PipelineState:
        """Update pipeline state with this agent's results. Must be overridden."""
        raise NotImplementedError

    def build_user_message(self, state: PipelineState) -> str:
        """Build the user message from current pipeline state. Must be overridden."""
        raise NotImplementedError
