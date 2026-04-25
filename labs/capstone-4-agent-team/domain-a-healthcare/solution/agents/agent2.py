"""
Clinical Criteria Agent (Agent 2) — Healthcare Pre-Auth Pipeline (Solution)

Fully implemented: looks up criteria, matches diagnoses, calculates necessity score.
"""

import json
import os
from typing import Any

import anthropic

from agents import BaseAgent, PipelineState
from mock_data import CLINICAL_CRITERIA, PROVIDER_NETWORK, BENEFIT_PLANS

MODEL = "claude-sonnet-4-20250514"
MAX_ITERATIONS = 10

TOOL_SCHEMAS = [
    {
        "name": "lookup_clinical_criteria",
        "description": "Look up clinical criteria for pre-authorization of a specific procedure by CPT code.",
        "input_schema": {
            "type": "object",
            "properties": {"cpt_code": {"type": "string", "description": "The CPT procedure code"}},
            "required": ["cpt_code"],
        },
    },
    {
        "name": "match_diagnosis_to_criteria",
        "description": "Match submitted diagnosis codes against required diagnoses for a procedure.",
        "input_schema": {
            "type": "object",
            "properties": {
                "cpt_code": {"type": "string", "description": "The CPT procedure code"},
                "submitted_codes": {"type": "array", "items": {"type": "string"}, "description": "Submitted ICD-10 codes"},
            },
            "required": ["cpt_code", "submitted_codes"],
        },
    },
    {
        "name": "calculate_medical_necessity_score",
        "description": "Calculate a medical necessity score (0-100) based on clinical info and criteria weights.",
        "input_schema": {
            "type": "object",
            "properties": {
                "cpt_code": {"type": "string", "description": "The CPT procedure code"},
                "clinical_info": {"type": "object", "description": "Structured clinical data from Intake Agent"},
                "diagnosis_match": {"type": "boolean", "description": "Whether diagnoses matched"},
            },
            "required": ["cpt_code", "clinical_info", "diagnosis_match"],
        },
    },
]


def lookup_clinical_criteria(cpt_code: str) -> dict:
    criteria = CLINICAL_CRITERIA.get(cpt_code)
    if not criteria:
        return {"error": f"No criteria found for CPT code {cpt_code}"}
    return criteria


def match_diagnosis_to_criteria(cpt_code: str, submitted_codes: list) -> dict:
    criteria = CLINICAL_CRITERIA.get(cpt_code)
    if not criteria:
        return {"error": f"No criteria found for CPT code {cpt_code}"}

    required = set(criteria["required_diagnoses"])
    matched = [c for c in submitted_codes if c in required]
    unmatched = [c for c in submitted_codes if c not in required]
    details = {}
    for code in matched:
        details[code] = criteria.get("diagnosis_descriptions", {}).get(code, "Description not available")

    return {
        "match": len(matched) > 0,
        "matched_codes": matched,
        "unmatched_codes": unmatched,
        "required_codes": criteria["required_diagnoses"],
        "details": details,
        "procedure_name": criteria["procedure_name"],
    }


def calculate_medical_necessity_score(cpt_code: str, clinical_info: dict, diagnosis_match: bool) -> dict:
    criteria = CLINICAL_CRITERIA.get(cpt_code)
    if not criteria:
        return {"error": f"No criteria found for CPT code {cpt_code}", "total_score": 0}

    weights = criteria.get("medical_necessity_weights", {})
    scores = {}
    total = 0.0

    if cpt_code == "27447":
        # Conservative treatment
        months = clinical_info.get("conservative_treatment_months")
        if months is not None and months >= 3:
            scores["conservative_treatment"] = weights.get("conservative_treatment", 0)
        else:
            scores["conservative_treatment"] = 0

        # Imaging grade
        kl = clinical_info.get("kl_grade")
        if kl is not None and kl >= 3:
            scores["imaging_grade"] = weights.get("imaging_grade", 0)
        else:
            scores["imaging_grade"] = 0

        # Functional score
        womac = clinical_info.get("womac_score")
        if womac is not None and womac >= 39:
            scores["functional_score"] = weights.get("functional_score", 0)
        elif womac is not None:
            # Partial credit
            scores["functional_score"] = int(weights.get("functional_score", 0) * (womac / 39.0) * 0.5)
        else:
            scores["functional_score"] = 0

        # BMI compliance
        bmi = clinical_info.get("bmi")
        urgency = clinical_info.get("urgency_indicators", [])
        if bmi is not None and bmi < 40:
            scores["bmi_compliance"] = weights.get("bmi_compliance", 0)
        elif "weight_management_enrolled" in urgency:
            scores["bmi_compliance"] = weights.get("bmi_compliance", 0)
        else:
            scores["bmi_compliance"] = 0

        # Diagnosis match
        scores["diagnosis_match"] = weights.get("diagnosis_match", 0) if diagnosis_match else 0

    elif cpt_code == "29881":
        urgency = clinical_info.get("urgency_indicators", [])
        scores["imaging_confirmation"] = weights.get("imaging_confirmation", 0)  # MRI assumed if request exists
        scores["mechanical_symptoms"] = weights.get("mechanical_symptoms", 0) if "locked_knee" in urgency or "acute" in urgency else 0
        scores["conservative_treatment_or_acute"] = weights.get("conservative_treatment_or_acute", 0) if "acute" in urgency else 0
        scores["diagnosis_match"] = weights.get("diagnosis_match", 0) if diagnosis_match else 0

    elif cpt_code == "43239":
        urgency = clinical_info.get("urgency_indicators", [])
        scores["ppi_failure"] = weights.get("ppi_failure", 0)  # Assumed from request
        has_alarm = any(s in urgency for s in ["weight_loss", "dysphagia"])
        scores["alarm_symptoms"] = weights.get("alarm_symptoms", 0) if has_alarm else 0
        scores["prior_egd_check"] = weights.get("prior_egd_check", 0)
        scores["diagnosis_match"] = weights.get("diagnosis_match", 0) if diagnosis_match else 0

    elif cpt_code == "70553":
        urgency = clinical_info.get("urgency_indicators", [])
        scores["neurological_deficit"] = 0  # Would need more specific data
        scores["new_onset_or_seizure"] = weights.get("new_onset_or_seizure", 0) if "seizure" in urgency else 0
        # Routine follow-up check
        notes = clinical_info.get("notes_summary", "")
        is_routine = "routine follow-up" in str(clinical_info).lower() or "well-controlled" in str(clinical_info).lower()
        scores["not_routine_followup"] = 0 if is_routine else weights.get("not_routine_followup", 0)
        scores["diagnosis_match"] = weights.get("diagnosis_match", 0) if diagnosis_match else 0

    elif cpt_code == "64483":
        urgency = clinical_info.get("urgency_indicators", [])
        scores["physical_exam_findings"] = weights.get("physical_exam_findings", 0) if "positive_slr" in urgency else 0
        months = clinical_info.get("conservative_treatment_months")
        scores["conservative_treatment"] = weights.get("conservative_treatment", 0) if months and months >= 1 else 0
        scores["imaging_confirmation"] = weights.get("imaging_confirmation", 0)
        scores["injection_frequency"] = weights.get("injection_frequency", 0)  # Assume within limits
        scores["diagnosis_match"] = weights.get("diagnosis_match", 0) if diagnosis_match else 0

    else:
        # Experimental or unknown
        scores["diagnosis_match"] = weights.get("diagnosis_match", 0) if diagnosis_match else 0

    total = sum(scores.values())

    return {
        "total_score": total,
        "component_scores": scores,
        "max_possible": 100,
        "recommendation_threshold": 80,
    }


TOOL_HANDLERS = {
    "lookup_clinical_criteria": lambda args: lookup_clinical_criteria(**args),
    "match_diagnosis_to_criteria": lambda args: match_diagnosis_to_criteria(**args),
    "calculate_medical_necessity_score": lambda args: calculate_medical_necessity_score(**args),
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


class ClinicalCriteriaAgent(BaseAgent):
    name = "ClinicalCriteriaAgent"
    tool_schemas = TOOL_SCHEMAS

    system_prompt = """You are the Clinical Criteria Agent in a healthcare pre-authorization pipeline.
You receive intake data and must evaluate clinical criteria.

You MUST:
1. FIRST look up clinical criteria using lookup_clinical_criteria
2. THEN match diagnosis codes using match_diagnosis_to_criteria
3. FINALLY calculate the medical necessity score using calculate_medical_necessity_score

Report: criteria found, diagnosis match status, and the necessity score.
Score >= 80 supports approval. Score < 80 may need additional review."""

    def execute_tool(self, tool_name: str, tool_input: dict) -> str:
        return execute_tool(tool_name, tool_input)

    def build_user_message(self, state: PipelineState) -> str:
        intake = state.intake
        return (
            f"Evaluate clinical criteria for request {intake.request_id}:\n\n"
            f"CPT Code: {intake.cpt_code}\n"
            f"Diagnosis Codes: {intake.diagnosis_codes}\n"
            f"Provider NPI: {intake.provider_npi}\n"
            f"Plan ID: {intake.plan_id}\n"
            f"Clinical Info Extracted: {json.dumps(intake.clinical_info_extracted, indent=2)}\n"
            f"Validation Status: {'PASSED' if intake.validation_passed else 'FAILED'}\n"
            f"Validation Errors: {intake.validation_errors}"
        )

    def run(self, state: PipelineState) -> PipelineState:
        client = anthropic.Anthropic()
        user_msg = self.build_user_message(state)
        messages = [{"role": "user", "content": user_msg}]

        print(f"\n{'~'*60}")
        print(f"[ClinicalCriteriaAgent] Starting ReAct loop...")
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
                state.halt_reason = f"ClinicalCriteriaAgent API error: {e}"
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

        # --- Populate state from direct tool calls ---
        cpt = state.intake.cpt_code
        criteria = lookup_clinical_criteria(cpt)
        if "error" not in criteria:
            state.criteria.criteria_found = True
            state.criteria.procedure_name = criteria.get("procedure_name", "")
            state.criteria.procedure_category = criteria.get("category", "")
            state.criteria.criteria_details = criteria
        else:
            state.criteria.criteria_found = False

        dx_result = match_diagnosis_to_criteria(cpt, state.intake.diagnosis_codes)
        if "error" not in dx_result:
            state.criteria.diagnosis_match = dx_result.get("match", False)
            state.criteria.matched_diagnoses = dx_result.get("matched_codes", [])
            state.criteria.unmatched_diagnoses = dx_result.get("unmatched_codes", [])

        score_result = calculate_medical_necessity_score(
            cpt, state.intake.clinical_info_extracted, state.criteria.diagnosis_match
        )
        state.criteria.medical_necessity_score = score_result.get("total_score", 0.0)

        # Network status
        provider = PROVIDER_NETWORK.get(state.intake.provider_npi)
        plan = BENEFIT_PLANS.get(state.intake.plan_id)
        if provider and plan:
            if plan["plan_type"] == "HMO" and provider["network_status"] == "out_of_network":
                state.criteria.network_status = "not_covered"
            elif provider["network_status"] == "out_of_network":
                state.criteria.network_status = "out_of_network"
            else:
                state.criteria.network_status = "in_network"
        else:
            state.criteria.network_status = "unknown"

        # Benefit coverage
        if plan and state.criteria.procedure_category:
            cat = state.criteria.procedure_category
            if cat in plan.get("excluded_categories", []):
                state.criteria.benefit_covered = False
            elif cat in plan.get("covered_categories", []):
                state.criteria.benefit_covered = True
            else:
                state.criteria.benefit_covered = False
        else:
            state.criteria.benefit_covered = False

        state.agent_trace.append({
            "agent": self.name,
            "completed_at": __import__("datetime").datetime.now().isoformat(),
            "medical_necessity_score": state.criteria.medical_necessity_score,
            "diagnosis_match": state.criteria.diagnosis_match,
            "network_status": state.criteria.network_status,
        })

        return state

    def update_state(self, state: PipelineState, result_text: str) -> PipelineState:
        return state
