"""mock_tools.py — All agent tools for Capstone 4-A pipeline.

Four agents x 2-3 tools each = 11 tools total.
Each agent has a focused tool set — no cross-agent tool access.

The agents in pipeline.py call these via the run_agent runner. The tools
themselves are deterministic (no LLM calls) so the unit tests run fast
and offline.
"""

import json
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
                   "specialty": "Orthopedic Surgery", "network": "in-network"},
}


def validate_auth_request(raw_request: dict) -> dict:
    """Validate and normalize an incoming auth request."""
    required = ["member_id", "provider_npi", "procedure_code",
                "diagnosis_codes", "clinical_notes"]
    missing = [f for f in required if f not in raw_request or not raw_request[f]]
    if missing:
        return {"validated": False, "missing_fields": missing,
                "normalized_request": None}
    return {
        "validated": True, "missing_fields": [],
        "normalized_request": {
            "procedure_code": raw_request["procedure_code"],
            "diagnosis_codes": raw_request["diagnosis_codes"],
            "clinical_notes_summary": raw_request["clinical_notes"][:200],
            "urgency": raw_request.get("urgency", "standard"),
        },
    }


def verify_member_eligibility(member_id: str, service_date: str) -> dict:
    member = MEMBER_DB.get(member_id)
    if not member:
        return {"error": "MEMBER_NOT_FOUND",
                "message": f"Member {member_id} not found."}
    return {**member, "member_id": member_id}


def verify_provider(provider_npi: str) -> dict:
    provider = PROVIDER_DB.get(provider_npi)
    if not provider:
        return {"error": "PROVIDER_NOT_FOUND",
                "message": f"NPI {provider_npi} not found."}
    return {**provider, "provider_npi": provider_npi}


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


def fetch_clinical_policy(procedure_code: str, payer: str = None) -> dict:
    policy = POLICY_DB.get(procedure_code)
    if not policy:
        return {"error": "NO_POLICY_FOUND",
                "message": f"No policy for CPT {procedure_code}."}
    return policy


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


def evaluate_criterion(criterion_id: str, clinical_notes: str,
                       supporting_docs: list = None) -> dict:
    """Evaluate a single criterion against clinical evidence."""
    mapping = CRITERIA_EVIDENCE_MAP.get(criterion_id)
    if not mapping:
        return {"error": "CRITERION_NOT_FOUND",
                "message": f"Unknown criterion: {criterion_id}"}
    notes_lower = clinical_notes.lower()
    matches = [kw for kw in mapping["keywords"] if kw.lower() in notes_lower]
    confidence = mapping["confidence_base"] * (
        len(matches) / max(len(mapping["keywords"]) * 0.5, 1))
    confidence = min(confidence, 1.0)
    met = confidence > 0.5
    gaps = [] if met else [f"Insufficient evidence for {criterion_id}"]
    evidence = (f"Found: {', '.join(matches)}" if matches
                else "No matching evidence")
    return {"criterion_id": criterion_id, "met": met,
            "confidence": round(confidence, 2),
            "evidence": evidence, "gaps": gaps}


# ===================================================================
# DECISION AGENT TOOLS
# ===================================================================

def compute_decision_confidence(criteria_results: list,
                                network_status: str,
                                benefit_summary: dict) -> dict:
    """Compute overall confidence and preliminary recommendation."""
    if not criteria_results:
        return {"error": "INCOMPLETE_INPUT",
                "message": "No criteria results."}
    avg_conf = sum(c.get("confidence", 0)
                   for c in criteria_results) / len(criteria_results)
    all_met = all(c.get("met", False) for c in criteria_results
                  if c.get("required", True))
    if all_met and avg_conf > 0.90:
        rec = "approve"
        human_review = False
    elif all_met and avg_conf >= 0.70:
        rec = "approve"
        human_review = True  # Medium confidence -> HITL
    elif not all_met:
        rec = "deny" if avg_conf < 0.70 else "request_info"
        human_review = avg_conf >= 0.70
    else:
        rec = "request_info"
        human_review = True
    return {"overall_confidence": round(avg_conf, 2),
            "recommendation": rec,
            "rationale": (f"Avg confidence {avg_conf:.0%}. "
                          f"Network: {network_status}."),
            "human_review_required": human_review}


def submit_for_human_review(request_id: str, confidence_score: float,
                            criteria_evaluation: list,
                            preliminary_recommendation: str) -> dict:
    return {"review_id": f"HR-{request_id}",
            "queue_position": 1,
            "estimated_wait": "5 minutes"}


def finalize_determination(request_id: str, determination: str,
                           rationale: str,
                           reviewer_override: dict = None) -> dict:
    return {"determination_id": f"DET-{request_id}",
            "determination": determination.upper(),
            "effective_date": datetime.now().isoformat(),
            "appeal_deadline": (datetime.now() + timedelta(days=60))
                .strftime("%Y-%m-%d"),
            "rationale": rationale,
            "reviewer_override": reviewer_override}


# ===================================================================
# COMMUNICATION AGENT TOOLS
# ===================================================================

LETTER_TEMPLATES = {
    "approve": ("Dear Provider,\n\n"
                "Authorization {det_id} has been APPROVED for {procedure}.\n\n"
                "Plan: {plan}\nMember copay: {copay}%\n\n"
                "Please schedule the procedure at your convenience.\n\n"
                "Sincerely,\nClinical Authorization Team"),
    "deny": ("Dear Provider,\n\n"
             "Authorization {det_id} has been DENIED for {procedure}.\n\n"
             "Rationale: {rationale}\n\n"
             "Appeal rights: You may appeal this decision within 60 days.\n"
             "To file an appeal, submit additional documentation to "
             "appeals@healthplan.example.\n\n"
             "Sincerely,\nClinical Authorization Team"),
    "request_info": ("Dear Provider,\n\n"
                     "Regarding authorization request {det_id} "
                     "for {procedure}:\n\n"
                     "Additional information is required:\n{gaps}\n\n"
                     "Please submit the requested documentation "
                     "within 14 days.\n\n"
                     "Sincerely,\nClinical Authorization Team"),
}


def draft_determination_letter(determination_id: str,
                               determination: str = "approve",
                               recipient_type: str = "provider",
                               language: str = "en") -> dict:
    """Draft letter using the correct template for the determination type."""
    template_key = determination.lower()
    template = LETTER_TEMPLATES.get(
        template_key, LETTER_TEMPLATES.get("request_info", ""))
    return {"letter_id": f"LTR-{determination_id}",
            "draft_text": template,
            "required_disclosures": ["Appeal rights",
                                     "Member cost share",
                                     "Effective date"]}


def send_notification(letter_id: str, channel: str,
                      recipient: str) -> dict:
    return {"notification_id": f"NOT-{letter_id}",
            "sent_at": datetime.now().isoformat(),
            "delivery_status": "delivered",
            "channel": channel}


# ── Output guardrail used by Agent 4 (Communication) ──────────────
SSN_PATTERN = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
DOB_PATTERN = re.compile(
    r"\b(0?[1-9]|1[0-2])[/-](0?[1-9]|[12]\d|3[01])[/-]((19|20)\d{2})\b"
)


def check_hipaa_compliance(letter_text: str,
                           determination_type: str) -> dict:
    """Output guardrail: verify a drafted letter is HIPAA-compliant.

    Checks performed:
      * PII leakage  - no raw SSN patterns, no full birthdates
      * Determination keywords - approvals say 'approved', denials
        include 'appeal' instructions, request_info letters list
        missing items
      * Salutation/sign-off - must start with 'Dear' and end with a
        sign-off ('Sincerely' or 'Regards')
    Returns: {"compliant": bool, "issues": [str], "redacted_text": str}
    """
    issues: list[str] = []
    redacted = letter_text or ""

    # 1) PII leakage — redact and flag
    if SSN_PATTERN.search(redacted):
        issues.append("PII_LEAK: SSN pattern detected in letter body")
        redacted = SSN_PATTERN.sub("[redacted-ssn]", redacted)
    if DOB_PATTERN.search(redacted):
        issues.append(
            "PII_LEAK: full date-of-birth detected (use [redacted])")
        redacted = DOB_PATTERN.sub("[redacted-dob]", redacted)

    # 2) Required keywords by determination type
    body_lower = redacted.lower()
    dtype = (determination_type or "").lower()
    if dtype in ("approve", "approval", "approved"):
        if "approved" not in body_lower:
            issues.append(
                "MISSING_KEYWORD: approval letter must say 'approved'")
    elif dtype in ("deny", "denial", "denied"):
        if "appeal" not in body_lower:
            issues.append("MISSING_KEYWORD: denial letter must "
                          "include appeal instructions")
    elif dtype in ("request_info", "info_request"):
        if not any(k in body_lower for k in
                   ("additional information", "missing", "submit")):
            issues.append("MISSING_KEYWORD: info-request letter "
                          "must list missing items")

    # 3) Salutation and sign-off
    stripped = redacted.strip()
    if not stripped.lower().startswith("dear"):
        issues.append("FORMAT: missing salutation ('Dear ...')")
    if "sincerely" not in body_lower and "regards" not in body_lower:
        issues.append(
            "FORMAT: missing sign-off ('Sincerely' or 'Regards')")

    return {"compliant": len(issues) == 0,
            "issues": issues,
            "redacted_text": redacted}
