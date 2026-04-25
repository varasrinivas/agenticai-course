"""
B2B Ecommerce Order Status Bot — Tool Definitions (SOLUTION)
===============================================================
Complete implementation of the get_order_status tool.
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
    """
    # Normalize the PO number (strip whitespace, uppercase)
    po_number = po_number.strip().upper()

    # Look up the record
    record = ORDER_RECORDS.get(po_number)

    if record is None:
        return {
            "error": f"No order found for PO number '{po_number}'.",
            "suggestion": (
                "Please verify the PO number format (PO-YYYY-NNNN) "
                "and try again. If this is a recent order, it may not "
                "have been entered into the system yet."
            ),
        }

    return record
