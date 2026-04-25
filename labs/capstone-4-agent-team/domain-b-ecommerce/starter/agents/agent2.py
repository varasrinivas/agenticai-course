"""
Fulfillment Planning Agent (Agent 2) — B2B Ecommerce Order Pipeline

Tools:
- allocate_inventory: Allocate stock from optimal warehouse(s)
- select_warehouse: Choose warehouse based on proximity and stock
- calculate_shipping: Calculate shipping cost and estimated delivery

HITL gate: triggers when split-shipment is needed (multiple warehouses).

YOUR TASK: Complete the TODO sections.
"""

import json
from typing import Any
import anthropic
from agents import BaseAgent, PipelineState
from mock_data import ORDERS, INVENTORY, CARRIERS, SLA_RULES

MODEL = "claude-sonnet-4-20250514"
MAX_ITERATIONS = 10

TOOL_SCHEMAS = [
    {
        "name": "allocate_inventory",
        "description": "Allocate inventory for order items from available warehouses. Returns allocation plan, noting if split shipment is required.",
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {"type": "string"},
                "inventory_status": {"type": "object", "description": "Per-SKU inventory from intake"},
            },
            "required": ["order_id", "inventory_status"],
        },
    },
    {
        "name": "select_warehouse",
        "description": "Select optimal warehouse based on stock availability and proximity to shipping address.",
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {"type": "string"},
                "sku": {"type": "string"},
                "qty_needed": {"type": "integer"},
            },
            "required": ["order_id", "sku", "qty_needed"],
        },
    },
    {
        "name": "calculate_shipping",
        "description": "Calculate shipping cost and estimated delivery date based on carrier, warehouse, and SLA tier.",
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {"type": "string"},
                "warehouse_id": {"type": "string"},
                "sla_tier": {"type": "string"},
            },
            "required": ["order_id", "warehouse_id", "sla_tier"],
        },
    },
]


def allocate_inventory(order_id: str, inventory_status: dict) -> dict:
    """Allocate inventory from warehouses."""
    # TODO: Implement
    # 1. For each SKU, find warehouses with sufficient stock
    # 2. If no single warehouse has enough, plan a split shipment
    # 3. Return {"allocations": [...], "split_shipment": bool}
    pass


def select_warehouse(order_id: str, sku: str, qty_needed: int) -> dict:
    """Select optimal warehouse for a SKU."""
    # TODO: Implement
    # 1. Check each warehouse for stock of the SKU
    # 2. Prefer warehouses closest to shipping address (simple state-distance heuristic)
    # 3. Return {"warehouse_id": str, "available": int, "can_fulfill": bool}
    pass


def calculate_shipping(order_id: str, warehouse_id: str, sla_tier: str) -> dict:
    """Calculate shipping cost and ETA."""
    # TODO: Implement
    # 1. Look up SLA rules for the tier
    # 2. Select carrier matching the SLA tier
    # 3. Calculate estimated cost and delivery date
    # 4. Return {"carrier": str, "cost": float, "estimated_delivery": str, "sla_feasible": bool}
    pass


TOOL_HANDLERS = {
    "allocate_inventory": lambda args: allocate_inventory(**args),
    "select_warehouse": lambda args: select_warehouse(**args),
    "calculate_shipping": lambda args: calculate_shipping(**args),
}


def execute_tool(tool_name: str, tool_input: dict) -> str:
    handler = TOOL_HANDLERS.get(tool_name)
    if not handler:
        return json.dumps({"error": f"Unknown tool: {tool_name}"})
    try:
        result = handler(tool_input)
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": f"Tool execution failed: {str(e)}"})


class FulfillmentPlanningAgent(BaseAgent):
    name = "FulfillmentPlanningAgent"
    tool_schemas = TOOL_SCHEMAS

    system_prompt = """You are the Fulfillment Planning Agent for a B2B ecommerce pipeline.
Plan warehouse allocation, carrier selection, and shipping for each order.

You MUST:
1. allocate_inventory — plan warehouse allocation
2. select_warehouse — choose optimal warehouse per SKU
3. calculate_shipping — estimate cost and delivery date

If a split shipment is required (multiple warehouses needed), flag it.
Split shipments require human approval before proceeding."""

    def execute_tool(self, tool_name: str, tool_input: dict) -> str:
        return execute_tool(tool_name, tool_input)

    def build_user_message(self, state: PipelineState) -> str:
        intake = state.intake
        return (
            f"Plan fulfillment for {intake.order_id}:\n"
            f"Items: {json.dumps(intake.items)}\n"
            f"Inventory Status: {json.dumps(intake.inventory_status)}\n"
            f"SLA Tier: {state.raw_order.get('sla_tier')}\n"
            f"Ship To: {json.dumps(state.raw_order.get('shipping_address', {}))}"
        )

    def run(self, state: PipelineState) -> PipelineState:
        # TODO: Implement ReAct loop with HITL for split shipments
        return state

    def update_state(self, state: PipelineState, result_text: str) -> PipelineState:
        return state
