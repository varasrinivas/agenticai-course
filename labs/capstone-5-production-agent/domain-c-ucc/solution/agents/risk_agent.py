"""
Risk Agent — lien risk assessment and collateral analysis.
(Solution — fully implemented)
"""

import json
from typing import Any, Dict, List, Optional
from datetime import datetime

from anthropic import Anthropic

from config import ANTHROPIC_API_KEY, SYSTEM_PROMPTS, MODEL_TIERS
from mock_data import UCC_FILINGS, BUSINESS_REGISTRY, COLLATERAL_CATEGORIES


RISK_TOOLS = [
    {
        "name": "search_filings",
        "description": "Search UCC filings by debtor name to find all liens.",
        "input_schema": {
            "type": "object",
            "properties": {
                "debtor_name": {"type": "string", "description": "Debtor name"},
                "state": {"type": "string", "description": "Optional state filter"},
            },
            "required": ["debtor_name"],
        },
    },
    {
        "name": "classify_collateral",
        "description": "Classify a collateral description into standard categories and risk levels.",
        "input_schema": {
            "type": "object",
            "properties": {
                "collateral_description": {"type": "string",
                    "description": "The collateral description text from a UCC filing"},
            },
            "required": ["collateral_description"],
        },
    },
    {
        "name": "calculate_exposure",
        "description": "Calculate total lien exposure for an entity based on its filings.",
        "input_schema": {
            "type": "object",
            "properties": {
                "ein": {"type": "string", "description": "EIN of the entity"},
                "filing_numbers": {"type": "array", "items": {"type": "string"},
                    "description": "List of filing numbers"},
            },
            "required": ["ein", "filing_numbers"],
        },
    },
    {
        "name": "generate_risk_report",
        "description": "Generate a structured risk assessment report for an entity.",
        "input_schema": {
            "type": "object",
            "properties": {
                "ein": {"type": "string", "description": "EIN of the entity"},
                "entity_name": {"type": "string", "description": "Name of the entity"},
                "filings_summary": {"type": "string",
                    "description": "JSON string with filing and collateral analysis results"},
            },
            "required": ["ein", "entity_name", "filings_summary"],
        },
    },
]


class RiskAgent:
    """Specialist agent for lien risk assessment."""

    def __init__(self, client: Optional[Anthropic] = None, model_tier: str = "powerful"):
        self.client = client or Anthropic(api_key=ANTHROPIC_API_KEY)
        self.model_tier = model_tier
        self.model_id = MODEL_TIERS[model_tier].model_id
        self.system_prompt = SYSTEM_PROMPTS["risk"]

    def _execute_tool(self, tool_name: str, tool_input: Dict[str, Any]) -> str:
        if tool_name == "search_filings":
            result = self._search_filings(tool_input["debtor_name"], tool_input.get("state"))
        elif tool_name == "classify_collateral":
            result = self._classify_collateral(tool_input["collateral_description"])
        elif tool_name == "calculate_exposure":
            result = self._calculate_exposure(tool_input["ein"], tool_input["filing_numbers"])
        elif tool_name == "generate_risk_report":
            result = self._generate_risk_report(
                tool_input["ein"], tool_input["entity_name"], tool_input["filings_summary"])
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
                        "collateral": filing["collateral"],
                        "filing_date": filing["filing_date"],
                        "lapse_date": filing.get("lapse_date"),
                        "status": filing["status"],
                    })

        if not results:
            return [{"message": f"No filings found for '{debtor_name}'."}]
        return results

    def _classify_collateral(self, collateral_description: str) -> Dict[str, Any]:
        desc_lower = collateral_description.lower()
        matched = []
        risk_levels = []

        for cat_name, cat_info in COLLATERAL_CATEGORIES.items():
            cat_keywords_matched = [kw for kw in cat_info["keywords"] if kw.lower() in desc_lower]
            if cat_keywords_matched:
                matched.append({
                    "category": cat_name,
                    "risk_level": cat_info["risk_level"],
                    "matched_keywords": cat_keywords_matched,
                    "description": cat_info["description"],
                })
                risk_levels.append(cat_info["risk_level"])

        # Determine highest risk level
        risk_priority = {"high": 3, "medium": 2, "low": 1}
        highest_risk = "low"
        if risk_levels:
            highest_risk = max(risk_levels, key=lambda r: risk_priority.get(r, 0))

        is_blanket = any(m["category"] == "all_assets" for m in matched)

        return {
            "categories": [m["category"] for m in matched],
            "risk_level": highest_risk,
            "is_blanket_lien": is_blanket,
            "details": matched,
            "original_description": collateral_description[:200],
        }

    def _calculate_exposure(self, ein: str, filing_numbers: List[str]) -> Dict[str, Any]:
        secured_parties = set()
        states = set()
        filing_details = []
        active_count = 0
        has_blanket = False
        categories_seen = set()
        earliest_date = None

        for fnum in filing_numbers:
            state = fnum[:2].upper()
            if state not in UCC_FILINGS or fnum not in UCC_FILINGS[state]:
                continue
            f = UCC_FILINGS[state][fnum]
            secured_parties.add(f["secured_party"])
            states.add(state)

            if f["status"] == "active":
                active_count += 1

            # Classify collateral
            classification = self._classify_collateral(f["collateral"])
            if classification["is_blanket_lien"]:
                has_blanket = True
            for cat in classification["categories"]:
                categories_seen.add(cat)

            filing_details.append({
                "filing_number": fnum,
                "secured_party": f["secured_party"],
                "collateral_summary": f["collateral"][:100],
                "collateral_categories": classification["categories"],
                "status": f["status"],
                "filing_date": f["filing_date"],
            })

            fdate = f["filing_date"]
            if earliest_date is None or fdate < earliest_date:
                earliest_date = fdate

        return {
            "ein": ein,
            "total_filings": len(filing_numbers),
            "total_active_filings": active_count,
            "unique_secured_parties": sorted(secured_parties),
            "has_blanket_lien": has_blanket,
            "collateral_categories": sorted(categories_seen),
            "states_with_filings": sorted(states),
            "earliest_filing_date": earliest_date,
            "filing_details": filing_details,
        }

    def _generate_risk_report(
        self, ein: str, entity_name: str, filings_summary: str,
    ) -> Dict[str, Any]:
        try:
            summary = json.loads(filings_summary) if isinstance(filings_summary, str) else filings_summary
        except (json.JSONDecodeError, TypeError):
            summary = {}

        # Compute risk score
        score = 0
        risk_factors = []

        has_blanket = summary.get("has_blanket_lien", False)
        active = summary.get("total_active_filings", 0)
        parties = len(summary.get("unique_secured_parties", []))
        states = len(summary.get("states_with_filings", []))
        total = summary.get("total_filings", 0)
        lapsed = total - active

        if has_blanket:
            score += 30
            risk_factors.append("Blanket lien exists — secured party claims all assets")

        filing_score = min(active * 10, 50)
        score += filing_score
        if active > 0:
            risk_factors.append(f"{active} active filing(s) across {states} state(s)")

        if parties > 3:
            score += 15
            risk_factors.append(f"Multiple secured parties ({parties}) — complex lien structure")

        if lapsed > 0:
            score += 20
            risk_factors.append(f"{lapsed} lapsed/terminated filing(s) — may indicate credit issues")

        if states > 3:
            score += 10
            risk_factors.append(f"Filings in {states} states — complex jurisdictional exposure")

        # Map to level
        if score <= 25:
            level = "LOW"
        elif score <= 50:
            level = "MEDIUM"
        elif score <= 75:
            level = "HIGH"
        else:
            level = "CRITICAL"

        # Generate recommendations
        recommendations = []
        if has_blanket:
            recommendations.append("Verify blanket lien priority date before extending new credit")
        if parties > 3:
            recommendations.append("Request subordination agreements from existing secured parties")
        if lapsed > 0:
            recommendations.append("Investigate reason for lapsed filings — may indicate past credit difficulties")
        if states > 3:
            recommendations.append("Consider multi-jurisdictional legal review before lending")
        if level in ("HIGH", "CRITICAL"):
            recommendations.append("Recommend enhanced due diligence and collateral verification")

        return {
            "entity_name": entity_name,
            "ein": ein,
            "risk_score": score,
            "risk_level": level,
            "risk_factors": risk_factors,
            "recommendations": recommendations,
            "filing_summary": {
                "total_filings": total,
                "active_filings": active,
                "unique_secured_parties": parties,
                "states": states,
                "has_blanket_lien": has_blanket,
                "collateral_categories": summary.get("collateral_categories", []),
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
                tools=RISK_TOOLS,
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
