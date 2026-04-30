"""
Transformation Agent (Agent 2) — UCC Data Engineering Pipeline (Solution)

Fully implemented: normalizes entities, classifies collateral, resolves entities.
"""

import json
import re
import os
from typing import Any

import anthropic

from agents import BaseAgent, PipelineState
from mock_data import ENTITY_REGISTRY, COLLATERAL_TYPES

MODEL = "claude-sonnet-4-6"
MAX_ITERATIONS = 10

TOOL_SCHEMAS = [
    {
        "name": "normalize_entities",
        "description": "Normalize entity names: uppercase, strip suffixes, remove DBA clauses.",
        "input_schema": {
            "type": "object",
            "properties": {
                "filing_list": {
                    "type": "array",
                    "items": {"type": "object"},
                    "description": "List of filing dicts to normalize",
                },
            },
            "required": ["filing_list"],
        },
    },
    {
        "name": "classify_collateral",
        "description": "Classify collateral descriptions into taxonomy categories.",
        "input_schema": {
            "type": "object",
            "properties": {
                "filing_list": {
                    "type": "array",
                    "items": {"type": "object"},
                    "description": "List of filing dicts with collateral descriptions",
                },
            },
            "required": ["filing_list"],
        },
    },
    {
        "name": "resolve_entities",
        "description": "Resolve entity names to canonical records via EIN or alias match.",
        "input_schema": {
            "type": "object",
            "properties": {
                "entity_list": {
                    "type": "array",
                    "items": {"type": "object"},
                    "description": "List of dicts with debtor_name, debtor_ein, filing_number",
                },
            },
            "required": ["entity_list"],
        },
    },
]


def normalize_entities(filing_list: list[dict]) -> dict:
    """Normalize entity names in a list of filings."""
    result = []
    for f in filing_list:
        name = f.get("debtor_name", "")
        # Uppercase
        normalized = name.upper().strip()
        # Remove DBA clause
        dba_idx = normalized.find(" DBA ")
        if dba_idx != -1:
            normalized = normalized[:dba_idx].strip()
        # Normalize suffixes
        normalized = re.sub(r"\bCORPORATION\b", "CORP", normalized)
        normalized = re.sub(r"\bINCORPORATED\b", "INC", normalized)
        normalized = re.sub(r"\bLIMITED LIABILITY COMPANY\b", "LLC", normalized)
        normalized = re.sub(r",?\s*L\.L\.C\.", " LLC", normalized)
        # Collapse whitespace
        normalized = re.sub(r"\s+", " ", normalized).strip()
        f_copy = dict(f)
        f_copy["normalized_name"] = normalized
        result.append(f_copy)

    return {"normalized": result, "count": len(result)}


def classify_collateral(filing_list: list[dict]) -> dict:
    """Classify collateral descriptions into taxonomy categories."""
    category_counts: dict[str, int] = {}
    result = []

    for f in filing_list:
        collateral_text = f.get("collateral", "").lower()
        categories = []

        for category, keywords in COLLATERAL_TYPES.items():
            for kw in keywords:
                if kw.lower() in collateral_text:
                    categories.append(category)
                    break  # One match per category is enough

        if not categories:
            categories = ["unclassified"]

        for cat in categories:
            category_counts[cat] = category_counts.get(cat, 0) + 1

        f_copy = dict(f)
        f_copy["collateral_categories"] = categories
        result.append(f_copy)

    return {"classifications": result, "category_counts": category_counts}


def resolve_entities(entity_list: list[dict]) -> dict:
    """Resolve entity names to canonical records."""
    resolutions = []
    resolved_count = 0
    unresolved_count = 0
    low_confidence_count = 0

    for entity in entity_list:
        debtor_name = entity.get("debtor_name", "")
        debtor_ein = entity.get("debtor_ein", "")
        filing_number = entity.get("filing_number", "")

        matched_id = None
        canonical_name = None
        confidence = 0.0
        match_method = "unresolved"

        # Try EIN match first
        if debtor_ein:
            for eid, erec in ENTITY_REGISTRY.items():
                if erec.get("ein") == debtor_ein:
                    matched_id = eid
                    canonical_name = erec["canonical_name"]
                    confidence = 1.0
                    match_method = "ein"
                    break

        # Try alias match if no EIN match
        if not matched_id:
            for eid, erec in ENTITY_REGISTRY.items():
                if debtor_name in erec.get("aliases", []):
                    matched_id = eid
                    canonical_name = erec["canonical_name"]
                    confidence = 0.9
                    match_method = "alias"
                    break

        if matched_id:
            resolved_count += 1
        else:
            unresolved_count += 1

        if confidence < 0.8:
            low_confidence_count += 1

        resolutions.append({
            "filing_number": filing_number,
            "debtor_name": debtor_name,
            "resolved_entity_id": matched_id,
            "canonical_name": canonical_name,
            "confidence": confidence,
            "match_method": match_method,
        })

    return {
        "resolutions": resolutions,
        "resolved_count": resolved_count,
        "unresolved_count": unresolved_count,
        "low_confidence_count": low_confidence_count,
    }


TOOL_HANDLERS = {
    "normalize_entities": lambda args: normalize_entities(**args),
    "classify_collateral": lambda args: classify_collateral(**args),
    "resolve_entities": lambda args: resolve_entities(**args),
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


class TransformationAgent(BaseAgent):
    name = "TransformationAgent"
    tool_schemas = TOOL_SCHEMAS

    system_prompt = """You are the Transformation Agent in a UCC data engineering pipeline.
Your job is to normalize, classify, and resolve entity identities in parsed UCC filings.

You MUST:
1. FIRST normalize entity names using normalize_entities
2. THEN classify collateral descriptions using classify_collateral
3. FINALLY resolve entities to canonical records using resolve_entities

Flag any low-confidence resolutions for the Quality Agent's HITL gating."""

    def execute_tool(self, tool_name: str, tool_input: dict) -> str:
        return execute_tool(tool_name, tool_input)

    def build_user_message(self, state: PipelineState) -> str:
        ing = state.ingestion
        return (
            f"Transform filings from batch {ing.batch_id}:\n\n"
            f"Source: {ing.source}\n"
            f"Format: {ing.format_detected}\n"
            f"Filing count: {ing.filing_count}\n"
            f"Schema valid: {ing.schema_valid}\n"
            f"Schema errors: {ing.schema_errors}\n\n"
            f"Parsed filings:\n{json.dumps(ing.parsed_filings, indent=2)}"
        )

    def run(self, state: PipelineState) -> PipelineState:
        client = anthropic.Anthropic()
        user_msg = self.build_user_message(state)
        messages = [{"role": "user", "content": user_msg}]

        print(f"\n{'~'*60}")
        print(f"[TransformationAgent] Starting ReAct loop...")
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
                state.halt_reason = f"TransformationAgent API error: {e}"
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

        norm_result = normalize_entities(filings)
        normalized_filings = norm_result.get("normalized", filings)

        classify_result = classify_collateral(normalized_filings)
        classified_filings = classify_result.get("classifications", normalized_filings)

        # Build entity list for resolution
        entity_list = [
            {
                "debtor_name": f.get("debtor_name", ""),
                "debtor_ein": f.get("debtor_ein", ""),
                "filing_number": f.get("filing_number", ""),
            }
            for f in filings
        ]
        resolve_result = resolve_entities(entity_list)

        state.transformation.normalized_entities = [
            {"filing_number": f.get("filing_number", ""), "normalized_name": f.get("normalized_name", "")}
            for f in normalized_filings
        ]
        state.transformation.collateral_classifications = [
            {"filing_number": f.get("filing_number", ""), "categories": f.get("collateral_categories", [])}
            for f in classified_filings
        ]
        state.transformation.entity_resolutions = resolve_result.get("resolutions", [])
        state.transformation.low_confidence_resolutions = resolve_result.get("low_confidence_count", 0)

        # Find conflicts (same debtor name resolving to different entities)
        name_to_entities: dict[str, set] = {}
        for r in resolve_result.get("resolutions", []):
            name = r.get("debtor_name", "")
            eid = r.get("resolved_entity_id")
            if eid:
                name_to_entities.setdefault(name, set()).add(eid)
        conflicts = [
            {"debtor_name": name, "entity_ids": list(eids)}
            for name, eids in name_to_entities.items()
            if len(eids) > 1
        ]
        state.transformation.resolution_conflicts = conflicts

        state.agent_trace.append({
            "agent": self.name,
            "completed_at": __import__("datetime").datetime.now().isoformat(),
            "entities_normalized": len(state.transformation.normalized_entities),
            "entities_resolved": resolve_result.get("resolved_count", 0),
            "entities_unresolved": resolve_result.get("unresolved_count", 0),
            "low_confidence": state.transformation.low_confidence_resolutions,
        })

        return state

    def update_state(self, state: PipelineState, result_text: str) -> PipelineState:
        return state
