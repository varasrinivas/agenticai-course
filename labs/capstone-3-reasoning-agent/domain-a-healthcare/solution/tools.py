"""
Healthcare Pre-Authorization Decision Support Agent — Tool Definitions (Solution)

Complete implementations of all five tools used by the ReAct agent.
"""

from mock_data import (
    CLINICAL_CRITERIA,
    PROVIDER_NETWORK,
    FACILITIES,
    BENEFIT_PLANS,
)

# ---------------------------------------------------------------------------
# Tool Schemas (Anthropic format)
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
# Tool Handler Functions
# ---------------------------------------------------------------------------

def lookup_clinical_criteria(cpt_code: str) -> dict:
    """Look up clinical criteria for a CPT code."""
    criteria = CLINICAL_CRITERIA.get(cpt_code)
    if not criteria:
        return {"error": f"No criteria found for CPT code {cpt_code}"}
    return criteria


def verify_diagnosis_match(cpt_code: str, submitted_diagnosis_codes: list) -> dict:
    """Verify submitted diagnoses against required diagnoses for a procedure."""
    criteria = CLINICAL_CRITERIA.get(cpt_code)
    if not criteria:
        return {"error": f"No criteria found for CPT code {cpt_code}"}

    required = set(criteria["required_diagnoses"])
    submitted = set(submitted_diagnosis_codes)
    matched = submitted & required
    unmatched = submitted - required

    details = {}
    for code in matched:
        details[code] = criteria["diagnosis_descriptions"].get(code, "Description not available")

    return {
        "match": len(matched) > 0,
        "matched_codes": sorted(matched),
        "unmatched_codes": sorted(unmatched),
        "required_codes": criteria["required_diagnoses"],
        "details": details,
        "procedure_name": criteria["procedure_name"],
    }


def check_network_status(provider_npi: str, facility_id: str, plan_id: str) -> dict:
    """Check network status for provider + facility under a given plan."""
    provider = PROVIDER_NETWORK.get(provider_npi)
    if not provider:
        return {"error": f"Provider {provider_npi} not found in network directory"}

    facility = FACILITIES.get(facility_id)
    if not facility:
        return {"error": f"Facility {facility_id} not found"}

    plan = BENEFIT_PLANS.get(plan_id)
    if not plan:
        return {"error": f"Plan {plan_id} not found"}

    provider_in_network = provider["network_status"] == "in_network"
    facility_in_network = facility["network_status"] == "in_network"

    if plan["plan_type"] == "HMO" and (not provider_in_network or not facility_in_network):
        combined_status = "not_covered"
        status_detail = (
            "HMO plan does not cover out-of-network services. "
            "Patient must use an in-network provider and facility."
        )
    elif not provider_in_network or not facility_in_network:
        combined_status = "out_of_network"
        oon_parts = []
        if not provider_in_network:
            oon_parts.append(f"Provider {provider['name']} is out-of-network")
        if not facility_in_network:
            oon_parts.append(f"Facility {facility['name']} is out-of-network")
        status_detail = ". ".join(oon_parts) + ". Higher cost sharing will apply."
    else:
        combined_status = "in_network"
        status_detail = "Both provider and facility are in-network."

    return {
        "combined_status": combined_status,
        "status_detail": status_detail,
        "provider": {
            "npi": provider["npi"],
            "name": provider["name"],
            "specialty": provider["specialty"],
            "network_status": provider["network_status"],
            "network_tier": provider["network_tier"],
            "board_certified": provider["board_certified"],
            "quality_score": provider["quality_score"],
        },
        "facility": {
            "id": facility["id"],
            "name": facility["name"],
            "network_status": facility["network_status"],
            "type": facility["type"],
        },
        "plan_type": plan["plan_type"],
    }


def get_benefit_summary(plan_id: str, procedure_category: str) -> dict:
    """Get benefit plan summary for a procedure category."""
    plan = BENEFIT_PLANS.get(plan_id)
    if not plan:
        return {"error": f"Plan {plan_id} not found"}

    is_covered = procedure_category in plan["covered_categories"]
    is_excluded = procedure_category in plan["excluded_categories"]

    remaining_deductible_in = max(
        0, plan["in_network_deductible"] - plan["in_network_deductible_met"]
    )
    remaining_oop_in = max(
        0, plan["in_network_oop_max"] - plan["current_oop_spent"]
    )

    result = {
        "plan_name": plan["plan_name"],
        "plan_type": plan["plan_type"],
        "category_covered": is_covered,
        "category_excluded": is_excluded,
        "in_network": {
            "deductible": plan["in_network_deductible"],
            "deductible_met": plan["in_network_deductible_met"],
            "remaining_deductible": remaining_deductible_in,
            "coinsurance": f"{int(plan['in_network_coinsurance'] * 100)}%",
            "oop_max": plan["in_network_oop_max"],
            "current_oop_spent": plan["current_oop_spent"],
            "remaining_oop": remaining_oop_in,
        },
        "pre_auth_required": plan["pre_auth_required"],
        "notes": plan["notes"],
    }

    if plan["plan_type"] == "PPO" and plan.get("out_of_network_deductible"):
        remaining_deductible_oon = max(
            0, plan["out_of_network_deductible"] - plan["out_of_network_deductible_met"]
        )
        result["out_of_network"] = {
            "deductible": plan["out_of_network_deductible"],
            "deductible_met": plan["out_of_network_deductible_met"],
            "remaining_deductible": remaining_deductible_oon,
            "coinsurance": f"{int(plan['out_of_network_coinsurance'] * 100)}%",
            "oop_max": plan["out_of_network_oop_max"],
        }

    if plan.get("annual_max"):
        result["annual_max"] = plan["annual_max"]

    if is_excluded:
        result["exclusion_note"] = (
            f"'{procedure_category}' is explicitly excluded from this plan. "
            "Authorization cannot be granted under standard benefits."
        )

    return result


def generate_auth_recommendation(
    cpt_code: str,
    diagnosis_match: bool,
    network_status: str,
    benefit_covered: bool,
    clinical_notes_summary: str,
) -> dict:
    """Generate a pre-authorization recommendation."""
    criteria = CLINICAL_CRITERIA.get(cpt_code, {})
    peer_review_threshold = criteria.get("peer_review_threshold", "auto_approve_if_all_criteria_met")

    # Determine recommendation
    if not benefit_covered:
        return {
            "recommendation": "DENIED",
            "reason": (
                "The requested procedure falls under a category that is explicitly excluded "
                "from the patient's benefit plan. Authorization cannot be granted."
            ),
            "conditions": [
                "Patient may appeal this decision",
                "Patient may request a plan exception through Medical Director review",
                "Patient is financially responsible for the full cost if they proceed",
            ],
            "peer_review_required": peer_review_threshold == "medical_director_review_required",
            "approval_validity_days": 0,
        }

    if network_status == "not_covered":
        return {
            "recommendation": "DENIED",
            "reason": (
                "The patient's HMO plan does not cover out-of-network services. "
                "The requested provider and/or facility is out-of-network."
            ),
            "conditions": [
                "Patient must select an in-network provider and facility",
                "Resubmit with in-network provider for re-evaluation",
                "Emergency exception may apply if clinically urgent",
            ],
            "peer_review_required": False,
            "approval_validity_days": 0,
        }

    if not diagnosis_match:
        return {
            "recommendation": "PENDED",
            "reason": (
                "The submitted diagnosis codes do not match the required diagnoses for "
                "this procedure. The request is being pended for peer clinical review."
            ),
            "conditions": [
                "Peer reviewer will evaluate clinical necessity",
                "Provider may submit additional documentation or corrected diagnosis codes",
                "Expected turnaround: 3-5 business days",
            ],
            "peer_review_required": True,
            "approval_validity_days": 0,
        }

    if network_status == "out_of_network":
        return {
            "recommendation": "APPROVED",
            "reason": (
                "Clinical criteria are met and diagnosis is verified. However, the provider "
                "and/or facility is out-of-network. The request is approved at out-of-network "
                "benefit levels."
            ),
            "conditions": [
                "Out-of-network cost sharing applies (higher deductible and coinsurance)",
                "Patient should be informed of estimated out-of-pocket costs",
                "Balance billing may apply — facility is not contracted",
            ],
            "peer_review_required": False,
            "approval_validity_days": criteria.get("approval_validity_days", 60),
        }

    # All criteria met, in-network
    return {
        "recommendation": "APPROVED",
        "reason": (
            "All clinical criteria are met. Diagnosis matches required codes. "
            "Provider and facility are in-network. Benefit coverage is confirmed. "
            f"Clinical summary: {clinical_notes_summary}"
        ),
        "conditions": [
            f"Authorization valid for {criteria.get('approval_validity_days', 60)} days",
            "Pre-operative clearance must be completed before scheduling",
            "Facility must submit claim with this authorization number",
        ],
        "peer_review_required": False,
        "approval_validity_days": criteria.get("approval_validity_days", 60),
    }


# ---------------------------------------------------------------------------
# Dispatcher
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
