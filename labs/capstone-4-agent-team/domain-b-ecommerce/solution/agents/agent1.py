"""
Order Intake Agent (Agent 1) — B2B Ecommerce Order Pipeline (Solution)
"""

import json
from typing import Any
import anthropic
from agents import BaseAgent, PipelineState
from mock_data import ORDERS, INVENTORY, CONTRACT_PRICING

MODEL = "claude-sonnet-4-6"
MAX_ITERATIONS = 10

TOOL_SCHEMAS = [
    {"name": "validate_order", "description": "Validate PO for completeness.", "input_schema": {"type": "object", "properties": {"order_id": {"type": "string"}}, "required": ["order_id"]}},
    {"name": "check_inventory", "description": "Check stock across warehouses.", "input_schema": {"type": "object", "properties": {"order_id": {"type": "string"}}, "required": ["order_id"]}},
    {"name": "verify_pricing", "description": "Verify PO prices vs contracts.", "input_schema": {"type": "object", "properties": {"order_id": {"type": "string"}}, "required": ["order_id"]}},
]


def validate_order(order_id: str) -> dict:
    order = ORDERS.get(order_id)
    if not order:
        return {"valid": False, "errors": [f"Order {order_id} not found"]}
    errors = []
    if not order.get("items"):
        errors.append("No items in order")
    all_skus = set()
    for wh in INVENTORY.values():
        all_skus.update(wh["stock"].keys())
    for item in order.get("items", []):
        if item["sku"] not in all_skus:
            errors.append(f"Unknown SKU: {item['sku']}")
        if item.get("qty", 0) <= 0:
            errors.append(f"Invalid quantity for {item['sku']}: {item.get('qty')}")
    return {"valid": len(errors) == 0, "errors": errors, "order_id": order_id, "item_count": len(order.get("items", []))}


def check_inventory(order_id: str) -> dict:
    order = ORDERS.get(order_id)
    if not order:
        return {"error": f"Order {order_id} not found"}
    result = {}
    for item in order.get("items", []):
        sku = item["sku"]
        needed = item["qty"]
        by_wh = {}
        total = 0
        for wh_id, wh in INVENTORY.items():
            qty = wh["stock"].get(sku, 0)
            by_wh[wh_id] = qty
            total += qty
        result[sku] = {"by_warehouse": by_wh, "total_available": total, "needed": needed, "sufficient": total >= needed}
    return result


def verify_pricing(order_id: str) -> dict:
    order = ORDERS.get(order_id)
    if not order:
        return {"error": f"Order {order_id} not found"}
    contract = CONTRACT_PRICING.get(order.get("customer_id", ""))
    if not contract:
        return {"verified": True, "note": "No contract pricing — standard list prices apply", "discrepancies": []}
    discrepancies = []
    for item in order.get("items", []):
        contract_price = contract.get("contract_prices", {}).get(item["sku"])
        if contract_price is not None and abs(item["unit_price"] - contract_price) > 0.01:
            discrepancies.append({
                "sku": item["sku"],
                "po_price": item["unit_price"],
                "contract_price": contract_price,
                "difference": round(item["unit_price"] - contract_price, 2),
            })
    return {"verified": len(discrepancies) == 0, "discrepancies": discrepancies, "pricing_tier": contract.get("pricing_tier", "")}


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
        return json.dumps(handler(tool_input), indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


class OrderIntakeAgent(BaseAgent):
    name = "OrderIntakeAgent"
    tool_schemas = TOOL_SCHEMAS
    system_prompt = "You are the Order Intake Agent. Validate orders, check inventory, verify pricing. Call all 3 tools then summarize."

    def execute_tool(self, tool_name, tool_input):
        return execute_tool(tool_name, tool_input)

    def build_user_message(self, state):
        o = state.raw_order
        return f"Process order {o.get('order_id')}:\nCustomer: {o.get('customer_name')}\nItems: {json.dumps(o.get('items', []))}\nSLA: {o.get('sla_tier')}"

    def run(self, state):
        client = anthropic.Anthropic()
        messages = [{"role": "user", "content": self.build_user_message(state)}]
        print(f"\n[OrderIntakeAgent] Starting...")
        for step in range(1, MAX_ITERATIONS + 1):
            try:
                response = client.messages.create(model=MODEL, max_tokens=4096, system=self.system_prompt, tools=self.tool_schemas, messages=messages)
            except Exception as e:
                state.halted = True; state.halt_reason = str(e); return state
            tool_blocks = [b for b in response.content if b.type == "tool_use"]
            for b in response.content:
                if b.type == "text": print(f"  [THINK] {b.text[:150]}...")
                elif b.type == "tool_use": print(f"  [ACT] {b.name}")
            if response.stop_reason == "end_turn": break
            if tool_blocks:
                messages.append({"role": "assistant", "content": response.content})
                messages.append({"role": "user", "content": [{"type": "tool_result", "tool_use_id": b.id, "content": self.execute_tool(b.name, b.input)} for b in tool_blocks]})

        order = state.raw_order
        state.intake.order_id = order.get("order_id", "")
        state.intake.customer_id = order.get("customer_id", "")
        state.intake.customer_name = order.get("customer_name", "")
        state.intake.items = order.get("items", [])
        v = validate_order(order.get("order_id", ""))
        state.intake.validation_passed = v.get("valid", False)
        state.intake.validation_errors = v.get("errors", [])
        state.intake.inventory_status = check_inventory(order.get("order_id", ""))
        p = verify_pricing(order.get("order_id", ""))
        state.intake.pricing_verified = p.get("verified", False)
        state.intake.pricing_discrepancies = [d.get("sku", "") for d in p.get("discrepancies", [])]
        state.agent_trace.append({"agent": self.name, "validation_passed": state.intake.validation_passed})
        return state

    def update_state(self, state, result_text):
        return state
