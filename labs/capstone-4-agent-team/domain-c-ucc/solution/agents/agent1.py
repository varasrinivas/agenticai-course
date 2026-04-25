"""
Ingestion Agent (Agent 1) — UCC Data Engineering Pipeline (Solution)

Fully implemented: detects format, parses batch, validates schema.
"""

import json
import re
import os
from typing import Any

import anthropic

from agents import BaseAgent, PipelineState
from mock_data import FILING_BATCHES

MODEL = "claude-sonnet-4-20250514"
MAX_ITERATIONS = 10

TOOL_SCHEMAS = [
    {
        "name": "detect_format",
        "description": (
            "Detect the file format of a UCC filing batch. Returns the detected format "
            "and whether it is supported for parsing."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "batch_id": {"type": "string", "description": "The batch ID to detect the format for"},
            },
            "required": ["batch_id"],
        },
    },
    {
        "name": "parse_batch",
        "description": (
            "Parse a UCC filing batch into structured filing records. "
            "Only works for supported formats (csv, json, xml)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "batch_id": {"type": "string", "description": "The batch ID to parse"},
            },
            "required": ["batch_id"],
        },
    },
    {
        "name": "validate_schema",
        "description": (
            "Validate parsed filing records against the required UCC filing schema. "
            "Checks required fields and date format."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "batch_id": {"type": "string", "description": "The batch ID whose parsed filings to validate"},
            },
            "required": ["batch_id"],
        },
    },
]


SUPPORTED_FORMATS = ["csv", "json", "xml"]


def detect_format(batch_id: str) -> dict:
    """Detect the file format of a filing batch."""
    batch = FILING_BATCHES.get(batch_id)
    if not batch:
        return {"error": f"Batch {batch_id} not found"}

    fmt = batch.get("format", "unknown")
    return {
        "batch_id": batch_id,
        "format": fmt,
        "supported": fmt in SUPPORTED_FORMATS,
        "source": batch.get("source", ""),
        "filing_count": batch.get("filing_count", 0),
    }


def parse_batch(batch_id: str) -> dict:
    """Parse a filing batch into structured records."""
    batch = FILING_BATCHES.get(batch_id)
    if not batch:
        return {"error": f"Batch {batch_id} not found"}

    fmt = batch.get("format", "unknown")
    if fmt not in SUPPORTED_FORMATS:
        return {
            "error": f"Unsupported format: {fmt}",
            "batch_id": batch_id,
            "parse_error": True,
        }

    filings = batch.get("filings", [])
    error_count = 0
    for f in filings:
        if not f.get("filing_number") or not f.get("debtor_name"):
            error_count += 1

    return {
        "batch_id": batch_id,
        "filing_count": len(filings),
        "filings": filings,
        "parse_error_count": error_count,
    }


def validate_schema(batch_id: str) -> dict:
    """Validate parsed filings against the UCC schema."""
    batch = FILING_BATCHES.get(batch_id)
    if not batch:
        return {"error": f"Batch {batch_id} not found"}

    filings = batch.get("filings", [])
    required_fields = ["filing_number", "debtor_name", "secured_party", "collateral", "filing_date", "status"]
    date_pattern = re.compile(r"^\d{4}-\d{2}-\d{2}$")

    errors_list = []
    valid_count = 0

    for f in filings:
        filing_errors = []
        fn = f.get("filing_number", "UNKNOWN")

        for field in required_fields:
            val = f.get(field, "")
            if not val or (isinstance(val, str) and val.strip() == ""):
                filing_errors.append(f"missing {field}")

        filing_date = f.get("filing_date", "")
        if filing_date and not date_pattern.match(filing_date):
            filing_errors.append(f"invalid date format: {filing_date}")

        if filing_errors:
            errors_list.append({"filing_number": fn, "errors": filing_errors})
        else:
            valid_count += 1

    return {
        "batch_id": batch_id,
        "total_filings": len(filings),
        "valid_count": valid_count,
        "invalid_count": len(filings) - valid_count,
        "schema_valid": len(errors_list) == 0,
        "errors": errors_list,
    }


TOOL_HANDLERS = {
    "detect_format": lambda args: detect_format(**args),
    "parse_batch": lambda args: parse_batch(**args),
    "validate_schema": lambda args: validate_schema(**args),
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


class IngestionAgent(BaseAgent):
    name = "IngestionAgent"
    tool_schemas = TOOL_SCHEMAS

    system_prompt = """You are the Ingestion Agent in a UCC data engineering pipeline.
Your job is to ingest raw filing batches, detect their format, parse them into
structured records, and validate the results against the expected schema.

You MUST:
1. FIRST detect the format using detect_format
2. THEN parse the batch using parse_batch
3. FINALLY validate the schema using validate_schema

After calling all 3 tools, summarize your findings:
- Format: detected format and whether supported
- Parsing: number of filings parsed and any parse errors
- Schema Validation: PASS or FAIL with specific errors

If format is unsupported, note it clearly. Downstream agents need clean data."""

    def execute_tool(self, tool_name: str, tool_input: dict) -> str:
        return execute_tool(tool_name, tool_input)

    def build_user_message(self, state: PipelineState) -> str:
        batch = state.raw_batch
        return (
            f"Ingest UCC filing batch {batch.get('batch_id', 'UNKNOWN')}:\n\n"
            f"Source: {batch.get('source', 'N/A')}\n"
            f"Format: {batch.get('format', 'N/A')}\n"
            f"Expected filing count: {batch.get('filing_count', 0)}\n"
            f"Number of filings in data: {len(batch.get('filings', []))}"
        )

    def run(self, state: PipelineState) -> PipelineState:
        client = anthropic.Anthropic()
        user_msg = self.build_user_message(state)
        messages = [{"role": "user", "content": user_msg}]

        print(f"\n{'~'*60}")
        print(f"[IngestionAgent] Starting ReAct loop...")
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
                state.halt_reason = f"IngestionAgent API error: {e}"
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
        batch = state.raw_batch
        batch_id = batch.get("batch_id", "")

        format_result = detect_format(batch_id)
        parse_result = parse_batch(batch_id)
        schema_result = validate_schema(batch_id)

        state.ingestion.batch_id = batch_id
        state.ingestion.source = batch.get("source", "")
        state.ingestion.format_detected = format_result.get("format", "unknown")

        if parse_result.get("parse_error"):
            # Unsupported format
            state.ingestion.filing_count = 0
            state.ingestion.parsed_filings = []
            state.ingestion.schema_valid = False
            state.ingestion.schema_errors = [parse_result.get("error", "Parse error")]
            state.ingestion.parse_error_count = 1
        else:
            state.ingestion.filing_count = parse_result.get("filing_count", 0)
            state.ingestion.parsed_filings = parse_result.get("filings", [])
            state.ingestion.parse_error_count = parse_result.get("parse_error_count", 0)
            state.ingestion.schema_valid = schema_result.get("schema_valid", False)
            state.ingestion.schema_errors = [
                f"{e['filing_number']}: {', '.join(e['errors'])}"
                for e in schema_result.get("errors", [])
            ]

        state.agent_trace.append({
            "agent": self.name,
            "completed_at": __import__("datetime").datetime.now().isoformat(),
            "format_detected": state.ingestion.format_detected,
            "filing_count": state.ingestion.filing_count,
            "schema_valid": state.ingestion.schema_valid,
            "parse_error_count": state.ingestion.parse_error_count,
        })

        return state

    def update_state(self, state: PipelineState, result_text: str) -> PipelineState:
        return state
