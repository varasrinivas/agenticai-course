"""
Healthcare Pre-Authorization Decision Support Agent — Tool Definitions (Starter)

This file defines:
1. TOOL_SCHEMAS — Anthropic tool schemas sent to the Claude API
2. Tool handler functions — implementations that look up mock data

YOUR TASK: Complete the TODO sections in each tool function.
The schemas are already complete — do not modify them.
"""

from mock_data import (
    CLINICAL_CRITERIA,
    PROVIDER_NETWORK,
    FACILITIES,
    BENEFIT_PLANS,
    SAMPLE_REQUESTS,
)

# ---------------------------------------------------------------------------
# Tool Schemas (Anthropic format) — these are sent to the API as-is
# ---------------------------------------------------------------------------
TOOL_SCHEMAS = [
    {
        "name": "lookup_clinical_criteria",
        "description": (
            "Look up the clinical criteria required for pre-authorization of a specific "
            "procedure. Returns the required diagnoses, clinical criteria checklist, "
            "required documentation, and approval validity period. Use this FIRST to "
            "understand what is needed for the requested procedure."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "cpt_code": {
                    "type": "string",
                    "description": "The CPT procedure code to look up (e.g., '27447' for Total Knee Arthroplasty)",
                }
            },
            "required": ["cpt_code"],
        },
    },
    {
        "name": "verify_diagnosis_match",
        "description": (
            "Verify whether the submitted diagnosis code(s) match the required diagnoses "
            "for the requested procedure. Returns match status and details about each "
            "submitted diagnosis. Use this AFTER looking up clinical criteria."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "cpt_code": {
                    "type": "string",
                    "description": "The CPT procedure code",
                },
                "submitted_diagnosis_codes": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of ICD-10 diagnosis codes submitted with the request",
                },
            },
            "required": ["cpt_code", "submitted_diagnosis_codes"],
        },
    },
    {
        "name": "check_network_status",
        "description": (
            "Check whether a provider and facility are in-network for the patient's plan. "
            "Returns network status, tier, and implications for patient cost sharing. "
            "This is critical for HMO plans where out-of-network is not covered."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "provider_npi": {
                    "type": "string",
                    "description": "The provider's NPI number (e.g., 'NPI-1234567890')",
                },
                "facility_id": {
                    "type": "string",
                    "description": "The facility ID (e.g., 'FAC-001')",
                },
                "plan_id": {
                    "type": "string",
                    "description": "The patient's benefit plan ID",
                },
            },
            "required": ["provider_npi", "facility_id", "plan_id"],
        },
    },
    {
        "name": "get_benefit_summary",
        "description": (
            "Retrieve the patient's benefit plan summary including deductible status, "
            "coinsurance rates, out-of-pocket maximum, and whether the procedure category "
            "is covered. Use this to determine the patient's financial responsibility."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "plan_id": {
                    "type": "string",
                    "description": "The patient's benefit plan ID",
                },
                "procedure_category": {
                    "type": "string",
                    "description": "The category of the procedure (e.g., 'Orthopedic Surgery')",
                },
            },
            "required": ["plan_id", "procedure_category"],
        },
    },
    {
        "name": "generate_auth_recommendation",
        "description": (
            "Generate a pre-authorization recommendation based on all gathered information. "
            "Provide a structured recommendation with approval/denial/pend status and "
            "justification. Use this as the FINAL step after gathering all evidence."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "cpt_code": {
                    "type": "string",
                    "description": "The CPT procedure code",
                },
                "diagnosis_match": {
                    "type": "boolean",
                    "description": "Whether the diagnosis codes match the required criteria",
                },
                "network_status": {
                    "type": "string",
                    "enum": ["in_network", "out_of_network", "not_covered"],
                    "description": "The provider/facility network status",
                },
                "benefit_covered": {
                    "type": "boolean",
                    "description": "Whether the procedure category is covered by the plan",
                },
                "clinical_notes_summary": {
                    "type": "string",
                    "description": "Brief summary of relevant clinical notes and whether criteria appear to be met",
                },
            },
            "required": [
                "cpt_code",
                "diagnosis_match",
                "network_status",
                "benefit_covered",
                "clinical_notes_summary",
            ],
        },
    },
]


# ---------------------------------------------------------------------------
# Tool Handler Functions — complete the TODOs
# ---------------------------------------------------------------------------

def lookup_clinical_criteria(cpt_code: str) -> dict:
    """Look up clinical criteria for a CPT code."""
    # TODO: Look up the cpt_code in CLINICAL_CRITERIA
    # If found, return the full criteria entry
    # If not found, return {"error": f"No criteria found for CPT code {cpt_code}"}
    pass


def verify_diagnosis_match(cpt_code: str, submitted_diagnosis_codes: list) -> dict:
    """Verify submitted diagnoses against required diagnoses for a procedure."""
    # TODO:
    # 1. Look up the criteria for the cpt_code
    # 2. Compare submitted_diagnosis_codes against criteria["required_diagnoses"]
    # 3. Return a dict with:
    #    - "match": True/False (at least one submitted code is in the required list)
    #    - "matched_codes": list of codes that match
    #    - "unmatched_codes": list of submitted codes that do NOT match
    #    - "required_codes": the full list of valid diagnosis codes
    #    - "details": description of each matched code
    pass


def check_network_status(provider_npi: str, facility_id: str, plan_id: str) -> dict:
    """Check network status for provider + facility under a given plan."""
    # TODO:
    # 1. Look up the provider in PROVIDER_NETWORK
    # 2. Look up the facility in FACILITIES
    # 3. Look up the plan in BENEFIT_PLANS
    # 4. Determine combined network status:
    #    - If plan is HMO and provider/facility is out_of_network → "not_covered"
    #    - If provider OR facility is out_of_network (PPO) → "out_of_network"
    #    - Otherwise → "in_network"
    # 5. Return provider info, facility info, and the combined status
    pass


def get_benefit_summary(plan_id: str, procedure_category: str) -> dict:
    """Get benefit plan summary for a procedure category."""
    # TODO:
    # 1. Look up the plan in BENEFIT_PLANS
    # 2. Check if procedure_category is in covered_categories or excluded_categories
    # 3. Return plan details including:
    #    - plan name, type
    #    - deductible info and how much has been met
    #    - coinsurance rate
    #    - out-of-pocket max and current spend
    #    - whether the category is covered
    #    - any relevant notes
    pass


def generate_auth_recommendation(
    cpt_code: str,
    diagnosis_match: bool,
    network_status: str,
    benefit_covered: bool,
    clinical_notes_summary: str,
) -> dict:
    """Generate a pre-authorization recommendation."""
    # TODO:
    # Determine recommendation based on inputs:
    # - If benefit_covered is False → DENIED
    # - If network_status is "not_covered" → DENIED
    # - If diagnosis_match is False → PENDED for peer review
    # - If network_status is "out_of_network" → APPROVED with out-of-network notice
    # - If all criteria appear met → APPROVED
    # - Check the peer_review_threshold in CLINICAL_CRITERIA for special handling
    #
    # Return a dict with:
    # - "recommendation": "APPROVED" | "DENIED" | "PENDED"
    # - "reason": explanation
    # - "conditions": list of any conditions or next steps
    # - "peer_review_required": True/False
    # - "approval_validity_days": number of days (0 if denied)
    pass


# ---------------------------------------------------------------------------
# Dispatcher — maps tool name to handler function
# ---------------------------------------------------------------------------
TOOL_HANDLERS = {
    "lookup_clinical_criteria": lambda args: lookup_clinical_criteria(**args),
    "verify_diagnosis_match": lambda args: verify_diagnosis_match(**args),
    "check_network_status": lambda args: check_network_status(**args),
    "get_benefit_summary": lambda args: get_benefit_summary(**args),
    "generate_auth_recommendation": lambda args: generate_auth_recommendation(**args),
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
