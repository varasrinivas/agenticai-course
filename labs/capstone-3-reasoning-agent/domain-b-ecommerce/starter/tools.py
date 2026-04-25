"""
B2B Ecommerce Order Exception Resolution Agent — Tool Definitions (Starter)

This file defines:
1. TOOL_SCHEMAS — Anthropic tool schemas sent to the Claude API
2. Tool handler functions — implementations that look up mock data

YOUR TASK: Complete the TODO sections in each tool function.
"""

from mock_data import (
    ORDERS,
    WAREHOUSE_INVENTORY,
    CARRIER_TRACKING,
    CONTRACT_PRICING,
    QUALITY_HOLDS,
)

# ---------------------------------------------------------------------------
# Tool Schemas (Anthropic format)
# ---------------------------------------------------------------------------
TOOL_SCHEMAS = [
    {
        "name": "get_order_details",
        "description": (
            "Retrieve full details for an order including line items, shipping info, "
            "exception type, customer data, and contract reference. Use this FIRST "
            "to understand the order and its exception."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {
                    "type": "string",
                    "description": "The order ID (e.g., 'ORD-2024-1847')",
                }
            },
            "required": ["order_id"],
        },
    },
    {
        "name": "query_warehouse_inventory",
        "description": (
            "Query current inventory levels at a specific warehouse for a given SKU. "
            "Returns available quantity, reserved quantity, hold status, reorder point, "
            "and lead time. Use this to check stock availability for fulfillment."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "warehouse_id": {
                    "type": "string",
                    "description": "The warehouse ID (e.g., 'WH-EAST')",
                },
                "sku": {
                    "type": "string",
                    "description": "The product SKU to check",
                },
            },
            "required": ["warehouse_id", "sku"],
        },
    },
    {
        "name": "track_shipment",
        "description": (
            "Get real-time tracking information for a shipment including status, "
            "events history, estimated delivery, and any service disruptions. "
            "Use this to understand shipping delays."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "tracking_number": {
                    "type": "string",
                    "description": "The carrier tracking number",
                }
            },
            "required": ["tracking_number"],
        },
    },
    {
        "name": "get_contract_pricing",
        "description": (
            "Look up the contract pricing agreement for a customer. Returns contracted "
            "prices vs list prices, volume discount tiers, and contract status. "
            "Use this to investigate pricing discrepancies."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "contract_id": {
                    "type": "string",
                    "description": "The contract ID (e.g., 'CTR-2024-0091')",
                }
            },
            "required": ["contract_id"],
        },
    },
    {
        "name": "check_quality_hold_status",
        "description": (
            "Check if a SKU has any active quality holds. Returns hold reason, "
            "severity, affected lots, inspection status, and estimated resolution. "
            "Use this when an order has a quality_hold exception."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "sku": {
                    "type": "string",
                    "description": "The product SKU to check for quality holds",
                }
            },
            "required": ["sku"],
        },
    },
    {
        "name": "draft_customer_notification",
        "description": (
            "Draft a professional customer notification email about the order exception. "
            "Include the root cause, impact, proposed resolution, and timeline. "
            "Use this as the FINAL step after determining root cause and resolution."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {
                    "type": "string",
                    "description": "The order ID",
                },
                "customer_name": {
                    "type": "string",
                    "description": "The customer's company name",
                },
                "contact_name": {
                    "type": "string",
                    "description": "The contact person's name",
                },
                "contact_email": {
                    "type": "string",
                    "description": "The contact person's email",
                },
                "exception_summary": {
                    "type": "string",
                    "description": "Brief summary of what happened",
                },
                "root_cause": {
                    "type": "string",
                    "description": "The identified root cause",
                },
                "resolution": {
                    "type": "string",
                    "description": "The proposed resolution with timeline",
                },
                "sla_impact": {
                    "type": "string",
                    "description": "Description of any SLA impact and credits if applicable",
                },
            },
            "required": [
                "order_id",
                "customer_name",
                "contact_name",
                "contact_email",
                "exception_summary",
                "root_cause",
                "resolution",
                "sla_impact",
            ],
        },
    },
]


# ---------------------------------------------------------------------------
# Tool Handler Functions — complete the TODOs
# ---------------------------------------------------------------------------

def get_order_details(order_id: str) -> dict:
    """Retrieve full order details."""
    # TODO: Look up order_id in ORDERS
    # If found, return the full order dict
    # If not found, return {"error": f"Order {order_id} not found"}
    pass


def query_warehouse_inventory(warehouse_id: str, sku: str) -> dict:
    """Query inventory for a SKU at a warehouse."""
    # TODO:
    # 1. Look up warehouse_id in WAREHOUSE_INVENTORY
    # 2. Look up sku in that warehouse's inventory
    # 3. Return the inventory entry with warehouse info
    # Handle cases: warehouse not found, SKU not found at that warehouse
    pass


def track_shipment(tracking_number: str) -> dict:
    """Get tracking information for a shipment."""
    # TODO: Look up tracking_number in CARRIER_TRACKING
    # If found, return tracking data
    # If not found, return {"error": f"Tracking number {tracking_number} not found"}
    pass


def get_contract_pricing(contract_id: str) -> dict:
    """Look up contract pricing agreement."""
    # TODO: Look up contract_id in CONTRACT_PRICING
    # If found, return contract data
    # If not found, return {"error": f"Contract {contract_id} not found"}
    pass


def check_quality_hold_status(sku: str) -> dict:
    """Check for quality holds on a SKU."""
    # TODO:
    # 1. Search QUALITY_HOLDS for any holds matching the given SKU
    # 2. Return a list of matching holds (there may be zero or multiple)
    # 3. If no holds found, return {"sku": sku, "holds": [], "status": "no_active_holds"}
    pass


def draft_customer_notification(
    order_id: str,
    customer_name: str,
    contact_name: str,
    contact_email: str,
    exception_summary: str,
    root_cause: str,
    resolution: str,
    sla_impact: str,
) -> dict:
    """Draft a customer notification email."""
    # TODO:
    # Compose a professional email notification dict with:
    # - "to": contact_email
    # - "subject": f"Order Update: {order_id} — Action Required"
    # - "body": A professional email including:
    #     - Greeting with contact_name
    #     - Exception summary
    #     - Root cause explanation
    #     - Proposed resolution with timeline
    #     - SLA impact / credit info
    #     - Closing with apology and next steps
    # - "status": "draft_ready"
    pass


# ---------------------------------------------------------------------------
# Dispatcher
# ---------------------------------------------------------------------------
TOOL_HANDLERS = {
    "get_order_details": lambda args: get_order_details(**args),
    "query_warehouse_inventory": lambda args: query_warehouse_inventory(**args),
    "track_shipment": lambda args: track_shipment(**args),
    "get_contract_pricing": lambda args: get_contract_pricing(**args),
    "check_quality_hold_status": lambda args: check_quality_hold_status(**args),
    "draft_customer_notification": lambda args: draft_customer_notification(**args),
}


def execute_tool(tool_name: str, tool_input: dict) -> str:
    """Execute a tool by name and return the result as a JSON string."""
    import json

    handler = TOOL_HANDLERS.get(tool_name)
    if not handler:
        return json.dumps({"error": f"Unknown tool: {tool_name}"})

    try:
        result = handler(tool_input)
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": f"Tool execution failed: {str(e)}"})
