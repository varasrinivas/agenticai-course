"""
Reporting Agent (Agent 4) — UCC Data Engineering Pipeline (Solution)

Fully implemented: generates risk profiles, lien summaries, and redacts PII.
"""

import json
import re
import os
from typing import Any

import anthropic

from agents import BaseAgent, PipelineState
from mock_data import ENTITY_REGISTRY

MODEL = "claude-sonnet-4-6"
MAX_ITERATIONS = 10

TOOL_SCHEMAS = [
    {
        "name": "generate_risk_profiles",
        "description": "Generate lien risk profiles for each resolved entity.",
        "input_schema": {
            "type": "object",
            "properties": {
                "filings": {"type": "array", "items": {"type": "object"}, "description": "Parsed filing dicts"},
                "entity_resolutions": {"type": "array", "items": {"type": "object"}, "description": "Entity resolution records"},
            },
            "required": ["filings", "entity_resolutions"],
        },
    },
    {
        "name": "generate_lien_summary",
        "description": "Generate aggregate lien summary for the batch.",
        "input_schema": {
            "type": "object",
            "properties": {
                "filings": {"type": "array", "items": {"type": "object"}, "description": "Parsed filing dicts"},
            },
            "required": ["filings"],
        },
    },
    {
        "name": "redact_pii",
        "description": "Scan and redact PII patterns (SSN, DOB, DL, EIN) from text.",
        "input_schema": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Text to redact PII from"},
            },
            "required": ["text"],
        },
    },
]


def generate_risk_profiles(filings: list[dict], entity_resolutions: list[dict]) -> dict:
    """Generate lien risk profiles for resolved entities."""
    # Map filing_number -> resolution
    resolution_map = {}
    for r in entity_resolutions:
        fn = r.get("filing_number", "")
        if fn:
            resolution_map[fn] = r

    # Group filings by entity_id
    entity_filings: dict[str, list[dict]] = {}
    entity_info: dict[str, dict] = {}

    for f in filings:
        fn = f.get("filing_number", "")
        res = resolution_map.get(fn, {})
        eid = res.get("resolved_entity_id")
        if eid:
            entity_filings.setdefault(eid, []).append(f)
            if eid not in entity_info:
                entity_info[eid] = {
                    "canonical_name": res.get("canonical_name", ""),
                    "risk_tier": ENTITY_REGISTRY.get(eid, {}).get("risk_tier", "unknown"),
                }
        else:
            # Unresolved — group under debtor name
            debtor = f.get("debtor_name", "UNKNOWN")
            key = f"UNRESOLVED:{debtor}"
            entity_filings.setdefault(key, []).append(f)
            if key not in entity_info:
                entity_info[key] = {"canonical_name": debtor, "risk_tier": "unknown"}

    profiles = []
    high_risk_count = 0

    for eid, efs in entity_filings.items():
        active_liens = sum(1 for ef in efs if ef.get("status") == "active")
        total_liens = len(efs)

        # Collect collateral types
        collateral_types = set()
        for ef in efs:
            cats = ef.get("collateral_categories", [])
            collateral_types.update(cats)

        risk_tier = entity_info[eid].get("risk_tier", "unknown")

        # Determine risk level
        if active_liens >= 4 or risk_tier == "high":
            risk_level = "critical"
        elif active_liens >= 3:
            risk_level = "high"
        elif active_liens >= 2:
            risk_level = "medium"
        else:
            risk_level = "low"

        if risk_level in ("critical", "high"):
            high_risk_count += 1

        profiles.append({
            "entity_id": eid,
            "canonical_name": entity_info[eid]["canonical_name"],
            "active_liens": active_liens,
            "total_liens": total_liens,
            "collateral_types": sorted(collateral_types),
            "risk_tier": risk_tier,
            "risk_level": risk_level,
        })

    return {
        "profiles": profiles,
        "total_entities": len(profiles),
        "high_risk_count": high_risk_count,
    }


def generate_lien_summary(filings: list[dict]) -> dict:
    """Generate aggregate lien summary for the batch."""
    active_count = 0
    terminated_count = 0
    by_state: dict[str, int] = {}
    secured_party_counts: dict[str, int] = {}
    collateral_dist: dict[str, int] = {}

    for f in filings:
        status = f.get("status", "").lower()
        if status == "active":
            active_count += 1
        elif status == "terminated":
            terminated_count += 1

        # Extract state from filing number (e.g., UCC-2024-CA-00101 -> CA)
        fn = f.get("filing_number", "")
        parts = fn.split("-")
        if len(parts) >= 3:
            filing_state = parts[2]
            by_state[filing_state] = by_state.get(filing_state, 0) + 1

        # Secured party counts
        sp = f.get("secured_party", "")
        if sp:
            secured_party_counts[sp] = secured_party_counts.get(sp, 0) + 1

        # Collateral distribution
        cats = f.get("collateral_categories", [])
        for cat in cats:
            collateral_dist[cat] = collateral_dist.get(cat, 0) + 1

    # Sort secured parties by count
    top_sp = sorted(
        [{"name": k, "filing_count": v} for k, v in secured_party_counts.items()],
        key=lambda x: x["filing_count"],
        reverse=True,
    )

    return {
        "total_filings": len(filings),
        "active_count": active_count,
        "terminated_count": terminated_count,
        "by_state": by_state,
        "top_secured_parties": top_sp[:10],
        "collateral_distribution": collateral_dist,
    }


def redact_pii(text: str) -> dict:
    """Redact PII patterns from text."""
    redaction_counts = {"ssn": 0, "dob": 0, "dl": 0, "ein": 0}
    redacted = text

    # SSN: XXX-XX-XXXX
    ssn_matches = re.findall(r"\d{3}-\d{2}-\d{4}", redacted)
    redaction_counts["ssn"] = len(ssn_matches)
    redacted = re.sub(r"\d{3}-\d{2}-\d{4}", "[REDACTED-SSN]", redacted)

    # DOB: DOB: followed by content until next comma or end
    dob_matches = re.findall(r"DOB[:\s]+[^,;]+", redacted, re.IGNORECASE)
    redaction_counts["dob"] = len(dob_matches)
    redacted = re.sub(r"DOB[:\s]+[^,;]+", "[REDACTED-DOB]", redacted, flags=re.IGNORECASE)

    # DL: DL: followed by content until next comma or end
    dl_matches = re.findall(r"DL[:\s]+[^,;]+", redacted, re.IGNORECASE)
    redaction_counts["dl"] = len(dl_matches)
    redacted = re.sub(r"DL[:\s]+[^,;]+", "[REDACTED-DL]", redacted, flags=re.IGNORECASE)

    # EIN: XX-XXXXXXX (7 digits after dash, to distinguish from SSN which has 4)
    ein_matches = re.findall(r"\d{2}-\d{7}", redacted)
    redaction_counts["ein"] = len(ein_matches)
    redacted = re.sub(r"\d{2}-\d{7}", "[REDACTED-EIN]", redacted)

    total = sum(redaction_counts.values())
    return {
        "redacted_text": redacted,
        "redaction_count": total,
        "redaction_types": redaction_counts,
    }


TOOL_HANDLERS = {
    "generate_risk_profiles": lambda args: generate_risk_profiles(**args),
    "generate_lien_summary": lambda args: generate_lien_summary(**args),
    "redact_pii": lambda args: redact_pii(**args),
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


class ReportingAgent(BaseAgent):
    name = "ReportingAgent"
    tool_schemas = TOOL_SCHEMAS

    system_prompt = """You are the Reporting Agent in a UCC data engineering pipeline.
Your job is to generate risk profiles, summarize lien data, and ensure PII is redacted.

You MUST:
1. FIRST generate risk profiles using generate_risk_profiles
2. THEN generate a lien summary using generate_lien_summary
3. FINALLY redact any PII from the report text using redact_pii

Produce a clean, compliance-ready report. Flag high-risk entities prominently.
All PII must be redacted before the report is considered complete."""

    def execute_tool(self, tool_name: str, tool_input: dict) -> str:
        return execute_tool(tool_name, tool_input)

    def build_user_message(self, state: PipelineState) -> str:
        ing = state.ingestion
        trans = state.transformation
        qual = state.quality
        return (
            f"Generate reports for batch {ing.batch_id}:\n\n"
            f"Filing count: {ing.filing_count}\n"
            f"Quality score: {qual.quality_score}\n"
            f"Quality gate: {'PASS' if qual.quality_score >= 80 else 'HITL_REVIEW'}\n\n"
            f"Parsed filings:\n{json.dumps(ing.parsed_filings, indent=2)}\n\n"
            f"Entity resolutions:\n{json.dumps(trans.entity_resolutions, indent=2)}\n\n"
            f"Collateral classifications:\n{json.dumps(trans.collateral_classifications, indent=2)}\n\n"
            f"Quality scorecard:\n{json.dumps(qual.scorecard, indent=2)}"
        )

    def run(self, state: PipelineState) -> PipelineState:
        client = anthropic.Anthropic()
        user_msg = self.build_user_message(state)
        messages = [{"role": "user", "content": user_msg}]

        print(f"\n{'~'*60}")
        print(f"[ReportingAgent] Starting ReAct loop...")
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
                state.halt_reason = f"ReportingAgent API error: {e}"
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
        entity_resolutions = state.transformation.entity_resolutions

        # Add collateral categories to filings for risk profile
        classifications = state.transformation.collateral_classifications
        class_map = {c.get("filing_number", ""): c.get("categories", []) for c in classifications}
        enriched_filings = []
        for f in filings:
            f_copy = dict(f)
            f_copy["collateral_categories"] = class_map.get(f.get("filing_number", ""), [])
            enriched_filings.append(f_copy)

        risk_result = generate_risk_profiles(enriched_filings, entity_resolutions)
        summary_result = generate_lien_summary(enriched_filings)

        # Build report text for PII redaction
        report_text = json.dumps({
            "risk_profiles": risk_result["profiles"],
            "lien_summary": summary_result,
            "filings": enriched_filings,
        }, indent=2)
        redact_result = redact_pii(report_text)

        state.reporting.risk_profiles = risk_result.get("profiles", [])
        state.reporting.lien_summary = summary_result
        state.reporting.pii_redacted = redact_result.get("redaction_count", 0) > 0
        state.reporting.redaction_count = redact_result.get("redaction_count", 0)
        state.reporting.report_generated = True

        state.agent_trace.append({
            "agent": self.name,
            "completed_at": __import__("datetime").datetime.now().isoformat(),
            "entities_profiled": risk_result.get("total_entities", 0),
            "high_risk_count": risk_result.get("high_risk_count", 0),
            "pii_redactions": redact_result.get("redaction_count", 0),
            "report_generated": True,
        })

        return state

    def update_state(self, state: PipelineState, result_text: str) -> PipelineState:
        return state
