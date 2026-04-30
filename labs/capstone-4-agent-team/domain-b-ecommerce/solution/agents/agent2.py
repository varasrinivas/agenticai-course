"""
Fulfillment Planning Agent (Agent 2) — B2B Ecommerce (Solution)
Includes HITL gate for split shipments.
"""

import json
from datetime import datetime, timedelta
from typing import Any
import anthropic
from agents import BaseAgent, PipelineState
from mock_data import ORDERS, INVENTORY, CARRIERS, SLA_RULES

MODEL = "claude-sonnet-4-6"
MAX_ITERATIONS = 10

TOOL_SCHEMAS = [
    {"name": "allocate_inventory", "description": "Allocate inventory from warehouses.", "input_schema": {"type": "object", "properties": {"order_id": {"type": "string"}, "inventory_status": {"type": "object"}}, "required": ["order_id", "inventory_status"]}},
    {"name": "select_warehouse", "description": "Select optimal warehouse for a SKU.", "input_schema": {"type": "object", "properties": {"order_id": {"type": "string"}, "sku": {"type": "string"}, "qty_needed": {"type": "integer"}}, "required": ["order_id", "sku", "qty_needed"]}},
    {"name": "calculate_shipping", "description": "Calculate shipping cost and ETA.", "input_schema": {"type": "object", "properties": {"order_id": {"type": "string"}, "warehouse_id": {"type": "string"}, "sla_tier": {"type": "string"}}, "required": ["order_id", "warehouse_id", "sla_tier"]}},
]


def allocate_inventory(order_id: str, inventory_status: dict) -> dict:
    allocations = []
    split_needed = False
    for sku, info in inventory_status.items():
        if isinstance(info, dict) and "by_warehouse" in info:
            needed = info.get("needed", 0)
            remaining = needed
            sku_allocs = []
            # Sort warehouses by stock descending
            sorted_whs = sorted(info["by_warehouse"].items(), key=lambda x: x[1], reverse=True)
            for wh_id, avail in sorted_whs:
                if remaining <= 0:
                    break
                alloc = min(remaining, avail)
                if alloc > 0:
                    sku_allocs.append({"warehouse_id": wh_id, "sku": sku, "allocated": alloc})
                    remaining -= alloc
            if len(sku_allocs) > 1:
                split_needed = True
            allocations.extend(sku_allocs)
    return {"allocations": allocations, "split_shipment": split_needed}


def select_warehouse(order_id: str, sku: str, qty_needed: int) -> dict:
    best = None
    best_qty = 0
    for wh_id, wh in INVENTORY.items():
        avail = wh["stock"].get(sku, 0)
        if avail >= qty_needed and (best is None or avail > best_qty):
            best = wh_id
            best_qty = avail
    if best:
        return {"warehouse_id": best, "available": best_qty, "can_fulfill": True}
    # Partial
    for wh_id, wh in INVENTORY.items():
        avail = wh["stock"].get(sku, 0)
        if avail > best_qty:
            best = wh_id
            best_qty = avail
    return {"warehouse_id": best or "NONE", "available": best_qty, "can_fulfill": False}


def calculate_shipping(order_id: str, warehouse_id: str, sla_tier: str) -> dict:
    sla = SLA_RULES.get(sla_tier, SLA_RULES["standard"])
    carrier_tier = sla["carrier_tier"]
    carrier = None
    for c in CARRIERS.values():
        if c["tier"] == carrier_tier:
            carrier = c
            break
    if not carrier:
        carrier = list(CARRIERS.values())[0]
    est_date = (datetime.now() + timedelta(days=carrier["avg_days"])).strftime("%Y-%m-%d")
    order = ORDERS.get(order_id, {})
    req_date = order.get("requested_delivery", est_date)
    feasible = est_date <= req_date
    return {"carrier": carrier["name"], "cost_per_lb": carrier["cost_per_lb"], "estimated_delivery": est_date, "sla_feasible": feasible}


TOOL_HANDLERS = {
    "allocate_inventory": lambda args: allocate_inventory(**args),
    "select_warehouse": lambda args: select_warehouse(**args),
    "calculate_shipping": lambda args: calculate_shipping(**args),
}


def execute_tool(tool_name, tool_input):
    handler = TOOL_HANDLERS.get(tool_name)
    if not handler:
        return json.dumps({"error": f"Unknown tool: {tool_name}"})
    try:
        return json.dumps(handler(tool_input), indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


class FulfillmentPlanningAgent(BaseAgent):
    name = "FulfillmentPlanningAgent"
    tool_schemas = TOOL_SCHEMAS
    system_prompt = "You are the Fulfillment Planning Agent. Allocate inventory, select warehouse, calculate shipping. Flag split shipments for HITL review."

    def execute_tool(self, tool_name, tool_input):
        return execute_tool(tool_name, tool_input)

    def build_user_message(self, state):
        return f"Plan fulfillment for {state.intake.order_id}:\nItems: {json.dumps(state.intake.items)}\nInventory: {json.dumps(state.intake.inventory_status)}\nSLA: {state.raw_order.get('sla_tier')}"

    def run(self, state):
        client = anthropic.Anthropic()
        messages = [{"role": "user", "content": self.build_user_message(state)}]
        print(f"\n[FulfillmentPlanningAgent] Starting...")
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

        # Populate state
        alloc = allocate_inventory(state.intake.order_id, state.intake.inventory_status)
        state.fulfillment.warehouse_allocations = alloc.get("allocations", [])
        state.fulfillment.split_shipment_needed = alloc.get("split_shipment", False)

        # HITL gate for split shipments
        if state.fulfillment.split_shipment_needed:
            print(f"\n{'!'*60}")
            print(f"  HITL: Split shipment required for {state.intake.order_id}")
            print(f"  Allocations: {json.dumps(state.fulfillment.warehouse_allocations, indent=2)}")
            print(f"{'!'*60}")
            try:
                choice = input("  Approve split shipment? (y/n): ").strip().lower()
            except EOFError:
                choice = "y"
            if choice != "y":
                state.halted = True
                state.halt_reason = "Split shipment rejected by reviewer"
                return state

        wh_id = state.fulfillment.warehouse_allocations[0]["warehouse_id"] if state.fulfillment.warehouse_allocations else "WH-CENTRAL"
        ship = calculate_shipping(state.intake.order_id, wh_id, state.raw_order.get("sla_tier", "standard"))
        state.fulfillment.selected_carrier = ship.get("carrier", "")
        state.fulfillment.estimated_shipping_cost = ship.get("cost_per_lb", 0)
        state.fulfillment.estimated_delivery_date = ship.get("estimated_delivery", "")
        state.fulfillment.sla_feasible = ship.get("sla_feasible", False)
        state.agent_trace.append({"agent": self.name, "split_shipment": state.fulfillment.split_shipment_needed, "sla_feasible": state.fulfillment.sla_feasible})
        return state

    def update_state(self, state, result_text):
        return state
