"""
Order Intake Agent (Agent 1) — B2B Ecommerce Order Pipeline

Tools:
- validate_order: Check order completeness, SKU validity, quantity > 0
- check_inventory: Check stock levels across all warehouses for each SKU
- verify_pricing: Verify PO prices against contract pricing

YOUR TASK: Complete the TODO sections.
"""

import json
from typing import Any
import anthropic
from agents import BaseAgent, PipelineState
from mock_data import ORDERS, INVENTORY, CONTRACT_PRICING

MODEL = "claude-sonnet-4-6"
MAX_ITERATIONS = 10

TOOL_SCHEMAS = [
    {
        "name": "validate_order",
        "description": "Validate a purchase order for completeness: check SKU existence, quantity > 0, required fields present.",
        "input_schema": {
            "type": "object",
            "properties": {"order_id": {"type": "string", "description": "The PO order ID"}},
            "required": ["order_id"],
        },
    },
    {
        "name": "check_inventory",
        "description": "Check stock levels across all warehouses for each SKU in the order. Returns per-warehouse availability.",
        "input_schema": {
            "type": "object",
            "properties": {"order_id": {"type": "string", "description": "The PO order ID"}},
            "required": ["order_id"],
        },
    },
    {
        "name": "verify_pricing",
        "description": "Verify that PO line item prices match contract pricing for the customer. Flags discrepancies.",
        "input_schema": {
            "type": "object",
            "properties": {"order_id": {"type": "string", "description": "The PO order ID"}},
            "required": ["order_id"],
        },
    },
]


def validate_order(order_id: str) -> dict:
    """Validate order completeness."""
    # TODO: Implement
    # 1. Look up order in ORDERS
    # 2. Check: items non-empty, each item has valid SKU in any warehouse, qty > 0
    # 3. Return {"valid": bool, "errors": [...], "order_summary": {...}}
    pass


def check_inventory(order_id: str) -> dict:
    """Check inventory across warehouses."""
    # TODO: Implement
    # 1. For each item in the order, check stock in each warehouse
    # 2. Return per-SKU availability: {"sku": {"WH-EAST": qty, "WH-CENTRAL": qty, ...}, "total": qty, "needed": qty}
    pass


def verify_pricing(order_id: str) -> dict:
    """Verify PO prices against contracts."""
    # TODO: Implement
    # 1. Look up customer contract in CONTRACT_PRICING
    # 2. Compare each line item unit_price to contract price
    # 3. Flag discrepancies
    # 4. Return {"verified": bool, "discrepancies": [...]}
    pass


TOOL_HANDLERS = {
    "validate_order": lambda args: validate_order(**args),
    "check_inventory": lambda args: check_inventory(**args),
    "verify_pricing": lambda args: verify_pricing(**args),
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


class OrderIntakeAgent(BaseAgent):
    name = "OrderIntakeAgent"
    tool_schemas = TOOL_SCHEMAS

    system_prompt = """You are the Order Intake Agent for a B2B ecommerce pipeline.
Validate incoming purchase orders, check inventory, and verify pricing.

You MUST:
1. validate_order — check completeness
2. check_inventory — verify stock availability
3. verify_pricing — compare to contract rates

Flag any issues for downstream agents."""

    def execute_tool(self, tool_name: str, tool_input: dict) -> str:
        return execute_tool(tool_name, tool_input)

    def build_user_message(self, state: PipelineState) -> str:
        o = state.raw_order
        return (
            f"Process order {o.get('order_id')}:\n"
            f"Customer: {o.get('customer_name')} ({o.get('customer_id')})\n"
            f"Items: {json.dumps(o.get('items', []))}\n"
            f"SLA Tier: {o.get('sla_tier')}\n"
            f"Requested Delivery: {o.get('requested_delivery')}"
        )

    def run(self, state: PipelineState) -> PipelineState:
        # TODO: Implement ReAct loop (same pattern as Domain A agents)
        return state

    def update_state(self, state: PipelineState, result_text: str) -> PipelineState:
        # TODO: Populate state.intake fields
        return state
