"""
Entity Agent — entity resolution across UCC filings and states.
(Solution — fully implemented)
"""

import json
import re
from typing import Any, Dict, List, Optional, Tuple

from anthropic import Anthropic

from config import ANTHROPIC_API_KEY, SYSTEM_PROMPTS, MODEL_TIERS
from mock_data import UCC_FILINGS, BUSINESS_REGISTRY, ADDITIONAL_ENTITIES


ENTITY_TOOLS = [
    {
        "name": "search_filings",
        "description": "Search UCC filings by debtor name across all states or a specific state.",
        "input_schema": {
            "type": "object",
            "properties": {
                "debtor_name": {"type": "string", "description": "Debtor name to search for"},
                "state": {"type": "string", "description": "Optional 2-letter state code"},
            },
            "required": ["debtor_name"],
        },
    },
    {
        "name": "fuzzy_match",
        "description": "Compare two entity names and return a similarity score (0.0-1.0) with analysis.",
        "input_schema": {
            "type": "object",
            "properties": {
                "name_a": {"type": "string", "description": "First entity name"},
                "name_b": {"type": "string", "description": "Second entity name"},
            },
            "required": ["name_a", "name_b"],
        },
    },
    {
        "name": "get_business_registry",
        "description": "Look up official business registration data by EIN or entity name.",
        "input_schema": {
            "type": "object",
            "properties": {
                "ein": {"type": "string", "description": "Employer Identification Number"},
                "entity_name": {"type": "string", "description": "Business name to search for"},
            },
            "required": [],
        },
    },
    {
        "name": "merge_entity_profile",
        "description": "Combine filing data and registry data into a unified entity profile.",
        "input_schema": {
            "type": "object",
            "properties": {
                "ein": {"type": "string", "description": "EIN of the entity"},
                "filings": {"type": "array", "items": {"type": "string"},
                            "description": "List of filing numbers to include"},
            },
            "required": ["ein", "filings"],
        },
    },
]

ENTITY_SUFFIXES = re.compile(
    r'\b(inc|llc|corp|corporation|company|co|ltd|lp|group|partners|services|'
    r'international|intl|ventures|holdings)\b\.?',
    re.IGNORECASE,
)


class EntityAgent:
    """Specialist agent for entity resolution across UCC filings."""

    def __init__(self, client: Optional[Anthropic] = None, model_tier: str = "balanced"):
        self.client = client or Anthropic(api_key=ANTHROPIC_API_KEY)
        self.model_tier = model_tier
        self.model_id = MODEL_TIERS[model_tier].model_id
        self.system_prompt = SYSTEM_PROMPTS["entity"]

    def _execute_tool(self, tool_name: str, tool_input: Dict[str, Any]) -> str:
        if tool_name == "search_filings":
            result = self._search_filings(tool_input["debtor_name"], tool_input.get("state"))
        elif tool_name == "fuzzy_match":
            result = self._fuzzy_match(tool_input["name_a"], tool_input["name_b"])
        elif tool_name == "get_business_registry":
            result = self._get_business_registry(tool_input.get("ein"), tool_input.get("entity_name"))
        elif tool_name == "merge_entity_profile":
            result = self._merge_entity_profile(tool_input["ein"], tool_input["filings"])
        else:
            result = {"error": f"Unknown tool: {tool_name}"}
        return json.dumps(result, default=str)

    def _search_filings(self, debtor_name: str, state: Optional[str] = None) -> List[Dict[str, Any]]:
        results = []
        states_to_search = [state.upper()] if state else UCC_FILINGS.keys()
        name_lower = debtor_name.lower()

        for st in states_to_search:
            if st not in UCC_FILINGS:
                continue
            for fnum, filing in UCC_FILINGS[st].items():
                if name_lower in filing["debtor_name"].lower():
                    results.append({
                        "filing_number": filing["filing_number"],
                        "state": filing["state"],
                        "filing_type": filing["filing_type"],
                        "debtor_name": filing["debtor_name"],
                        "debtor_ein": filing.get("debtor_ein", ""),
                        "secured_party": filing["secured_party"],
                        "filing_date": filing["filing_date"],
                        "status": filing["status"],
                    })

        if not results:
            return [{"message": f"No filings found for '{debtor_name}'."}]
        return results

    def _normalize_name(self, name: str) -> str:
        n = name.lower().strip()
        n = re.sub(r'[^\w\s]', '', n)  # Remove punctuation
        n = ENTITY_SUFFIXES.sub('', n)
        n = re.sub(r'\s+', ' ', n).strip()
        return n

    def _fuzzy_match(self, name_a: str, name_b: str) -> Dict[str, Any]:
        norm_a = self._normalize_name(name_a)
        norm_b = self._normalize_name(name_b)

        if norm_a == norm_b:
            return {"score": 1.0, "name_a_normalized": norm_a,
                    "name_b_normalized": norm_b, "match_type": "exact_after_normalization"}

        if norm_a in norm_b or norm_b in norm_a:
            return {"score": 0.85, "name_a_normalized": norm_a,
                    "name_b_normalized": norm_b, "match_type": "containment"}

        tokens_a = set(norm_a.split())
        tokens_b = set(norm_b.split())
        union = tokens_a | tokens_b
        if not union:
            return {"score": 0.0, "name_a_normalized": norm_a,
                    "name_b_normalized": norm_b, "match_type": "no_overlap"}

        jaccard = len(tokens_a & tokens_b) / len(union)
        score = round(jaccard * 0.8, 3)
        match_type = "token_overlap" if score > 0 else "no_overlap"

        return {"score": score, "name_a_normalized": norm_a,
                "name_b_normalized": norm_b, "match_type": match_type}

    def _get_business_registry(
        self, ein: Optional[str] = None, entity_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        # Look up by EIN
        if ein:
            if ein in BUSINESS_REGISTRY:
                return BUSINESS_REGISTRY[ein]
            if ein in ADDITIONAL_ENTITIES:
                return ADDITIONAL_ENTITIES[ein]

        # Look up by name
        if entity_name:
            name_lower = entity_name.lower()
            for eid, entry in {**BUSINESS_REGISTRY, **ADDITIONAL_ENTITIES}.items():
                if name_lower in entry.get("legal_name", "").lower():
                    return entry
                for dba in entry.get("dba_names", []):
                    if name_lower in dba.lower():
                        return entry

        return {"error": f"No registry entry found for EIN={ein}, name={entity_name}."}

    def _merge_entity_profile(self, ein: str, filings: List[str]) -> Dict[str, Any]:
        # Get registry data
        registry = BUSINESS_REGISTRY.get(ein) or ADDITIONAL_ENTITIES.get(ein, {})

        # Collect filing data
        name_variations = set()
        secured_parties = set()
        collateral_descriptions = []
        states_with_filings = set()
        filing_details = []
        active_count = 0

        for fnum in filings:
            state = fnum[:2].upper()
            if state in UCC_FILINGS and fnum in UCC_FILINGS[state]:
                f = UCC_FILINGS[state][fnum]
                name_variations.add(f["debtor_name"])
                secured_parties.add(f["secured_party"])
                collateral_descriptions.append(f["collateral"])
                states_with_filings.add(state)
                if f["status"] == "active":
                    active_count += 1
                filing_details.append({
                    "filing_number": fnum,
                    "state": state,
                    "status": f["status"],
                    "secured_party": f["secured_party"],
                    "filing_date": f["filing_date"],
                })

        return {
            "ein": ein,
            "legal_name": registry.get("legal_name", "Unknown"),
            "name_variations": sorted(name_variations),
            "entity_type": registry.get("entity_type", "Unknown"),
            "state_of_incorporation": registry.get("state_of_incorporation", "Unknown"),
            "total_filings": len(filings),
            "active_filings": active_count,
            "unique_secured_parties": sorted(secured_parties),
            "states_with_filings": sorted(states_with_filings),
            "collateral_descriptions": collateral_descriptions,
            "filing_details": filing_details,
            "registry_data": {
                "dba_names": registry.get("dba_names", []),
                "officers": registry.get("officers", []),
                "annual_revenue_range": registry.get("annual_revenue_range", "Unknown"),
            },
        }

    def process(self, query: str) -> Dict[str, Any]:
        messages = [{"role": "user", "content": query}]
        tool_calls_made = []

        for _ in range(10):
            response = self.client.messages.create(
                model=self.model_id,
                max_tokens=MODEL_TIERS[self.model_tier].max_tokens,
                system=self.system_prompt,
                tools=ENTITY_TOOLS,
                messages=messages,
            )

            if response.stop_reason == "tool_use":
                messages.append({"role": "assistant", "content": response.content})
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
                answer = ""
                for block in response.content:
                    if hasattr(block, "text"):
                        answer += block.text
                return {
                    "answer": answer,
                    "tool_calls_made": tool_calls_made,
                    "model_used": self.model_id,
                }

        return {"answer": "Maximum iterations reached.",
                "tool_calls_made": tool_calls_made, "model_used": self.model_id}
