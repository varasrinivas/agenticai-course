"""
Healthcare Pre-Auth Status Checker — Tool Definitions
=======================================================
This module defines the tool schema and implementation for the
get_preauth_status tool. The schema tells Claude what the tool does
and what parameters it accepts. The function body executes the actual lookup.

YOUR TASK: Implement the get_preauth_status() function body.
"""

from mock_data import PREAUTH_RECORDS

# ──────────────────────────────────────────────────────────────
# Tool Schema (Anthropic format)
# This is passed to client.messages.create(tools=[...])
# ──────────────────────────────────────────────────────────────

TOOLS = [
    {
        "name": "get_preauth_status",
        "description": (
            "Look up the status of a healthcare prior authorization request. "
            "Returns the authorization status (approved, pending, denied, "
            "info-requested, expired, partially-approved), patient info, "
            "CPT/ICD codes, clinical reviewer notes, and next steps. "
            "Use this tool when a user asks about a pre-auth, prior authorization, "
            "or PA reference number."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "reference_id": {
                    "type": "string",
                    "description": (
                        "The prior authorization reference ID, "
                        "formatted as PA-YYYY-NNNNN (e.g., PA-2024-00142)"
                    ),
                }
            },
            "required": ["reference_id"],
        },
    }
]


# ──────────────────────────────────────────────────────────────
# Tool Implementation
# ──────────────────────────────────────────────────────────────

def get_preauth_status(reference_id: str) -> dict:
    """
    Look up a pre-authorization record by reference ID.

    Args:
        reference_id: The PA reference ID (e.g., "PA-2024-00142")

    Returns:
        A dictionary with the pre-auth record, or an error message
        if the reference ID is not found.

    TODO: Implement this function.
    - Look up the reference_id in PREAUTH_RECORDS
    - If found, return the record
    - If not found, return a dict with an "error" key and a helpful message
    """
    # TODO: Implement this function
    pass
