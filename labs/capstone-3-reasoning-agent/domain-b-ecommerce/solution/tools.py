"""
B2B Ecommerce Order Exception Resolution Agent — Tool Definitions (Solution)

Complete implementations of all six tools used by the ReAct agent.
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
            "events history, estimated delivery, and any service disruptions."
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
            "prices vs list prices, volume discount tiers, and contract status."
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
            "severity, affected lots, inspection status, and estimated resolution."
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
                "order_id": {"type": "string", "description": "The order ID"},
                "customer_name": {"type": "string", "description": "The customer's company name"},
                "contact_name": {"type": "string", "description": "The contact person's name"},
                "contact_email": {"type": "string", "description": "The contact person's email"},
                "exception_summary": {"type": "string", "description": "Brief summary of what happened"},
                "root_cause": {"type": "string", "description": "The identified root cause"},
                "resolution": {"type": "string", "description": "The proposed resolution with timeline"},
                "sla_impact": {"type": "string", "description": "Description of any SLA impact and credits"},
            },
            "required": [
                "order_id", "customer_name", "contact_name", "contact_email",
                "exception_summary", "root_cause", "resolution", "sla_impact",
            ],
        },
    },
]


# ---------------------------------------------------------------------------
# Tool Handler Functions
# ---------------------------------------------------------------------------

def get_order_details(order_id: str) -> dict:
    """Retrieve full order details."""
    order = ORDERS.get(order_id)
    if not order:
        return {"error": f"Order {order_id} not found"}
    return order


def query_warehouse_inventory(warehouse_id: str, sku: str) -> dict:
    """Query inventory for a SKU at a warehouse."""
    warehouse = WAREHOUSE_INVENTORY.get(warehouse_id)
    if not warehouse:
        return {"error": f"Warehouse {warehouse_id} not found"}

    inv = warehouse["inventory"].get(sku)
    if not inv:
        return {
            "error": f"SKU {sku} not found at warehouse {warehouse_id}",
            "warehouse_name": warehouse["name"],
        }

    return {
        "warehouse_id": warehouse_id,
        "warehouse_name": warehouse["name"],
        "location": warehouse["location"],
        "sku": sku,
        **inv,
    }


def track_shipment(tracking_number: str) -> dict:
    """Get tracking information for a shipment."""
    tracking = CARRIER_TRACKING.get(tracking_number)
    if not tracking:
        return {"error": f"Tracking number {tracking_number} not found"}
    return tracking


def get_contract_pricing(contract_id: str) -> dict:
    """Look up contract pricing agreement."""
    contract = CONTRACT_PRICING.get(contract_id)
    if not contract:
        return {"error": f"Contract {contract_id} not found"}
    return contract


def check_quality_hold_status(sku: str) -> dict:
    """Check for quality holds on a SKU."""
    holds = [
        hold for hold in QUALITY_HOLDS.values()
        if hold["sku"] == sku
    ]

    if not holds:
        return {"sku": sku, "holds": [], "status": "no_active_holds"}

    return {
        "sku": sku,
        "status": "holds_found",
        "hold_count": len(holds),
        "holds": holds,
    }


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
    body = f"""Dear {contact_name},

We are writing to provide you with an update regarding your order {order_id}.

ISSUE SUMMARY
{exception_summary}

ROOT CAUSE
{root_cause}

RESOLUTION & NEXT STEPS
{resolution}

SLA & CREDIT INFORMATION
{sla_impact}

We sincerely apologize for the inconvenience this has caused. Please do not hesitate to reach out if you have any questions or require further assistance.

Your dedicated account representative has been notified and will follow up within 24 hours to confirm resolution.

Best regards,
Order Management Team
B2B Industrial Supply Co."""

    return {
        "to": contact_email,
        "subject": f"Order Update: {order_id} — Action Required",
        "body": body,
        "status": "draft_ready",
        "order_id": order_id,
        "customer_name": customer_name,
    }


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
