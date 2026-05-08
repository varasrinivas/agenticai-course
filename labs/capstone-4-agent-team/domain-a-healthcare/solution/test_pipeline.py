"""test_pipeline.py — 6 pytest test cases for Capstone 4-A pipeline.

Run:
  pytest test_pipeline.py -v

Each test exercises a different pipeline path WITHOUT making real API
calls. We call the mock tools and pipeline helpers directly.
"""

import pytest

from pipeline import (PipelineState, check_circuit_breaker,
                      record_failure, record_success)
from mock_tools import (
    validate_auth_request,
    verify_member_eligibility,
    fetch_clinical_policy,
    evaluate_criterion,
    compute_decision_confidence,
    finalize_determination,
    draft_determination_letter,
    send_notification,
    check_hipaa_compliance,
)

# ── Shared fixtures ───────────────────────────────────────────────

VALID_REQUEST = {
    "request_id": "AR-TEST-001",
    "member_id": "MBR-555-1234",
    "provider_npi": "1234567890",
    "procedure_code": "27447",
    "diagnosis_codes": ["M17.11"],
    "clinical_notes": (
        "Severe right knee osteoarthritis (M17.11). "
        "KL Grade IV on weight-bearing films. "
        "8 months physical therapy (PT). Failed conservative "
        "NSAIDs, 2 corticosteroid injections. "
        "WOMAC score 68. BMI 31."
    ),
}


# ── Test 1: Happy path — TKA approval (high confidence) ──────────

def test_high_confidence_auto_approve():
    """Full pipeline: all criteria met, confidence >90%, auto-approve."""
    # Step 1: Intake validation
    result = validate_auth_request(VALID_REQUEST)
    assert result["validated"] is True
    assert result["missing_fields"] == []

    # Step 2: Member + provider verification
    member = verify_member_eligibility("MBR-555-1234", "2024-03-10")
    assert member["eligible"] is True

    # Step 3: Clinical criteria evaluation
    policy = fetch_clinical_policy("27447")
    criteria_eval = []
    for c in policy["criteria"]:
        ev = evaluate_criterion(c["id"], VALID_REQUEST["clinical_notes"])
        criteria_eval.append(ev)

    # Step 4: Decision — expect auto-approve (no HITL)
    decision = compute_decision_confidence(
        criteria_eval, "in-network", {"plan": "Gold PPO", "copay": 20})
    assert decision["overall_confidence"] > 0.90, (
        f"Expected >0.90, got {decision['overall_confidence']}")
    assert decision["recommendation"] == "approve"
    assert decision["human_review_required"] is False

    # Step 5: Communication — letter drafted and sent
    det = finalize_determination(
        "AR-TEST-001", "approve", decision["rationale"])
    letter = draft_determination_letter(
        det["determination_id"], "APPROVE")
    notif = send_notification(letter["letter_id"], "portal",
                              "provider@test.example")
    assert notif["delivery_status"] == "delivered"


# ── Test 2: Denial — missing conservative treatment ──────────────

def test_denial_missing_conservative_treatment():
    """Sparse clinical notes -> low confidence -> deny."""
    sparse_notes = "Right knee pain. M17.11. BMI 31."
    policy = fetch_clinical_policy("27447")
    criteria_eval = []
    for c in policy["criteria"]:
        ev = evaluate_criterion(c["id"], sparse_notes)
        criteria_eval.append(ev)

    # C2 (conservative treatment) should fail — no PT/NSAID/injection
    c2 = next(e for e in criteria_eval if e["criterion_id"] == "C2")
    assert c2["met"] is False, (
        "C2 should fail without conservative treatment evidence")

    decision = compute_decision_confidence(
        criteria_eval, "in-network", {"plan": "Gold PPO", "copay": 20})
    assert decision["recommendation"] == "deny"


# ── Test 3: HITL escalation — borderline confidence (70-90%) ─────

def test_hitl_escalation_borderline_confidence():
    """Borderline notes produce 70-90% confidence -> HITL required."""
    borderline_notes = (
        "Right knee osteoarthritis M17.11. KL Grade III. "
        "3 months PT. WOMAC score 55. BMI 33."
    )
    policy = fetch_clinical_policy("27447")
    criteria_eval = []
    for c in policy["criteria"]:
        ev = evaluate_criterion(c["id"], borderline_notes)
        criteria_eval.append(ev)

    decision = compute_decision_confidence(
        criteria_eval, "in-network", {"plan": "Gold PPO", "copay": 20})
    assert decision["human_review_required"] is True, (
        f"Expected HITL for confidence "
        f"{decision['overall_confidence']}")


# ── Test 4: Circuit breaker trips after 3 consecutive failures ───

def test_circuit_breaker_trips():
    """Breaker transitions healthy -> tripped after 3 failures."""
    state = PipelineState(request_id="AR-TEST-CB")

    assert check_circuit_breaker(state) is False
    assert state.circuit_breaker["status"] == "healthy"

    # 2 failures — still healthy
    record_failure(state)
    record_failure(state)
    assert state.circuit_breaker["consecutive_failures"] == 2
    assert check_circuit_breaker(state) is False

    # 3rd failure — should trip
    record_failure(state)
    assert state.circuit_breaker["consecutive_failures"] == 3
    assert state.circuit_breaker["status"] == "tripped"
    assert check_circuit_breaker(state) is True

    # A success resets the counter (on a fresh state)
    state2 = PipelineState(request_id="AR-TEST-CB2")
    record_failure(state2)
    record_success(state2)
    assert state2.circuit_breaker["consecutive_failures"] == 0


# ── Test 5: Invalid input handling ───────────────────────────────

def test_invalid_input_handling():
    """Missing required fields are caught by intake validation."""
    # Completely empty request
    result = validate_auth_request({})
    assert result["validated"] is False
    assert "member_id" in result["missing_fields"]
    assert "procedure_code" in result["missing_fields"]
    assert result["normalized_request"] is None

    # Partial request — missing clinical_notes
    partial = {
        "member_id": "MBR-555-1234",
        "provider_npi": "1234567890",
        "procedure_code": "27447",
        "diagnosis_codes": ["M17.11"],
    }
    result = validate_auth_request(partial)
    assert result["validated"] is False
    assert "clinical_notes" in result["missing_fields"]

    # Unknown member
    member = verify_member_eligibility("MBR-UNKNOWN", "2024-03-10")
    assert "error" in member
    assert member["error"] == "MEMBER_NOT_FOUND"


# ── Test 6: HIPAA output guardrail flags SSN-leaking letter ──────

def test_hipaa_guardrail_blocks_ssn_leak():
    """check_hipaa_compliance flags SSN patterns + redacts text."""
    leaky = (
        "Dear Provider,\n\n"
        "Authorization for member SSN 123-45-6789 has been approved.\n\n"
        "Sincerely,\nClinical Authorization Team"
    )
    result = check_hipaa_compliance(leaky, "approve")

    assert result["compliant"] is False
    assert any("PII_LEAK" in i and "SSN" in i for i in result["issues"]), (
        f"Expected PII_LEAK SSN issue, got {result['issues']}")
    assert "123-45-6789" not in result["redacted_text"]
    assert "[redacted-ssn]" in result["redacted_text"]

    # A clean approval letter should pass
    clean = (
        "Dear Provider,\n\n"
        "Authorization has been approved for the procedure.\n\n"
        "Sincerely,\nClinical Authorization Team"
    )
    ok = check_hipaa_compliance(clean, "approve")
    assert ok["compliant"] is True, (
        f"Expected compliant=True, got issues={ok['issues']}")

    # A denial letter missing the word 'appeal' must be flagged
    bad_denial = ("Dear Provider,\n\nAuthorization is denied.\n\n"
                  "Sincerely,\nTeam")
    bd = check_hipaa_compliance(bad_denial, "deny")
    assert bd["compliant"] is False
    assert any("MISSING_KEYWORD" in i for i in bd["issues"])
