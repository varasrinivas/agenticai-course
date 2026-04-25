"""
Healthcare Pre-Auth Status Checker — Tool Definitions (SOLUTION)
===================================================================
Complete implementation of the get_preauth_status tool.
"""

from mock_data import PREAUTH_RECORDS

# ──────────────────────────────────────────────────────────────
# Tool Schema (Anthropic format)
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
    """
    # Normalize the reference ID (strip whitespace, uppercase)
    reference_id = reference_id.strip().upper()

    # Look up the record
    record = PREAUTH_RECORDS.get(reference_id)

    if record is None:
        return {
            "error": f"No pre-authorization found for reference ID '{reference_id}'.",
            "suggestion": (
                "Please verify the reference ID format (PA-YYYY-NNNNN) "
                "and try again. If the issue persists, contact the payer "
                "directly for assistance."
            ),
        }

    return record
