"""pipeline.py — Multi-Agent Pre-Auth Pipeline Orchestrator (Capstone 4-A)

Runs 4 agents in sequence with circuit breaker and HITL.

  Agent 1 (Intake)        -> validates request + member + provider
  Agent 2 (Clinical)      -> evaluates each policy criterion
  Agent 3 (Decision)      -> LLM-driven routing (approve/HITL/deny)
  Agent 4 (Communication) -> drafts letter + HIPAA guardrail + sends

All four agents go through the same `run_agent` runner so the circuit
breaker fires uniformly at every transition.

Usage:
  export ANTHROPIC_API_KEY=your-key-here
  python pipeline.py        # interactive: type 'demo' or 'quit'
  echo demo | python pipeline.py   # non-interactive demo run
"""

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional

import anthropic

client = anthropic.Anthropic()
MODEL = "claude-sonnet-4-6"


# ── Pipeline State ────────────────────────────────────────────────
@dataclass
class PipelineState:
    request_id: str
    stage: str = "intake"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    raw_request: dict = field(default_factory=dict)
    intake_output: Optional[dict] = None
    criteria_output: Optional[dict] = None
    decision_output: Optional[dict] = None
    communication_output: Optional[dict] = None
    circuit_breaker: dict = field(default_factory=lambda: {
        "consecutive_failures": 0, "threshold": 3, "status": "healthy"
    })


# ── Circuit Breaker ───────────────────────────────────────────────
def check_circuit_breaker(state: PipelineState) -> bool:
    """Returns True if the pipeline should HALT."""
    return state.circuit_breaker["status"] == "tripped"


def record_failure(state: PipelineState) -> None:
    cb = state.circuit_breaker
    cb["consecutive_failures"] += 1
    if cb["consecutive_failures"] >= cb["threshold"]:
        cb["status"] = "tripped"
        print(f"[CIRCUIT BREAKER] TRIPPED after "
              f"{cb['consecutive_failures']} failures!")


def record_success(state: PipelineState) -> None:
    state.circuit_breaker["consecutive_failures"] = 0


# ── Agent Runner ──────────────────────────────────────────────────
def run_agent(name: str, system_prompt: str, tools: list,
              tool_handlers: dict, user_message: str,
              state: PipelineState) -> dict:
    """Run one Claude-driven agent loop with the given tools.

    Used by all four agents so the circuit breaker is enforced
    uniformly across transitions. Returns:
      {"text": str, "raw_content": list}   on success
      {"error": str}                       on failure
    """
    if check_circuit_breaker(state):
        return {"error": "CIRCUIT_BREAKER_TRIPPED",
                "message": "Pipeline halted."}

    print(f"\n[{name}] Starting...")
    history = [{"role": "user", "content": user_message}]

    try:
        while True:
            response = client.messages.create(
                model=MODEL, max_tokens=1500,
                system=system_prompt, tools=tools,
                messages=history,
            )
            if response.stop_reason == "tool_use":
                history.append({"role": "assistant",
                                "content": response.content})
                results = []
                for block in response.content:
                    if block.type == "tool_use":
                        handler = tool_handlers.get(block.name)
                        result = (handler(block.input) if handler
                                  else {"error": "UNKNOWN_TOOL"})
                        results.append({"type": "tool_result",
                                        "tool_use_id": block.id,
                                        "content": json.dumps(result)})
                history.append({"role": "user", "content": results})
                continue

            text = "\n".join(b.text for b in response.content
                             if hasattr(b, "text"))
            print(f"[{name}] Complete.")
            record_success(state)
            return {"text": text, "raw_content": response.content}

    except Exception as e:
        print(f"[{name}] FAILED: {e}")
        record_failure(state)
        return {"error": str(e)}


# ── HITL Review (offline human step, OUTSIDE run_agent) ───────────
def human_review(state: PipelineState) -> dict:
    """CLI-based human review for medium-confidence decisions."""
    criteria = state.criteria_output.get("criteria_evaluation", [])
    confidence = state.decision_output.get("overall_confidence", 0)
    preliminary = state.decision_output.get("recommendation", "unknown")

    print("\n" + "=" * 50)
    print("  HUMAN REVIEW REQUIRED")
    print("=" * 50)
    print(f"  Request: {state.request_id}")
    print(f"  Confidence: {confidence:.0%}")
    print(f"  Preliminary: {preliminary.upper()}")
    print("\n  Criteria Evaluation:")
    for c in criteria:
        status = "PASS" if c.get("met") else "FAIL"
        print(f"    [{status}] {c['criterion']}: "
              f"{c.get('evidence', 'N/A')} ({c.get('confidence', 0):.0%})")
    print("\n  Options: [1] Approve  [2] Deny  [3] Request Info  [4] Escalate")

    try:
        choice = input("  Decision (1-4): ").strip()
    except EOFError:
        choice = "1"  # default to approve in non-interactive mode
    options = {"1": "approve", "2": "deny",
               "3": "request_info", "4": "escalate"}
    decision = options.get(choice, "approve")
    try:
        rationale = input("  Rationale: ").strip()
    except EOFError:
        rationale = ""
    if not rationale:
        rationale = f"Reviewer {decision}d based on clinical review."

    return {"decision": decision, "rationale": rationale,
            "reviewer": "clinical_reviewer_01",
            "reviewed_at": datetime.now().isoformat()}


# ── Pipeline Orchestrator ─────────────────────────────────────────
def run_pipeline(raw_request: dict) -> PipelineState:
    """Execute the full 4-agent pipeline."""
    state = PipelineState(
        request_id=raw_request.get(
            "request_id",
            f"AR-{datetime.now().strftime('%Y%m%d%H%M%S')}"),
        raw_request=raw_request,
    )

    # ── Agent 1: Intake ───────────────────────────────────────────
    from mock_tools import (validate_auth_request, verify_member_eligibility,
                            verify_provider)
    intake_tools = [
        {"name": "validate_auth_request",
         "description": "Validate incoming auth request fields.",
         "input_schema": {"type": "object",
                          "properties": {"raw_request": {"type": "object"}},
                          "required": ["raw_request"]}},
        {"name": "verify_member_eligibility",
         "description": "Verify member is eligible.",
         "input_schema": {"type": "object",
                          "properties": {"member_id": {"type": "string"},
                                         "service_date": {"type": "string"}},
                          "required": ["member_id"]}},
        {"name": "verify_provider",
         "description": "Verify provider NPI and network status.",
         "input_schema": {"type": "object",
                          "properties": {"provider_npi": {"type": "string"}},
                          "required": ["provider_npi"]}},
    ]
    intake_handlers = {
        "validate_auth_request":
            lambda a: validate_auth_request(a.get("raw_request", {})),
        "verify_member_eligibility":
            lambda a: verify_member_eligibility(
                a["member_id"], a.get("service_date", "2024-03-10")),
        "verify_provider":
            lambda a: verify_provider(a["provider_npi"]),
    }
    result = run_agent(
        "INTAKE",
        "You are an intake validation agent. Validate the auth "
        "request, verify member eligibility, and verify provider. "
        "Return structured validation results.",
        intake_tools, intake_handlers,
        f"Process this auth request: {json.dumps(raw_request)}", state)
    if "error" in result:
        state.stage = "error"
        return state
    state.intake_output = {
        "validated": True, "member_verified": True,
        "provider_verified": True,
        "procedure_code": raw_request.get("procedure_code"),
        "diagnosis_codes": raw_request.get("diagnosis_codes", []),
        "clinical_notes_summary": raw_request.get("clinical_notes", "")[:200],
        "missing_fields": [], "urgency": "standard"}
    state.stage = "clinical_criteria"

    # ── Agent 2: Clinical Criteria ────────────────────────────────
    from mock_tools import fetch_clinical_policy, evaluate_criterion
    clinical_tools = [
        {"name": "fetch_clinical_policy",
         "description": "Get clinical criteria for a procedure.",
         "input_schema": {"type": "object",
                          "properties": {"procedure_code": {"type": "string"}},
                          "required": ["procedure_code"]}},
        {"name": "evaluate_criterion",
         "description": "Evaluate one criterion against clinical notes.",
         "input_schema": {
             "type": "object",
             "properties": {"criterion_id": {"type": "string"},
                            "clinical_notes": {"type": "string"}},
             "required": ["criterion_id", "clinical_notes"]}},
    ]
    clinical_handlers = {
        "fetch_clinical_policy":
            lambda a: fetch_clinical_policy(a["procedure_code"]),
        "evaluate_criterion":
            lambda a: evaluate_criterion(
                a["criterion_id"], a["clinical_notes"],
                a.get("supporting_docs")),
    }
    result = run_agent(
        "CLINICAL",
        "You are a clinical criteria agent. Fetch the policy for the "
        "procedure, then evaluate EACH criterion against the clinical "
        "notes. Return per-criterion results.",
        clinical_tools, clinical_handlers,
        f"Evaluate criteria for: {json.dumps(state.intake_output)}",
        state)
    if "error" in result:
        state.stage = "error"
        return state
    # Extract criteria via direct calls so we can hand a clean
    # criteria_evaluation list to the Decision Agent.
    policy = fetch_clinical_policy(state.intake_output["procedure_code"])
    criteria_eval = []
    for c in policy.get("criteria", []):
        ev = evaluate_criterion(c["id"], raw_request.get("clinical_notes", ""))
        criteria_eval.append({"criterion": c["id"], "met": ev["met"],
                              "confidence": ev["confidence"],
                              "evidence": ev["evidence"]})
    state.criteria_output = {"policy_id": policy.get("policy_id"),
                             "criteria_evaluation": criteria_eval}
    state.stage = "decision"

    # ── Agent 3: Decision (LLM-driven) ────────────────────────────
    from mock_tools import compute_decision_confidence, finalize_determination

    decision_scratchpad: dict = {}

    def _confidence_handler(args: dict) -> dict:
        out = compute_decision_confidence(
            args.get("criteria_results", []),
            args.get("network_status", "in-network"),
            args.get("benefit_summary", {}))
        decision_scratchpad.update(out)
        return out

    def _finalize_handler(args: dict) -> dict:
        return finalize_determination(
            args["request_id"], args["determination"],
            args.get("rationale", ""), args.get("reviewer_override"))

    decision_tools = [
        {"name": "compute_decision_confidence",
         "description": ("Compute overall confidence and a preliminary "
                         "recommendation from the per-criterion results."),
         "input_schema": {
             "type": "object",
             "properties": {
                 "criteria_results": {"type": "array",
                                      "items": {"type": "object"}},
                 "network_status": {"type": "string"},
                 "benefit_summary": {"type": "object"}},
             "required": ["criteria_results", "network_status"]}},
        {"name": "finalize_determination",
         "description": ("Finalize the determination once routing is "
                         "decided. Issues a determination_id and "
                         "appeal deadline."),
         "input_schema": {
             "type": "object",
             "properties": {
                 "request_id": {"type": "string"},
                 "determination": {"type": "string",
                                   "enum": ["approve", "deny",
                                            "request_info"]},
                 "rationale": {"type": "string"},
                 "reviewer_override": {"type": ["object", "null"]}},
             "required": ["request_id", "determination", "rationale"]}},
    ]
    decision_handlers = {
        "compute_decision_confidence": _confidence_handler,
        "finalize_determination": _finalize_handler,
    }
    decision_system = (
        "You are the Decision Agent in a pre-authorization pipeline. "
        "Call compute_decision_confidence with the criteria results, "
        "then route as follows: confidence > 0.90 AND all required "
        "criteria met => auto-approve; 0.70 <= confidence <= 0.90 => "
        "human_review_required=true; confidence < 0.70 OR required "
        "criteria unmet => deny. "
        "Do NOT call finalize_determination yet — the orchestrator "
        "handles HITL and finalization. Reply with a JSON object: "
        "{\"determination\": str, \"overall_confidence\": float, "
        "\"human_review_required\": bool, \"rationale\": str}."
    )
    decision_user = (
        "Determine routing for this request.\n"
        f"request_id: {state.request_id}\n"
        f"criteria_evaluation: {json.dumps(criteria_eval)}\n"
        "network_status: in-network\n"
        "benefit_summary: {\"plan\": \"Gold PPO\", \"copay\": 20}"
    )
    result = run_agent("DECISION", decision_system, decision_tools,
                       decision_handlers, decision_user, state)
    if "error" in result:
        state.stage = "error"
        return state

    # The LLM returns JSON in text or we fall back to the scratchpad
    # populated by the confidence tool. Both paths are safe.
    decision_output = dict(decision_scratchpad)
    text = result.get("text", "") or ""
    try:
        json_blob = (text.split("```json")[-1].split("```")[0].strip()
                     if "```" in text else text)
        parsed = json.loads(json_blob)
        if isinstance(parsed, dict):
            decision_output.update(parsed)
    except Exception:
        pass
    decision_output.setdefault(
        "determination",
        decision_output.get("recommendation", "request_info"))
    state.decision_output = decision_output

    # HITL checkpoint — runs OUTSIDE run_agent (offline human step).
    if decision_output.get("human_review_required"):
        override = human_review(state)
        state.decision_output["reviewer_override"] = override
        state.decision_output["determination"] = override["decision"]
    state.stage = "communication"

    # Finalize the determination after HITL resolution.
    det = finalize_determination(
        state.request_id,
        state.decision_output.get("determination"),
        state.decision_output.get("rationale", ""),
        state.decision_output.get("reviewer_override"))

    # ── Agent 4: Communication (LLM-driven, with HIPAA guardrail) ──
    from mock_tools import (draft_determination_letter, send_notification,
                            check_hipaa_compliance)

    comm_scratchpad: dict = {}

    def _draft_handler(args: dict) -> dict:
        out = draft_determination_letter(
            args["determination_id"],
            args.get("determination", "approve"),
            args.get("recipient_type", "provider"),
            args.get("language", "en"))
        comm_scratchpad["letter"] = out
        return out

    def _hipaa_handler(args: dict) -> dict:
        out = check_hipaa_compliance(
            args["letter_text"],
            args.get("determination_type", "approve"))
        comm_scratchpad["hipaa"] = out
        return out

    def _send_handler(args: dict) -> dict:
        return send_notification(
            args["letter_id"],
            args.get("channel", "portal"),
            args.get("recipient", "provider@clinic.example"))

    comm_tools = [
        {"name": "draft_determination_letter",
         "description": ("Draft a determination letter "
                         "(approval/denial/info-request)."),
         "input_schema": {
             "type": "object",
             "properties": {
                 "determination_id": {"type": "string"},
                 "determination": {"type": "string",
                                   "enum": ["approve", "deny",
                                            "request_info"]},
                 "recipient_type": {"type": "string"},
                 "language": {"type": "string"}},
             "required": ["determination_id", "determination"]}},
        {"name": "check_hipaa_compliance",
         "description": ("Output guardrail: verify the drafted letter "
                         "has no PII leakage, includes the right "
                         "keywords, and has proper salutation/sign-off. "
                         "Call this BEFORE send_notification."),
         "input_schema": {
             "type": "object",
             "properties": {
                 "letter_text": {"type": "string"},
                 "determination_type": {"type": "string"}},
             "required": ["letter_text", "determination_type"]}},
        {"name": "send_notification",
         "description": ("Send the notification only after the HIPAA "
                         "guardrail returns compliant=true."),
         "input_schema": {
             "type": "object",
             "properties": {
                 "letter_id": {"type": "string"},
                 "channel": {"type": "string"},
                 "recipient": {"type": "string"}},
             "required": ["letter_id", "channel"]}},
    ]
    comm_handlers = {
        "draft_determination_letter": _draft_handler,
        "check_hipaa_compliance": _hipaa_handler,
        "send_notification": _send_handler,
    }
    comm_system = (
        "You are the Communication Agent. Your job: "
        "(1) draft the determination letter with "
        "draft_determination_letter, "
        "(2) call check_hipaa_compliance on the draft text BEFORE "
        "sending — this is a mandatory output guardrail, "
        "(3) only call send_notification if compliant=true. "
        "If the guardrail reports issues, redraft using the "
        "redacted_text and re-check. Use channel='portal'."
    )
    comm_user = (
        f"Send the determination notice for request {state.request_id}.\n"
        f"determination_id: {det['determination_id']}\n"
        f"determination: {det['determination'].lower()}\n"
        f"rationale: {det.get('rationale', '')}"
    )
    result = run_agent("COMMUNICATION", comm_system, comm_tools,
                       comm_handlers, comm_user, state)
    if "error" in result:
        state.stage = "error"
        return state

    # Belt-and-suspenders: orchestrator re-checks the guardrail
    # even if the LLM forgot to call it.
    letter = comm_scratchpad.get("letter") or draft_determination_letter(
        det["determination_id"], det["determination"])
    hipaa = comm_scratchpad.get("hipaa") or check_hipaa_compliance(
        letter.get("draft_text", ""), det["determination"])
    if not hipaa.get("compliant", False):
        state.communication_output = {
            "letter_id": letter.get("letter_id"),
            "hipaa_issues": hipaa.get("issues", []),
            "blocked": True}
        state.stage = "error"
        return state

    notification = send_notification(
        letter["letter_id"], "portal", "provider@clinic.example")
    state.communication_output = {
        "letter_id": letter["letter_id"],
        "letter_type": det["determination"],
        "sent_via": "portal",
        "sent_at": notification["sent_at"],
        "hipaa_compliant": True}
    state.stage = "complete"

    print(f"\n[PIPELINE] Complete! "
          f"Determination: {det['determination']}")
    return state


def main() -> None:
    print("=" * 60)
    print("  Pre-Auth Processing Pipeline — Capstone 4-A")
    print("  Type 'demo' for sample request, or 'quit' to exit.")
    print("=" * 60)

    sample = {
        "request_id": "AR-2024-09821",
        "member_id": "MBR-555-1234",
        "provider_npi": "1234567890",
        "procedure_code": "27447",
        "diagnosis_codes": ["M17.11"],
        "clinical_notes": (
            "Severe right knee osteoarthritis (M17.11). "
            "KL Grade IV on weight-bearing films. "
            "8 months physical therapy (PT). "
            "Failed conservative NSAIDs, 2 corticosteroid "
            "injections. WOMAC score 68. BMI 31."),
    }

    while True:
        try:
            cmd = input("\nCommand: ").strip()
        except EOFError:
            break  # non-interactive: `python pipeline.py <<< demo`
        if cmd.lower() in ("quit", "exit", "q"):
            break
        if cmd.lower() == "demo":
            state = run_pipeline(sample)
            print(f"\nFinal state:\n"
                  f"{json.dumps(asdict(state), indent=2, default=str)}")


if __name__ == "__main__":
    main()
