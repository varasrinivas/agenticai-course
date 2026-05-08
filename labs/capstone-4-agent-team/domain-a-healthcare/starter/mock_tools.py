"""mock_tools.py — All agent tools for Capstone 4-A pipeline.

Four agents x 2-3 tools each = 11 tools total.
Each tool here is deterministic — no LLM calls. The pipeline.py
agent runner calls these via tool_use messages.

YOUR JOB: complete the TODOs in this file. Run `pytest test_pipeline.py
test_invalid_input_handling test_hipaa_guardrail_blocks_ssn_leak`
to validate as you go (those two tests don't need pipeline.py).
"""

import re
from datetime import datetime, timedelta

# ===================================================================
# INTAKE AGENT TOOLS
# ===================================================================

MEMBER_DB = {
    "MBR-555-1234": {"eligible": True, "plan": "Gold PPO",
                     "effective": "2024-01-01", "termination": None},
}

PROVIDER_DB = {
    "1234567890": {"verified": True, "name": "Dr. Sarah Johnson, MD",
                   "specialty": "Orthopedic Surgery",
                   "network": "in-network"},
}


def validate_auth_request(raw_request: dict) -> dict:
    """Validate and normalize an incoming auth request.

    Required fields: member_id, provider_npi, procedure_code,
    diagnosis_codes, clinical_notes.

    Returns:
      {validated: True, missing_fields: [], normalized_request: {...}}
        when all required fields are present (truthy)
      {validated: False, missing_fields: [...], normalized_request: None}
        otherwise.
    """
    # TODO: 1) Build the `required` list from the docstring above.
    # TODO: 2) Compute `missing` — fields that are absent OR empty.
    # TODO: 3) If `missing` is non-empty, return validated=False.
    # TODO: 4) Otherwise return validated=True with a normalized_request
    #         object containing procedure_code, diagnosis_codes,
    #         clinical_notes_summary (first 200 chars), urgency.
    raise NotImplementedError("Complete validate_auth_request")


def verify_member_eligibility(member_id: str, service_date: str) -> dict:
    """Look up member in MEMBER_DB. Return MEMBER_NOT_FOUND on miss."""
    # TODO: implement — see solution/mock_tools.py if stuck.
    raise NotImplementedError("Complete verify_member_eligibility")


def verify_provider(provider_npi: str) -> dict:
    """Look up provider in PROVIDER_DB. Return PROVIDER_NOT_FOUND on miss."""
    # TODO: implement.
    raise NotImplementedError("Complete verify_provider")


# ===================================================================
# CLINICAL CRITERIA AGENT TOOLS
# ===================================================================

POLICY_DB = {
    "27447": {
        "policy_id": "POLICY-ORTHO-TKA-2024",
        "criteria": [
            {"id": "C1",
             "description": "Severe OA (M17.11/M17.12) KL Grade III+",
             "required": True},
            {"id": "C2", "description": "6+ months conservative treatment",
             "required": True},
            {"id": "C3", "description": "WOMAC score > 50",
             "required": True},
            {"id": "C4", "description": "BMI < 40", "required": False},
        ],
        "effective_date": "2024-01-01",
    },
}

CRITERIA_EVIDENCE_MAP = {
    "C1": {"keywords": ["M17.11", "M17.12", "KL Grade III", "KL Grade IV",
                        "osteoarthritis", "severe"],
           "confidence_base": 0.90},
    "C2": {"keywords": ["PT", "physical therapy", "NSAIDs", "injection",
                        "conservative", "6 month", "8 month"],
           "confidence_base": 0.85},
    "C3": {"keywords": ["WOMAC", "score"], "confidence_base": 0.90},
    "C4": {"keywords": ["BMI"], "confidence_base": 0.95},
}


def fetch_clinical_policy(procedure_code: str, payer: str = None) -> dict:
    """Look up POLICY_DB. Return NO_POLICY_FOUND on miss."""
    # TODO: implement.
    raise NotImplementedError("Complete fetch_clinical_policy")


def evaluate_criterion(criterion_id: str, clinical_notes: str,
                       supporting_docs: list = None) -> dict:
    """Score a single criterion against clinical evidence.

    Steps:
      1. Look up `mapping = CRITERIA_EVIDENCE_MAP[criterion_id]`.
         Return CRITERION_NOT_FOUND if missing.
      2. Lower-case the clinical notes.
      3. Find which keywords appear in the notes.
      4. confidence = base * (matches / max(keywords*0.5, 1)),
         capped at 1.0.
      5. met = confidence > 0.5.
      6. Return {criterion_id, met, confidence, evidence, gaps}.
    """
    # TODO: implement using the steps above.
    raise NotImplementedError("Complete evaluate_criterion")


# ===================================================================
# DECISION AGENT TOOLS
# ===================================================================

def compute_decision_confidence(criteria_results: list,
                                network_status: str,
                                benefit_summary: dict) -> dict:
    """Compute overall confidence + recommendation.

    Routing rules:
      all_met AND avg > 0.90    -> approve, no HITL
      all_met AND avg >= 0.70   -> approve, HITL=True
      not all_met AND avg<0.70  -> deny, no HITL
      not all_met AND avg>=0.70 -> request_info, HITL=True
      otherwise                 -> request_info, HITL=True

    Where:
      avg = mean of c['confidence'] across criteria_results
      all_met = every required-criterion has met=True
    """
    # TODO: implement.
    raise NotImplementedError("Complete compute_decision_confidence")


def submit_for_human_review(request_id: str, confidence_score: float,
                            criteria_evaluation: list,
                            preliminary_recommendation: str) -> dict:
    """Stub — production would push to a queue (e.g., Pub/Sub)."""
    return {"review_id": f"HR-{request_id}",
            "queue_position": 1,
            "estimated_wait": "5 minutes"}


def finalize_determination(request_id: str, determination: str,
                           rationale: str,
                           reviewer_override: dict = None) -> dict:
    """Issue a determination_id + appeal deadline (60 days)."""
    # TODO: implement using datetime / timedelta.
    raise NotImplementedError("Complete finalize_determination")


# ===================================================================
# COMMUNICATION AGENT TOOLS
# ===================================================================

LETTER_TEMPLATES = {
    "approve": ("Dear Provider,\n\n"
                "Authorization has been APPROVED.\n\n"
                "Please schedule the procedure at your convenience.\n\n"
                "Sincerely,\nClinical Authorization Team"),
    "deny": ("Dear Provider,\n\n"
             "Authorization has been DENIED.\n\n"
             "Appeal rights: You may appeal this decision within "
             "60 days.\n\n"
             "Sincerely,\nClinical Authorization Team"),
    "request_info": ("Dear Provider,\n\n"
                     "Additional information is required.\n\n"
                     "Please submit the missing documentation "
                     "within 14 days.\n\n"
                     "Sincerely,\nClinical Authorization Team"),
}


def draft_determination_letter(determination_id: str,
                               determination: str = "approve",
                               recipient_type: str = "provider",
                               language: str = "en") -> dict:
    """Render the right LETTER_TEMPLATES entry."""
    # TODO: implement.
    raise NotImplementedError("Complete draft_determination_letter")


def send_notification(letter_id: str, channel: str,
                      recipient: str) -> dict:
    """Stub send — production would call Twilio/SendGrid/etc."""
    return {"notification_id": f"NOT-{letter_id}",
            "sent_at": datetime.now().isoformat(),
            "delivery_status": "delivered",
            "channel": channel}


# ── Output guardrail — Agent 4 calls this BEFORE sending ──────────
SSN_PATTERN = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
DOB_PATTERN = re.compile(
    r"\b(0?[1-9]|1[0-2])[/-](0?[1-9]|[12]\d|3[01])[/-]((19|20)\d{2})\b"
)


def check_hipaa_compliance(letter_text: str,
                           determination_type: str) -> dict:
    """Output guardrail — flag PII leakage and missing keywords.

    Checks (each adds an issue string, never silently rewrites
    semantic content):
      1. PII: SSN pattern -> add 'PII_LEAK: SSN ...' and replace
         the SSN with '[redacted-ssn]' in `redacted_text`.
         DOB pattern -> add 'PII_LEAK: DOB ...' and replace with
         '[redacted-dob]'.
      2. Determination keywords:
         - approve: body must contain 'approved'
         - deny: body must contain 'appeal'
         - request_info: body must contain one of
           'additional information' / 'missing' / 'submit'
      3. Format:
         - Must START with 'Dear' (case-insensitive)
         - Must contain 'Sincerely' or 'Regards' (case-insensitive)

    Returns: {compliant: bool, issues: [str], redacted_text: str}
    """
    # TODO: implement using SSN_PATTERN / DOB_PATTERN above.
    raise NotImplementedError("Complete check_hipaa_compliance")
