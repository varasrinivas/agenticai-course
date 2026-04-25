"""
B2B Ecommerce Order Status Bot — Tool Definitions
====================================================
This module defines the tool schema and implementation for the
get_order_status tool.

YOUR TASK: Implement the get_order_status() function body.
"""

from mock_data import ORDER_RECORDS

# ──────────────────────────────────────────────────────────────
# Tool Schema (Anthropic format)
# ──────────────────────────────────────────────────────────────

TOOLS = [
    {
        "name": "get_order_status",
        "description": (
            "Look up the status of a B2B purchase order by PO number. "
            "Returns order status (processing, shipped, delivered, backordered, "
            "cancelled, partially-shipped, on-hold, returned), line items, "
            "tracking information, warehouse, carrier, and payment status. "
            "Use this tool when a user asks about a purchase order or PO number."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "po_number": {
                    "type": "string",
                    "description": (
                        "The purchase order number, formatted as PO-YYYY-NNNN "
                        "(e.g., PO-2024-8847)"
                    ),
                }
            },
            "required": ["po_number"],
        },
    }
]


# ──────────────────────────────────────────────────────────────
# Tool Implementation
# ──────────────────────────────────────────────────────────────

def get_order_status(po_number: str) -> dict:
    """
    Look up an order record by PO number.

    Args:
        po_number: The purchase order number (e.g., "PO-2024-8847")

    Returns:
        A dictionary with the order record, or an error message
        if the PO number is not found.

    TODO: Implement this function.
    - Look up the po_number in ORDER_RECORDS
    - If found, return the record
    - If not found, return a dict with an "error" key and a helpful message
    """
    # TODO: Implement this function
    pass
