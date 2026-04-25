"""
Ingestion Agent (Agent 1) — UCC Data Engineering Pipeline

Responsibilities:
- Detect the format of an incoming filing batch
- Parse the batch into structured filing records
- Validate the parsed records against the expected schema

Tools:
- detect_format: Identify the file format (csv, json, xml) of a batch
- parse_batch: Parse raw batch data into structured filing records
- validate_schema: Validate parsed filings against required field schema

YOUR TASK: Complete the TODO sections to build a working Ingestion Agent.
"""

import json
import os
from typing import Any

import anthropic

from agents import BaseAgent, PipelineState
from mock_data import FILING_BATCHES

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
MODEL = "claude-sonnet-4-20250514"
MAX_ITERATIONS = 10

# ---------------------------------------------------------------------------
# Tool Schemas (Anthropic format)
# ---------------------------------------------------------------------------
TOOL_SCHEMAS = [
    {
        "name": "detect_format",
        "description": (
            "Detect the file format of a UCC filing batch. Reads the batch metadata "
            "to determine whether the source data is CSV, JSON, XML, or an unsupported "
            "format. Returns the detected format and whether it is supported for parsing."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "batch_id": {
                    "type": "string",
                    "description": "The batch ID to detect the format for",
                },
            },
            "required": ["batch_id"],
        },
    },
    {
        "name": "parse_batch",
        "description": (
            "Parse a UCC filing batch into structured filing records. Extracts individual "
            "filings from the batch and returns them as a list of dictionaries with "
            "standardized field names. Only works for supported formats (csv, json, xml)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "batch_id": {
                    "type": "string",
                    "description": "The batch ID to parse",
                },
            },
            "required": ["batch_id"],
        },
    },
    {
        "name": "validate_schema",
        "description": (
            "Validate parsed filing records against the required UCC filing schema. "
            "Checks that each filing has required fields (filing_number, debtor_name, "
            "secured_party, collateral, filing_date, status) and that values are non-empty. "
            "Returns validation results with any errors found per filing."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "batch_id": {
                    "type": "string",
                    "description": "The batch ID whose parsed filings to validate",
                },
            },
            "required": ["batch_id"],
        },
    },
]


# ---------------------------------------------------------------------------
# Tool Handler Functions
# ---------------------------------------------------------------------------

def detect_format(batch_id: str) -> dict:
    """Detect the file format of a filing batch."""
    # TODO: Implement this function
    # 1. Look up batch_id in FILING_BATCHES
    # 2. If not found, return {"error": f"Batch {batch_id} not found"}
    # 3. Read the "format" field from the batch metadata
    # 4. Check if format is in the supported list: ["csv", "json", "xml"]
    # 5. Return:
    #    {
    #        "batch_id": batch_id,
    #        "format": detected_format,
    #        "supported": True/False,
    #        "source": batch["source"],
    #        "filing_count": batch["filing_count"],
    #    }
    pass


def parse_batch(batch_id: str) -> dict:
    """Parse a filing batch into structured records."""
    # TODO: Implement this function
    # 1. Look up batch_id in FILING_BATCHES
    # 2. If not found, return {"error": f"Batch {batch_id} not found"}
    # 3. Check the format — if unsupported (not csv/json/xml), return:
    #    {"error": f"Unsupported format: {fmt}", "batch_id": batch_id, "parse_error": True}
    # 4. Extract the "filings" list from the batch
    # 5. Count any filings that have empty filing_number or empty debtor_name as parse_errors
    # 6. Return:
    #    {
    #        "batch_id": batch_id,
    #        "filing_count": len(filings),
    #        "filings": filings,
    #        "parse_error_count": error_count,
    #    }
    pass


def validate_schema(batch_id: str) -> dict:
    """Validate parsed filings against the UCC schema."""
    # TODO: Implement this function
    # 1. Look up batch_id in FILING_BATCHES
    # 2. If not found, return {"error": f"Batch {batch_id} not found"}
    # 3. Define required fields: ["filing_number", "debtor_name", "secured_party",
    #                              "collateral", "filing_date", "status"]
    # 4. For each filing, check:
    #    a. All required fields exist and are non-empty strings
    #    b. filing_date matches YYYY-MM-DD pattern (simple regex or string check)
    # 5. Collect errors per filing as a list of dicts:
    #    {"filing_number": "...", "errors": ["missing debtor_name", ...]}
    # 6. Return:
    #    {
    #        "batch_id": batch_id,
    #        "total_filings": len(filings),
    #        "valid_count": count of filings with zero errors,
    #        "invalid_count": count of filings with errors,
    #        "schema_valid": True if all valid else False,
    #        "errors": list of error dicts,
    #    }
    pass


# ---------------------------------------------------------------------------
# Tool dispatcher
# ---------------------------------------------------------------------------
TOOL_HANDLERS = {
    "detect_format": lambda args: detect_format(**args),
    "parse_batch": lambda args: parse_batch(**args),
    "validate_schema": lambda args: validate_schema(**args),
}


def execute_tool(tool_name: str, tool_input: dict) -> str:
    """Execute a tool by name and return the result as a JSON string."""
    handler = TOOL_HANDLERS.get(tool_name)
    if not handler:
        return json.dumps({"error": f"Unknown tool: {tool_name}"})
    try:
        result = handler(tool_input)
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": f"Tool execution failed: {str(e)}"})


# ---------------------------------------------------------------------------
# Ingestion Agent Class
# ---------------------------------------------------------------------------

class IngestionAgent(BaseAgent):
    """
    Agent 1: Detects format, parses batch, and validates schema
    for incoming UCC filing batches.
    """

    name = "IngestionAgent"
    tool_schemas = TOOL_SCHEMAS

    system_prompt = """You are the Ingestion Agent in a UCC data engineering pipeline.
Your job is to ingest raw filing batches, detect their format, parse them into
structured records, and validate the results against the expected schema.

You MUST:
1. FIRST detect the format using detect_format
2. THEN parse the batch using parse_batch
3. FINALLY validate the schema using validate_schema

After calling all 3 tools, summarize your findings in a structured format:
- Format: detected format and whether it is supported
- Parsing: number of filings parsed and any parse errors
- Schema Validation: PASS or FAIL with specific errors

If the format is unsupported, note it clearly. The downstream agents need clean data."""

    def execute_tool(self, tool_name: str, tool_input: dict) -> str:
        return execute_tool(tool_name, tool_input)

    def build_user_message(self, state: PipelineState) -> str:
        """Build the user message from the raw batch data."""
        batch = state.raw_batch
        return (
            f"Ingest UCC filing batch {batch.get('batch_id', 'UNKNOWN')}:\n\n"
            f"Source: {batch.get('source', 'N/A')}\n"
            f"Format: {batch.get('format', 'N/A')}\n"
            f"Expected filing count: {batch.get('filing_count', 0)}\n"
            f"Number of filings in data: {len(batch.get('filings', []))}"
        )

    def run(self, state: PipelineState) -> PipelineState:
        """
        Run the Ingestion Agent's ReAct loop.

        Args:
            state: The current pipeline state.

        Returns:
            Updated pipeline state with ingestion results.
        """
        # TODO: Implement the ReAct loop for the Ingestion Agent
        # 1. Create an Anthropic client
        # 2. Build the initial user message using self.build_user_message(state)
        # 3. Loop up to MAX_ITERATIONS:
        #    a. Call client.messages.create() with model, system prompt, tools, messages
        #    b. Process response content blocks (text and tool_use)
        #    c. If stop_reason == "end_turn", break
        #    d. If stop_reason == "tool_use", execute tools and continue
        # 4. Parse the agent's final response to update state.ingestion
        # 5. Return the updated state
        return state

    def update_state(self, state: PipelineState, result_text: str) -> PipelineState:
        """Update pipeline state with ingestion results."""
        # TODO: Parse result_text and populate state.ingestion fields
        # This is called by the coordinator after run() completes
        return state
