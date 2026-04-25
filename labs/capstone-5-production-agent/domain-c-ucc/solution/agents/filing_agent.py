"""
Filing Agent — UCC filing lookup and analysis.
(Solution — fully implemented)
"""

import json
from typing import Any, Dict, List, Optional
from datetime import datetime, date

from anthropic import Anthropic

from config import ANTHROPIC_API_KEY, SYSTEM_PROMPTS, MODEL_TIERS
from mock_data import UCC_FILINGS


FILING_TOOLS = [
    {
        "name": "search_filings",
        "description": "Search UCC filings by debtor name and/or state. Returns matching filings.",
        "input_schema": {
            "type": "object",
            "properties": {
                "debtor_name": {"type": "string", "description": "Debtor name (partial/fuzzy match)"},
                "state": {"type": "string", "description": "Two-letter state code. Omit to search all states."},
            },
            "required": [],
        },
    },
    {
        "name": "get_filing_details",
        "description": "Get complete details for a specific UCC filing by filing number.",
        "input_schema": {
            "type": "object",
            "properties": {
                "filing_number": {"type": "string", "description": "The filing number (e.g., 'NY-2023-0558291')"},
            },
            "required": ["filing_number"],
        },
    },
    {
        "name": "check_filing_status",
        "description": "Check the current status of a UCC filing (active, lapsed, terminated).",
        "input_schema": {
            "type": "object",
            "properties": {
                "filing_number": {"type": "string", "description": "The filing number to check"},
            },
            "required": ["filing_number"],
        },
    },
    {
        "name": "get_amendments",
        "description": "Get the amendment history for a specific UCC filing.",
        "input_schema": {
            "type": "object",
            "properties": {
                "filing_number": {"type": "string", "description": "The filing number"},
            },
            "required": ["filing_number"],
        },
    },
]


class FilingAgent:
    """Specialist agent for UCC filing lookups and analysis."""

    def __init__(self, client: Optional[Anthropic] = None, model_tier: str = "fast"):
        self.client = client or Anthropic(api_key=ANTHROPIC_API_KEY)
        self.model_tier = model_tier
        self.model_id = MODEL_TIERS[model_tier].model_id
        self.system_prompt = SYSTEM_PROMPTS["filing"]

    def _execute_tool(self, tool_name: str, tool_input: Dict[str, Any]) -> str:
        if tool_name == "search_filings":
            result = self._search_filings(
                debtor_name=tool_input.get("debtor_name"),
                state=tool_input.get("state"),
            )
        elif tool_name == "get_filing_details":
            result = self._get_filing_details(tool_input["filing_number"])
        elif tool_name == "check_filing_status":
            result = self._check_filing_status(tool_input["filing_number"])
        elif tool_name == "get_amendments":
            result = self._get_amendments(tool_input["filing_number"])
        else:
            result = {"error": f"Unknown tool: {tool_name}"}
        return json.dumps(result, default=str)

    def _search_filings(
        self, debtor_name: Optional[str] = None, state: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        results = []
        states_to_search = [state.upper()] if state else UCC_FILINGS.keys()

        for st in states_to_search:
            if st not in UCC_FILINGS:
                continue
            for fnum, filing in UCC_FILINGS[st].items():
                if debtor_name:
                    if debtor_name.lower() not in filing["debtor_name"].lower():
                        continue
                results.append({
                    "filing_number": filing["filing_number"],
                    "state": filing["state"],
                    "filing_type": filing["filing_type"],
                    "debtor_name": filing["debtor_name"],
                    "secured_party": filing["secured_party"],
                    "filing_date": filing["filing_date"],
                    "status": filing["status"],
                })

        if not results:
            return [{"message": "No filings found matching the search criteria."}]
        return results

    def _get_filing_details(self, filing_number: str) -> Dict[str, Any]:
        state = filing_number[:2].upper()
        if state in UCC_FILINGS and filing_number in UCC_FILINGS[state]:
            return UCC_FILINGS[state][filing_number]
        return {"error": f"Filing {filing_number} not found."}

    def _check_filing_status(self, filing_number: str) -> Dict[str, Any]:
        state = filing_number[:2].upper()
        if state not in UCC_FILINGS or filing_number not in UCC_FILINGS[state]:
            return {"error": f"Filing {filing_number} not found."}

        filing = UCC_FILINGS[state][filing_number]
        result = {
            "filing_number": filing_number,
            "status": filing["status"],
            "filing_date": filing["filing_date"],
            "filing_type": filing["filing_type"],
            "debtor_name": filing["debtor_name"],
        }

        lapse_date = filing.get("lapse_date")
        if lapse_date:
            result["lapse_date"] = lapse_date
            try:
                lapse = datetime.strptime(lapse_date, "%Y-%m-%d").date()
                today = date.today()
                delta = (lapse - today).days
                if delta > 0:
                    result["days_until_lapse"] = delta
                else:
                    result["days_since_lapse"] = abs(delta)
            except ValueError:
                pass

        if filing.get("related_filing"):
            result["related_filing"] = filing["related_filing"]

        return result

    def _get_amendments(self, filing_number: str) -> Dict[str, Any]:
        state = filing_number[:2].upper()
        if state not in UCC_FILINGS or filing_number not in UCC_FILINGS[state]:
            return {"error": f"Filing {filing_number} not found."}

        filing = UCC_FILINGS[state][filing_number]
        return {
            "filing_number": filing_number,
            "filing_date": filing["filing_date"],
            "amendments": filing.get("amendments", []),
            "amendment_count": len(filing.get("amendments", [])),
        }

    def process(self, query: str) -> Dict[str, Any]:
        messages = [{"role": "user", "content": query}]
        tool_calls_made = []

        for _ in range(10):
            response = self.client.messages.create(
                model=self.model_id,
                max_tokens=MODEL_TIERS[self.model_tier].max_tokens,
                system=self.system_prompt,
                tools=FILING_TOOLS,
                messages=messages,
            )

            # Check if we need to process tool calls
            if response.stop_reason == "tool_use":
                # Add assistant message
                messages.append({"role": "assistant", "content": response.content})

                # Process each tool use block
                tool_results = []
                for block in response.content:
                    if block.type == "tool_use":
                        tool_calls_made.append({"name": block.name, "input": block.input})
                        result = self._execute_tool(block.name, block.input)
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": result,
                        })

                messages.append({"role": "user", "content": tool_results})
            else:
                # Final text response
                answer = ""
                for block in response.content:
                    if hasattr(block, "text"):
                        answer += block.text
                return {
                    "answer": answer,
                    "tool_calls_made": tool_calls_made,
                    "model_used": self.model_id,
                }

        return {
            "answer": "Maximum iterations reached.",
            "tool_calls_made": tool_calls_made,
            "model_used": self.model_id,
        }
