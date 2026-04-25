"""
Decision Agent (Agent 3) — Healthcare Pre-Auth Pipeline (Solution)

Fully implemented with HITL gate when confidence < 80%.
"""

import json
import os
from typing import Any

import anthropic

from agents import BaseAgent, PipelineState
from mock_data import CLINICAL_CRITERIA, BENEFIT_PLANS, PROVIDER_NETWORK

MODEL = "claude-sonnet-4-20250514"
MAX_ITERATIONS = 10
HITL_CONFIDENCE_THRESHOLD = 80.0

TOOL_SCHEMAS = [
    {
        "name": "apply_decision_rules",
        "description": "Apply pre-authorization decision rules. Returns preliminary decision with confidence score.",
        "input_schema": {
            "type": "object",
            "properties": {
                "cpt_code": {"type": "string"},
                "diagnosis_match": {"type": "boolean"},
                "medical_necessity_score": {"type": "number"},
                "network_status": {"type": "string", "enum": ["in_network", "out_of_network", "not_covered", "unknown"]},
                "benefit_covered": {"type": "boolean"},
                "plan_type": {"type": "string"},
            },
            "required": ["cpt_code", "diagnosis_match", "medical_necessity_score", "network_status", "benefit_covered", "plan_type"],
        },
    },
    {
        "name": "generate_determination",
        "description": "Generate formal determination record with justification.",
        "input_schema": {
            "type": "object",
            "properties": {
                "preliminary_decision": {"type": "string", "enum": ["APPROVED", "DENIED", "PENDED"]},
                "confidence": {"type": "number"},
                "reason": {"type": "string"},
                "cpt_code": {"type": "string"},
            },
            "required": ["preliminary_decision", "confidence", "reason", "cpt_code"],
        },
    },
    {
        "name": "route_for_review",
        "description": "Route low-confidence decision for human review (HITL gate).",
        "input_schema": {
            "type": "object",
            "properties": {
                "request_id": {"type": "string"},
                "preliminary_decision": {"type": "string"},
                "confidence": {"type": "number"},
                "reason": {"type": "string"},
                "review_context": {"type": "string"},
            },
            "required": ["request_id", "preliminary_decision", "confidence", "reason"],
        },
    },
]


def apply_decision_rules(
    cpt_code: str, diagnosis_match: bool, medical_necessity_score: float,
    network_status: str, benefit_covered: bool, plan_type: str,
) -> dict:
    factors = []

    if not benefit_covered:
        factors.append("Procedure category excluded from benefit plan")
        return {"decision": "DENIED", "confidence": 95.0, "reason": "Procedure category excluded from benefit plan.", "factors": factors}

    if network_status == "not_covered":
        factors.append("HMO plan does not cover out-of-network services")
        return {"decision": "DENIED", "confidence": 95.0, "reason": "HMO plan does not cover out-of-network services.", "factors": factors}

    if not diagnosis_match:
        factors.append("Diagnosis codes do not match required criteria")
        return {"decision": "PENDED", "confidence": 70.0, "reason": "Diagnosis codes do not match. Pended for peer review.", "factors": factors}

    if medical_necessity_score >= 80:
        if network_status == "in_network":
            factors.append(f"Medical necessity score {medical_necessity_score}/100 meets threshold")
            factors.append("In-network provider and facility")
            return {"decision": "APPROVED", "confidence": medical_necessity_score, "reason": f"All criteria met. Score: {medical_necessity_score}/100. In-network.", "factors": factors}
        else:
            factors.append(f"Medical necessity score {medical_necessity_score}/100 meets threshold")
            factors.append("Out-of-network: higher cost sharing applies")
            conf = max(medical_necessity_score - 10, 60)
            return {"decision": "APPROVED", "confidence": conf, "reason": f"Criteria met. Score: {medical_necessity_score}/100. Out-of-network benefit level.", "factors": factors}

    if medical_necessity_score >= 60:
        factors.append(f"Medical necessity score {medical_necessity_score}/100 below threshold of 80")
        return {"decision": "PENDED", "confidence": medical_necessity_score, "reason": f"Score {medical_necessity_score}/100 below auto-approval threshold. Pended for peer review.", "factors": factors}

    factors.append(f"Medical necessity score {medical_necessity_score}/100 insufficient")
    conf = min(90 - medical_necessity_score, 95)
    return {"decision": "DENIED", "confidence": conf, "reason": f"Medical necessity not demonstrated. Score: {medical_necessity_score}/100.", "factors": factors}


def generate_determination(preliminary_decision: str, confidence: float, reason: str, cpt_code: str) -> dict:
    criteria = CLINICAL_CRITERIA.get(cpt_code, {})
    validity = criteria.get("approval_validity_days", 0) if preliminary_decision == "APPROVED" else 0

    conditions = []
    if preliminary_decision == "APPROVED":
        conditions = [
            f"Authorization valid for {validity} days",
            "Pre-operative clearance required",
        ]
    elif preliminary_decision == "DENIED":
        conditions = ["Patient may appeal within 60 days", "Provider may submit additional documentation"]
    elif preliminary_decision == "PENDED":
        conditions = ["Peer review within 5 business days", "Provider may submit additional documentation"]

    return {
        "determination": preliminary_decision,
        "confidence": confidence,
        "reason": reason,
        "conditions": conditions,
        "peer_review_required": preliminary_decision == "PENDED",
        "approval_validity_days": validity,
    }


def route_for_review(
    request_id: str, preliminary_decision: str, confidence: float,
    reason: str, review_context: str = "",
) -> dict:
    print(f"\n{'!'*60}")
    print(f"  HUMAN-IN-THE-LOOP REVIEW REQUIRED")
    print(f"{'!'*60}")
    print(f"  Request ID: {request_id}")
    print(f"  Preliminary Decision: {preliminary_decision}")
    print(f"  Confidence: {confidence}%")
    print(f"  Reason: {reason}")
    if review_context:
        print(f"  Context: {review_context}")
    print(f"{'!'*60}")

    try:
        choice = input("  Reviewer: Approve (a), Reject (r), or Override (o)? ").strip().lower()
    except EOFError:
        choice = "a"  # Auto-approve in non-interactive mode

    if choice == "r":
        reviewer_decision = "rejected"
    elif choice == "o":
        reviewer_decision = "override"
    else:
        reviewer_decision = "approved"

    print(f"  Reviewer decision: {reviewer_decision}")
    return {
        "hitl_triggered": True,
        "reviewer_decision": reviewer_decision,
        "original_decision": preliminary_decision,
        "request_id": request_id,
    }


TOOL_HANDLERS = {
    "apply_decision_rules": lambda args: apply_decision_rules(**args),
    "generate_determination": lambda args: generate_determination(**args),
    "route_for_review": lambda args: route_for_review(**args),
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


class DecisionAgent(BaseAgent):
    name = "DecisionAgent"
    tool_schemas = TOOL_SCHEMAS

    system_prompt = f"""You are the Decision Agent in a healthcare pre-authorization pipeline.
You receive clinical criteria evaluation results and must make a determination.

You MUST:
1. FIRST apply decision rules using apply_decision_rules
2. IF confidence < {HITL_CONFIDENCE_THRESHOLD}, use route_for_review for human input
3. FINALLY generate the formal determination using generate_determination

Always justify your decision based on all evidence from prior agents."""

    def execute_tool(self, tool_name: str, tool_input: dict) -> str:
        return execute_tool(tool_name, tool_input)

    def build_user_message(self, state: PipelineState) -> str:
        criteria = state.criteria
        intake = state.intake
        plan = BENEFIT_PLANS.get(intake.plan_id, {})
        return (
            f"Make determination for request {intake.request_id}:\n\n"
            f"CPT Code: {intake.cpt_code}\n"
            f"Diagnosis Match: {criteria.diagnosis_match}\n"
            f"Medical Necessity Score: {criteria.medical_necessity_score}\n"
            f"Network Status: {criteria.network_status}\n"
            f"Benefit Covered: {criteria.benefit_covered}\n"
            f"Plan Type: {plan.get('plan_type', 'UNKNOWN')}\n"
            f"Procedure: {criteria.procedure_name} ({criteria.procedure_category})\n"
            f"Clinical Notes: {intake.clinical_notes}"
        )

    def run(self, state: PipelineState) -> PipelineState:
        client = anthropic.Anthropic()
        user_msg = self.build_user_message(state)
        messages = [{"role": "user", "content": user_msg}]

        print(f"\n{'~'*60}")
        print(f"[DecisionAgent] Starting ReAct loop...")
        print(f"{'~'*60}")

        for step in range(1, MAX_ITERATIONS + 1):
            try:
                response = client.messages.create(
                    model=MODEL, max_tokens=4096,
                    system=self.system_prompt, tools=self.tool_schemas,
                    messages=messages,
                )
            except Exception as e:
                print(f"  [ERROR] API call failed: {e}")
                state.halted = True
                state.halt_reason = f"DecisionAgent API error: {e}"
                return state

            tool_use_blocks = []
            for block in response.content:
                if block.type == "text":
                    print(f"  [THINK] Step {step}: {block.text[:200]}...")
                elif block.type == "tool_use":
                    tool_use_blocks.append(block)
                    print(f"  [ACT] Step {step}: {block.name}({json.dumps(block.input)[:150]})")

            if response.stop_reason == "end_turn":
                break

            if response.stop_reason == "tool_use" and tool_use_blocks:
                messages.append({"role": "assistant", "content": response.content})
                tool_results = []
                for tb in tool_use_blocks:
                    result = self.execute_tool(tb.name, tb.input)
                    print(f"  [OBSERVE] {tb.name} -> {result[:200]}...")
                    tool_results.append({"type": "tool_result", "tool_use_id": tb.id, "content": result})
                messages.append({"role": "user", "content": tool_results})

        # --- Populate state directly ---
        plan = BENEFIT_PLANS.get(state.intake.plan_id, {})
        rules_result = apply_decision_rules(
            cpt_code=state.intake.cpt_code,
            diagnosis_match=state.criteria.diagnosis_match,
            medical_necessity_score=state.criteria.medical_necessity_score,
            network_status=state.criteria.network_status,
            benefit_covered=state.criteria.benefit_covered,
            plan_type=plan.get("plan_type", "PPO"),
        )

        confidence = rules_result.get("confidence", 0)
        decision = rules_result.get("decision", "PENDED")
        reason = rules_result.get("reason", "")

        # HITL gate
        hitl_triggered = False
        hitl_decision = ""
        if confidence < HITL_CONFIDENCE_THRESHOLD:
            hitl_result = route_for_review(
                request_id=state.intake.request_id,
                preliminary_decision=decision,
                confidence=confidence,
                reason=reason,
            )
            hitl_triggered = True
            hitl_decision = hitl_result.get("reviewer_decision", "")
            if hitl_decision == "rejected":
                decision = "DENIED"
                reason = f"Reviewer rejected: {reason}"
            elif hitl_decision == "override":
                decision = "APPROVED"
                reason = f"Reviewer override: {reason}"

        det = generate_determination(decision, confidence, reason, state.intake.cpt_code)

        state.decision.determination = det["determination"]
        state.decision.confidence = det["confidence"]
        state.decision.reason = det["reason"]
        state.decision.conditions = det["conditions"]
        state.decision.peer_review_required = det["peer_review_required"]
        state.decision.hitl_triggered = hitl_triggered
        state.decision.hitl_decision = hitl_decision
        state.decision.approval_validity_days = det["approval_validity_days"]

        state.agent_trace.append({
            "agent": self.name,
            "completed_at": __import__("datetime").datetime.now().isoformat(),
            "determination": state.decision.determination,
            "confidence": state.decision.confidence,
            "hitl_triggered": hitl_triggered,
        })

        return state

    def update_state(self, state: PipelineState, result_text: str) -> PipelineState:
        return state
