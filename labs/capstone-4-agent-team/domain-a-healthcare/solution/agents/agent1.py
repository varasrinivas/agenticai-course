"""
Intake Agent (Agent 1) — Healthcare Pre-Auth Pipeline (Solution)

Fully implemented: validates requests, extracts clinical info, checks eligibility.
"""

import json
import re
import os
from typing import Any

import anthropic

from agents import BaseAgent, PipelineState
from mock_data import PREAUTH_REQUESTS, CLINICAL_CRITERIA, ELIGIBILITY, PROVIDER_NETWORK

MODEL = "claude-sonnet-4-20250514"
MAX_ITERATIONS = 10

TOOL_SCHEMAS = [
    {
        "name": "validate_request",
        "description": (
            "Validate a pre-authorization request for completeness and correctness. "
            "Checks required fields, CPT code validity, diagnosis codes, and provider NPI."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "request_id": {"type": "string", "description": "The pre-authorization request ID to validate"},
            },
            "required": ["request_id"],
        },
    },
    {
        "name": "extract_clinical_info",
        "description": (
            "Extract structured clinical information from the free-text clinical notes. "
            "Parses BMI, WOMAC score, KL grade, PT sessions, treatment history, and symptoms."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "request_id": {"type": "string", "description": "The pre-authorization request ID"},
            },
            "required": ["request_id"],
        },
    },
    {
        "name": "check_eligibility",
        "description": "Check patient eligibility status and verify active plan coverage.",
        "input_schema": {
            "type": "object",
            "properties": {
                "patient_id": {"type": "string", "description": "The patient ID to check eligibility for"},
            },
            "required": ["patient_id"],
        },
    },
]


def validate_request(request_id: str) -> dict:
    """Validate a pre-auth request for completeness."""
    req = PREAUTH_REQUESTS.get(request_id)
    if not req:
        return {"valid": False, "errors": [f"Request {request_id} not found"]}

    errors = []

    # Check CPT code
    if not req.get("cpt_code"):
        errors.append("Missing CPT code")
    elif req["cpt_code"] not in CLINICAL_CRITERIA:
        errors.append(f"Unknown CPT code: {req['cpt_code']}")

    # Check diagnosis codes
    if not req.get("diagnosis_codes") or len(req["diagnosis_codes"]) == 0:
        errors.append("No diagnosis codes provided")

    # Check provider
    if not req.get("provider_npi"):
        errors.append("Missing provider NPI")
    elif req["provider_npi"] not in PROVIDER_NETWORK:
        errors.append(f"Unknown provider NPI: {req['provider_npi']}")

    # Check patient ID
    if not req.get("patient_id"):
        errors.append("Missing patient ID")

    # Check plan ID
    if not req.get("plan_id"):
        errors.append("Missing plan ID")

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "request_id": request_id,
        "patient_name": req.get("patient_name", ""),
        "cpt_code": req.get("cpt_code", ""),
        "diagnosis_codes": req.get("diagnosis_codes", []),
    }


def extract_clinical_info(request_id: str) -> dict:
    """Extract structured clinical info from free-text notes."""
    req = PREAUTH_REQUESTS.get(request_id)
    if not req:
        return {"error": f"Request {request_id} not found"}

    notes = req.get("clinical_notes", "")
    info: dict[str, Any] = {}

    # BMI
    bmi_match = re.search(r"BMI\s+(\d+\.?\d*)", notes, re.IGNORECASE)
    info["bmi"] = float(bmi_match.group(1)) if bmi_match else None

    # WOMAC score
    womac_match = re.search(r"WOMAC\s+(?:score\s+)?(\d+)", notes, re.IGNORECASE)
    info["womac_score"] = int(womac_match.group(1)) if womac_match else None

    # KL grade
    kl_match = re.search(r"(?:Kellgren-Lawrence|KL)\s+grade\s+(\d+)", notes, re.IGNORECASE)
    info["kl_grade"] = int(kl_match.group(1)) if kl_match else None

    # PT sessions
    pt_match = re.search(r"PT\s*(?:\(|\s+)?(\d+)\s*sessions", notes, re.IGNORECASE)
    if not pt_match:
        pt_match = re.search(r"PT\s+x\s*(\d+)", notes, re.IGNORECASE)
    info["pt_sessions"] = int(pt_match.group(1)) if pt_match else None

    # Conservative treatment duration (months)
    months_match = re.search(r"(\d+)\s*months?\s*(?:of\s+)?(?:conservative|PT|treatment)", notes, re.IGNORECASE)
    info["conservative_treatment_months"] = int(months_match.group(1)) if months_match else None

    # Steroid injections
    inj_match = re.search(r"(\d+)\s*(?:corticosteroid\s+)?(?:steroid\s+)?injection", notes, re.IGNORECASE)
    info["steroid_injections"] = int(inj_match.group(1)) if inj_match else None

    # Urgency indicators
    urgency = []
    if re.search(r"weight\s+loss", notes, re.IGNORECASE):
        urgency.append("weight_loss")
    if re.search(r"dysphagia", notes, re.IGNORECASE):
        urgency.append("dysphagia")
    if re.search(r"seizure", notes, re.IGNORECASE):
        urgency.append("seizure")
    if re.search(r"locked\s+knee", notes, re.IGNORECASE):
        urgency.append("locked_knee")
    if re.search(r"acute", notes, re.IGNORECASE):
        urgency.append("acute")
    if re.search(r"straight\s+leg\s+raise", notes, re.IGNORECASE):
        urgency.append("positive_slr")
    if re.search(r"weight\s+management", notes, re.IGNORECASE):
        urgency.append("weight_management_enrolled")
    info["urgency_indicators"] = urgency

    return {"request_id": request_id, "clinical_info": info}


def check_eligibility(patient_id: str) -> dict:
    """Check patient eligibility."""
    record = ELIGIBILITY.get(patient_id)
    if not record:
        return {"eligible": False, "reason": f"Patient {patient_id} not found in eligibility database"}
    return record


TOOL_HANDLERS = {
    "validate_request": lambda args: validate_request(**args),
    "extract_clinical_info": lambda args: extract_clinical_info(**args),
    "check_eligibility": lambda args: check_eligibility(**args),
}


def execute_tool(tool_name: str, tool_input: dict) -> str:
    handler = TOOL_HANDLERS.get(tool_name)
    if not handler:
        return json.dumps({"error": f"Unknown tool: {tool_name}"})
    try:
        result = handler(tool_input)
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": f"Tool execution failed: {str(e)}"})


class IntakeAgent(BaseAgent):
    name = "IntakeAgent"
    tool_schemas = TOOL_SCHEMAS

    system_prompt = """You are the Intake Agent in a healthcare pre-authorization pipeline.
Your job is to validate incoming requests, extract structured clinical data, and verify eligibility.

You MUST:
1. FIRST validate the request using validate_request
2. THEN extract clinical information using extract_clinical_info
3. FINALLY check eligibility using check_eligibility

After calling all 3 tools, summarize your findings in a structured format:
- Validation: PASS or FAIL (with reasons)
- Clinical Info: key data points extracted
- Eligibility: CONFIRMED or DENIED

If validation fails, note the specific errors. The downstream agents need accurate data."""

    def execute_tool(self, tool_name: str, tool_input: dict) -> str:
        return execute_tool(tool_name, tool_input)

    def build_user_message(self, state: PipelineState) -> str:
        req = state.raw_request
        return (
            f"Process intake for pre-authorization request {req.get('request_id', 'UNKNOWN')}:\n\n"
            f"Patient: {req.get('patient_name', 'N/A')} (ID: {req.get('patient_id', 'N/A')})\n"
            f"Plan: {req.get('plan_id', 'N/A')}\n"
            f"Provider: {req.get('provider_npi', 'N/A')}\n"
            f"Facility: {req.get('facility_id', 'N/A')}\n"
            f"CPT Code: {req.get('cpt_code', 'N/A')}\n"
            f"Diagnosis Codes: {req.get('diagnosis_codes', [])}\n"
            f"Clinical Notes: {req.get('clinical_notes', 'N/A')}\n"
            f"Urgency: {req.get('urgency', 'routine')}"
        )

    def run(self, state: PipelineState) -> PipelineState:
        client = anthropic.Anthropic()
        user_msg = self.build_user_message(state)
        messages = [{"role": "user", "content": user_msg}]

        print(f"\n{'~'*60}")
        print(f"[IntakeAgent] Starting ReAct loop...")
        print(f"{'~'*60}")

        final_text = ""

        for step in range(1, MAX_ITERATIONS + 1):
            try:
                response = client.messages.create(
                    model=MODEL,
                    max_tokens=4096,
                    system=self.system_prompt,
                    tools=self.tool_schemas,
                    messages=messages,
                )
            except Exception as e:
                print(f"  [ERROR] API call failed: {e}")
                state.halted = True
                state.halt_reason = f"IntakeAgent API error: {e}"
                return state

            tool_use_blocks = []
            text_parts = []

            for block in response.content:
                if block.type == "text":
                    text_parts.append(block.text)
                    print(f"  [THINK] Step {step}: {block.text[:200]}...")
                elif block.type == "tool_use":
                    tool_use_blocks.append(block)
                    print(f"  [ACT] Step {step}: {block.name}({json.dumps(block.input)})")

            if response.stop_reason == "end_turn":
                final_text = "\n".join(text_parts)
                break

            if response.stop_reason == "tool_use" and tool_use_blocks:
                messages.append({"role": "assistant", "content": response.content})
                tool_results = []
                for tb in tool_use_blocks:
                    result = self.execute_tool(tb.name, tb.input)
                    print(f"  [OBSERVE] {tb.name} -> {result[:200]}...")
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tb.id,
                        "content": result,
                    })
                messages.append({"role": "user", "content": tool_results})

        # --- Update state from tool results ---
        req = state.raw_request
        state.intake.request_id = req.get("request_id", "")
        state.intake.patient_name = req.get("patient_name", "")
        state.intake.patient_id = req.get("patient_id", "")
        state.intake.plan_id = req.get("plan_id", "")
        state.intake.cpt_code = req.get("cpt_code", "")
        state.intake.diagnosis_codes = req.get("diagnosis_codes", [])
        state.intake.provider_npi = req.get("provider_npi", "")
        state.intake.facility_id = req.get("facility_id", "")
        state.intake.clinical_notes = req.get("clinical_notes", "")

        # Run tool functions directly to populate state fields
        validation = validate_request(req.get("request_id", ""))
        state.intake.validation_passed = validation.get("valid", False)
        state.intake.validation_errors = validation.get("errors", [])

        clinical = extract_clinical_info(req.get("request_id", ""))
        state.intake.clinical_info_extracted = clinical.get("clinical_info", {})

        eligibility = check_eligibility(req.get("patient_id", ""))
        state.intake.eligibility_confirmed = eligibility.get("eligible", False)

        state.agent_trace.append({
            "agent": self.name,
            "completed_at": __import__("datetime").datetime.now().isoformat(),
            "validation_passed": state.intake.validation_passed,
            "eligibility_confirmed": state.intake.eligibility_confirmed,
        })

        return state

    def update_state(self, state: PipelineState, result_text: str) -> PipelineState:
        return state
