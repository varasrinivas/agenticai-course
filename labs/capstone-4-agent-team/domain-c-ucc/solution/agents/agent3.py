"""
Quality Agent (Agent 3) — UCC Data Engineering Pipeline (Solution)

Fully implemented with HITL gate when quality_score < 80% or low_confidence_resolutions > 0.
"""

import json
import re
import os
from typing import Any

import anthropic

from agents import BaseAgent, PipelineState
from mock_data import QUALITY_RULES

MODEL = "claude-sonnet-4-6"
MAX_ITERATIONS = 10
QUALITY_SCORE_THRESHOLD = 80.0
LOW_CONFIDENCE_THRESHOLD = 0

TOOL_SCHEMAS = [
    {
        "name": "run_quality_checks",
        "description": "Run configured quality rules against parsed UCC filings.",
        "input_schema": {
            "type": "object",
            "properties": {
                "filings": {"type": "array", "items": {"type": "object"}, "description": "List of filing dicts"},
                "batch_format": {"type": "string", "description": "Detected format (csv, json, xml, etc.)"},
            },
            "required": ["filings", "batch_format"],
        },
    },
    {
        "name": "detect_anomalies",
        "description": "Detect anomalies: duplicates, PII in collateral, invalid dates, missing fields.",
        "input_schema": {
            "type": "object",
            "properties": {
                "filings": {"type": "array", "items": {"type": "object"}, "description": "List of filing dicts"},
            },
            "required": ["filings"],
        },
    },
    {
        "name": "generate_scorecard",
        "description": "Generate quality scorecard and determine if HITL review is needed.",
        "input_schema": {
            "type": "object",
            "properties": {
                "check_results": {"type": "object", "description": "Results from run_quality_checks"},
                "anomalies": {"type": "array", "items": {"type": "object"}, "description": "Anomaly records"},
                "low_confidence_resolutions": {"type": "integer", "description": "Count from Agent 2"},
            },
            "required": ["check_results", "anomalies", "low_confidence_resolutions"],
        },
    },
]


SSN_PATTERN = re.compile(r"\d{3}-\d{2}-\d{4}")
DOB_PATTERN = re.compile(r"DOB[:\s]", re.IGNORECASE)
DL_PATTERN = re.compile(r"DL[:\s]", re.IGNORECASE)
DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")
SUPPORTED_FORMATS = ["csv", "json", "xml"]


def run_quality_checks(filings: list[dict], batch_format: str) -> dict:
    """Run quality rules against filings."""
    checks_passed = 0
    checks_failed = 0
    failures = []

    # Check supported format (once per batch)
    if batch_format in SUPPORTED_FORMATS:
        checks_passed += 1
    else:
        checks_failed += 1
        failures.append({
            "filing_number": "BATCH",
            "rule": "supported_format",
            "severity": QUALITY_RULES["supported_format"]["severity"],
            "detail": f"Unsupported format: {batch_format}",
        })

    # Check for duplicate filing numbers
    filing_numbers = [f.get("filing_number", "") for f in filings if f.get("filing_number")]
    seen = set()
    duplicates = set()
    for fn in filing_numbers:
        if fn in seen:
            duplicates.add(fn)
        seen.add(fn)

    if duplicates:
        checks_failed += 1
        failures.append({
            "filing_number": ", ".join(duplicates),
            "rule": "no_duplicate_filings",
            "severity": QUALITY_RULES["no_duplicate_filings"]["severity"],
            "detail": f"Duplicate filing numbers: {', '.join(duplicates)}",
        })
    else:
        checks_passed += 1

    # Per-filing checks
    for f in filings:
        fn = f.get("filing_number", "UNKNOWN")

        # filing_number_required
        if f.get("filing_number", "").strip():
            checks_passed += 1
        else:
            checks_failed += 1
            failures.append({
                "filing_number": fn,
                "rule": "filing_number_required",
                "severity": QUALITY_RULES["filing_number_required"]["severity"],
                "detail": "Filing number is empty",
            })

        # debtor_name_required
        if f.get("debtor_name", "").strip():
            checks_passed += 1
        else:
            checks_failed += 1
            failures.append({
                "filing_number": fn,
                "rule": "debtor_name_required",
                "severity": QUALITY_RULES["debtor_name_required"]["severity"],
                "detail": "Debtor name is empty",
            })

        # valid_date_format
        filing_date = f.get("filing_date", "")
        if DATE_PATTERN.match(filing_date):
            checks_passed += 1
        else:
            checks_failed += 1
            failures.append({
                "filing_number": fn,
                "rule": "valid_date_format",
                "severity": QUALITY_RULES["valid_date_format"]["severity"],
                "detail": f"Invalid date: {filing_date}",
            })

        # no_pii_in_collateral
        collateral = f.get("collateral", "")
        has_pii = SSN_PATTERN.search(collateral) or DOB_PATTERN.search(collateral) or DL_PATTERN.search(collateral)
        if has_pii:
            checks_failed += 1
            failures.append({
                "filing_number": fn,
                "rule": "no_pii_in_collateral",
                "severity": QUALITY_RULES["no_pii_in_collateral"]["severity"],
                "detail": "PII detected in collateral description",
            })
        else:
            checks_passed += 1

    total = checks_passed + checks_failed
    return {
        "checks_passed": checks_passed,
        "checks_failed": checks_failed,
        "total_checks": total,
        "failures": failures,
    }


def detect_anomalies(filings: list[dict]) -> dict:
    """Detect anomalies in filings."""
    anomalies = []

    # Duplicate filing numbers
    fn_counts: dict[str, int] = {}
    for f in filings:
        fn = f.get("filing_number", "")
        if fn:
            fn_counts[fn] = fn_counts.get(fn, 0) + 1
    for fn, count in fn_counts.items():
        if count > 1:
            anomalies.append({
                "type": "duplicate_filing",
                "filing_number": fn,
                "severity": "high",
                "detail": f"Filing number {fn} appears {count} times",
            })

    for f in filings:
        fn = f.get("filing_number", "UNKNOWN")

        # PII in collateral
        collateral = f.get("collateral", "")
        if SSN_PATTERN.search(collateral):
            anomalies.append({
                "type": "pii_detected",
                "filing_number": fn,
                "severity": "critical",
                "detail": "SSN pattern found in collateral",
            })
        if DOB_PATTERN.search(collateral):
            anomalies.append({
                "type": "pii_detected",
                "filing_number": fn,
                "severity": "critical",
                "detail": "DOB reference found in collateral",
            })
        if DL_PATTERN.search(collateral):
            anomalies.append({
                "type": "pii_detected",
                "filing_number": fn,
                "severity": "critical",
                "detail": "Driver's license pattern found in collateral",
            })

        # Invalid dates
        filing_date = f.get("filing_date", "")
        if filing_date and not DATE_PATTERN.match(filing_date):
            anomalies.append({
                "type": "invalid_date",
                "filing_number": fn,
                "severity": "high",
                "detail": f"Invalid date format: {filing_date}",
            })

        # Missing required fields
        if not f.get("filing_number", "").strip():
            anomalies.append({
                "type": "missing_field",
                "filing_number": fn,
                "severity": "critical",
                "detail": "Missing filing number",
            })
        if not f.get("debtor_name", "").strip():
            anomalies.append({
                "type": "missing_field",
                "filing_number": fn,
                "severity": "critical",
                "detail": "Missing debtor name",
            })

    return {"anomalies": anomalies, "anomaly_count": len(anomalies)}


def generate_scorecard(
    check_results: dict, anomalies: list[dict], low_confidence_resolutions: int
) -> dict:
    """Generate quality scorecard and determine if HITL is needed."""
    total_checks = check_results.get("total_checks", 0)
    checks_passed = check_results.get("checks_passed", 0)

    if total_checks > 0:
        base_score = (checks_passed / total_checks) * 100
    else:
        base_score = 0.0

    # Deductions by anomaly severity
    critical_count = sum(1 for a in anomalies if a.get("severity") == "critical")
    high_count = sum(1 for a in anomalies if a.get("severity") == "high")
    medium_count = sum(1 for a in anomalies if a.get("severity") == "medium")

    quality_score = base_score - (critical_count * 5) - (high_count * 2) - (medium_count * 1)
    quality_score = max(quality_score, 0.0)

    # Determine HITL
    hitl_reasons = []
    if quality_score < QUALITY_SCORE_THRESHOLD:
        hitl_reasons.append(f"Quality score {quality_score:.1f} < {QUALITY_SCORE_THRESHOLD}")
    if low_confidence_resolutions > LOW_CONFIDENCE_THRESHOLD:
        hitl_reasons.append(f"{low_confidence_resolutions} low-confidence resolutions")

    hitl_required = len(hitl_reasons) > 0

    scorecard = {
        "quality_score": round(quality_score, 1),
        "checks_passed": checks_passed,
        "checks_failed": check_results.get("checks_failed", 0),
        "anomaly_count": len(anomalies),
        "critical_anomalies": critical_count,
        "low_confidence_resolutions": low_confidence_resolutions,
        "hitl_required": hitl_required,
        "hitl_reasons": hitl_reasons,
        "gate_status": "HITL_REVIEW" if hitl_required else "PASS",
    }

    if hitl_required:
        review = _human_review(scorecard)
        scorecard["review_decision"] = review.get("review_decision", "approved")
        scorecard["hitl_triggered"] = True
    else:
        scorecard["hitl_triggered"] = False

    return scorecard


def _human_review(scorecard: dict) -> dict:
    """Simulate HITL gate."""
    print(f"\n{'!'*60}")
    print(f"  HUMAN-IN-THE-LOOP REVIEW REQUIRED")
    print(f"{'!'*60}")
    print(f"  Quality Score: {scorecard['quality_score']}%")
    print(f"  Anomalies: {scorecard['anomaly_count']} ({scorecard['critical_anomalies']} critical)")
    print(f"  Low-confidence resolutions: {scorecard['low_confidence_resolutions']}")
    print(f"  Reasons: {', '.join(scorecard['hitl_reasons'])}")
    print(f"{'!'*60}")

    try:
        choice = input("  Reviewer: Approve (a), Reject (r), or Escalate (e)? ").strip().lower()
    except EOFError:
        choice = "a"  # Auto-approve in non-interactive mode

    if choice == "r":
        review_decision = "rejected"
    elif choice == "e":
        review_decision = "escalated"
    else:
        review_decision = "approved"

    print(f"  Reviewer decision: {review_decision}")
    return {"review_decision": review_decision, "hitl_triggered": True}


TOOL_HANDLERS = {
    "run_quality_checks": lambda args: run_quality_checks(**args),
    "detect_anomalies": lambda args: detect_anomalies(**args),
    "generate_scorecard": lambda args: generate_scorecard(**args),
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


class QualityAgent(BaseAgent):
    name = "QualityAgent"
    tool_schemas = TOOL_SCHEMAS

    system_prompt = f"""You are the Quality Agent in a UCC data engineering pipeline.
Your job is to validate data quality, detect anomalies, and gate the pipeline.

You MUST:
1. FIRST run quality checks using run_quality_checks
2. THEN detect anomalies using detect_anomalies
3. FINALLY generate a scorecard using generate_scorecard

The HITL gate triggers when:
- Quality score < {QUALITY_SCORE_THRESHOLD}%
- Low-confidence entity resolutions > {LOW_CONFIDENCE_THRESHOLD}

If HITL is triggered, the pipeline pauses for human review."""

    def execute_tool(self, tool_name: str, tool_input: dict) -> str:
        return execute_tool(tool_name, tool_input)

    def build_user_message(self, state: PipelineState) -> str:
        ing = state.ingestion
        trans = state.transformation
        return (
            f"Run quality checks on batch {ing.batch_id}:\n\n"
            f"Format: {ing.format_detected}\n"
            f"Filing count: {ing.filing_count}\n"
            f"Schema valid: {ing.schema_valid}\n"
            f"Parse errors: {ing.parse_error_count}\n\n"
            f"Parsed filings:\n{json.dumps(ing.parsed_filings, indent=2)}\n\n"
            f"Entity resolutions:\n{json.dumps(trans.entity_resolutions, indent=2)}\n"
            f"Low-confidence resolutions: {trans.low_confidence_resolutions}\n"
            f"Resolution conflicts: {json.dumps(trans.resolution_conflicts, indent=2)}"
        )

    def run(self, state: PipelineState) -> PipelineState:
        client = anthropic.Anthropic()
        user_msg = self.build_user_message(state)
        messages = [{"role": "user", "content": user_msg}]

        print(f"\n{'~'*60}")
        print(f"[QualityAgent] Starting ReAct loop...")
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
                state.halt_reason = f"QualityAgent API error: {e}"
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
        filings = state.ingestion.parsed_filings
        batch_format = state.ingestion.format_detected

        check_results = run_quality_checks(filings, batch_format)
        anomaly_results = detect_anomalies(filings)
        scorecard = generate_scorecard(
            check_results,
            anomaly_results.get("anomalies", []),
            state.transformation.low_confidence_resolutions,
        )

        state.quality.checks_passed = check_results.get("checks_passed", 0)
        state.quality.checks_failed = check_results.get("checks_failed", 0)
        state.quality.quality_score = scorecard.get("quality_score", 0.0)
        state.quality.anomalies = anomaly_results.get("anomalies", [])
        state.quality.scorecard = scorecard

        # Handle HITL rejection
        if scorecard.get("hitl_triggered") and scorecard.get("review_decision") == "rejected":
            state.halted = True
            state.halt_reason = "Quality gate: reviewer rejected the batch."

        state.agent_trace.append({
            "agent": self.name,
            "completed_at": __import__("datetime").datetime.now().isoformat(),
            "quality_score": state.quality.quality_score,
            "anomaly_count": len(state.quality.anomalies),
            "hitl_triggered": scorecard.get("hitl_triggered", False),
            "gate_status": scorecard.get("gate_status", "UNKNOWN"),
        })

        return state

    def update_state(self, state: PipelineState, result_text: str) -> PipelineState:
        return state
