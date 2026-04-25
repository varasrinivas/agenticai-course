"""
B2B Ecommerce Order Pipeline — Shared State & Base Agent

PipelineState flows between:
  Order Intake Agent -> Fulfillment Planning Agent -> Exception Monitor Agent -> Communication Agent
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class OrderIntakeResult(BaseModel):
    """Output from Order Intake Agent (Agent 1)."""
    order_id: str = ""
    customer_id: str = ""
    customer_name: str = ""
    items: list[dict[str, Any]] = Field(default_factory=list)
    validation_passed: bool = False
    validation_errors: list[str] = Field(default_factory=list)
    inventory_status: dict[str, Any] = Field(default_factory=dict)
    pricing_verified: bool = False
    pricing_discrepancies: list[str] = Field(default_factory=list)


class FulfillmentResult(BaseModel):
    """Output from Fulfillment Planning Agent (Agent 2)."""
    warehouse_allocations: list[dict[str, Any]] = Field(default_factory=list)
    split_shipment_needed: bool = False
    selected_carrier: str = ""
    estimated_shipping_cost: float = 0.0
    estimated_delivery_date: str = ""
    sla_feasible: bool = False


class ExceptionResult(BaseModel):
    """Output from Exception Monitor Agent (Agent 3)."""
    sla_status: str = ""  # on_track, at_risk, violated
    exceptions_detected: list[str] = Field(default_factory=list)
    escalation_needed: bool = False
    escalation_reason: str = ""
    consecutive_violations: int = 0


class CommunicationResult(BaseModel):
    """Output from Communication Agent (Agent 4)."""
    customer_update_sent: bool = False
    customer_message: str = ""
    internal_alert_sent: bool = False
    internal_alert: str = ""
    event_logged: bool = False
    log_entry: dict[str, Any] = Field(default_factory=dict)


class PipelineState(BaseModel):
    """Typed state flowing through all 4 agents."""
    pipeline_id: str = ""
    started_at: str = ""
    current_agent: str = ""
    agent_trace: list[dict[str, Any]] = Field(default_factory=list)
    raw_order: dict[str, Any] = Field(default_factory=dict)
    intake: OrderIntakeResult = Field(default_factory=OrderIntakeResult)
    fulfillment: FulfillmentResult = Field(default_factory=FulfillmentResult)
    exception: ExceptionResult = Field(default_factory=ExceptionResult)
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
