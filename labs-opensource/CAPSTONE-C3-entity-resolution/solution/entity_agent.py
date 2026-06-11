"""
CAPSTONE C3: ReAct Entity Resolution Agent — SOLUTION
======================================================
Run: python entity_agent.py
"""

import json

from openai import OpenAI

from entity_tools import (fuzzy_match_score, get_business_registry_data,
                          get_filing_details, merge_entity_profile,
                          search_filings_by_name)

client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")
MODEL = "mistral"  # swap to "mixtral" or "llama3" for stronger reasoning

SYSTEM_PROMPT = """You are an Entity Resolution Agent for a commercial data provider.
Given a business entity name, you determine whether UCC filing records
under different name variations refer to the same real-world company.

## Your Reasoning Process (ReAct)
For each resolution request, think step by step:
1. THINK: What do I know? What do I need to find out?
2. ACT: Call the appropriate tool to gather evidence.
3. OBSERVE: What did the tool return? What does it tell me?
4. REPEAT until you have enough evidence to make a decision.

## Decision Criteria
- token_sort_ratio >= 0.90 AND same state AND same address -> MERGE (high confidence)
- token_sort_ratio >= 0.80 AND same state -> LIKELY MERGE (verify with registry)
- token_sort_ratio >= 0.70 AND different state -> INVESTIGATE (check registry)
- token_sort_ratio < 0.70 -> DISTINCT ENTITY

## Output Format
After resolution, call merge_entity_profile with your findings.
Include a confidence score (0.0-1.0) based on evidence strength.
Explain your reasoning for each merge/separate decision.

## Rules
- Always check the business registry for ambiguous matches.
- If registry data is unavailable, lower your confidence accordingly.
- Never force a merge — flag conflicts for human review.
- If there are 10+ candidates, filter by state before matching."""

TOOLS = [
    {"type": "function", "function": {
        "name": "search_filings_by_name",
        "description": "Search UCC filings by business name across states. Returns candidate entities with filing counts.",
        "parameters": {"type": "object", "properties": {
            "business_name": {"type": "string"},
            "state": {"type": "string"},
            "match_type": {"type": "string", "enum": ["exact", "fuzzy"]}},
            "required": ["business_name"]}}},
    {"type": "function", "function": {
        "name": "fuzzy_match_score",
        "description": "Compute similarity scores between two entity names using normalization and token sort ratio.",
        "parameters": {"type": "object", "properties": {
            "entity_a": {"type": "string"}, "entity_b": {"type": "string"}},
            "required": ["entity_a", "entity_b"]}}},
    {"type": "function", "function": {
        "name": "get_filing_details",
        "description": "Get full filing details (secured parties, collateral, amounts) for an entity in a state.",
        "parameters": {"type": "object", "properties": {
            "business_name": {"type": "string"}, "state": {"type": "string"}},
            "required": ["business_name", "state"]}}},
    {"type": "function", "function": {
        "name": "get_business_registry_data",
        "description": "Cross-reference entity against official SOS business registry for address and status.",
        "parameters": {"type": "object", "properties": {
            "business_name": {"type": "string"}, "state": {"type": "string"}},
            "required": ["business_name", "state"]}}},
    {"type": "function", "function": {
        "name": "merge_entity_profile",
        "description": "Create a merged entity profile from confirmed matches with a confidence score.",
        "parameters": {"type": "object", "properties": {
            "primary_entity": {"type": "object"},
            "merge_candidates": {"type": "array"},
            "confidence": {"type": "number"}},
            "required": ["primary_entity", "merge_candidates", "confidence"]}}},
]

HANDLERS = {
    "search_filings_by_name": lambda a: search_filings_by_name(
        a["business_name"], a.get("state"), a.get("match_type", "fuzzy")),
    "fuzzy_match_score": lambda a: fuzzy_match_score(a["entity_a"], a["entity_b"]),
    "get_filing_details": lambda a: get_filing_details(a["business_name"], a["state"]),
    "get_business_registry_data": lambda a: get_business_registry_data(a["business_name"], a["state"]),
    "merge_entity_profile": lambda a: merge_entity_profile(
        a["primary_entity"], a["merge_candidates"], a["confidence"]),
}


def run_entity_agent(query: str, verbose: bool = True) -> str:
    """The ReAct loop."""
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": query},
    ]

    for _ in range(15):  # entity resolution legitimately needs 8-12 tool calls
        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=messages,
                tools=TOOLS,
            )
        except Exception as e:
            return f"Error calling model: {e}"

        choice = response.choices[0]

        if choice.finish_reason == "tool_calls":
            tool_calls = choice.message.tool_calls or []

            # Append the assistant message with tool_calls re-serialized as dicts
            messages.append({
                "role": "assistant",
                "content": choice.message.content,
                "tool_calls": [
                    {"id": tc.id, "type": "function",
                     "function": {"name": tc.function.name, "arguments": tc.function.arguments}}
                    for tc in tool_calls
                ],
            })

            for tc in tool_calls:
                if verbose:
                    print(f"  [tool] {tc.function.name}({tc.function.arguments[:80]})")
                handler = HANDLERS.get(tc.function.name)
                try:
                    args = json.loads(tc.function.arguments)
                except json.JSONDecodeError:
                    args = {}  # malformed args != crash
                result = handler(args) if handler else {
                    "is_error": True, "error_category": "UNKNOWN_TOOL"}
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": json.dumps(result),
                })

        elif choice.finish_reason == "stop":
            return choice.message.content or "Resolution complete (no text output)."

    return "Resolution exceeded maximum iterations (15)."


if __name__ == "__main__":
    result = run_entity_agent(
        "Resolve entity: Acme Logistics LLC in Delaware. "
        "Check for name variations across states and produce a merged profile."
    )
    print("\n" + "=" * 60)
    print("RESOLUTION:")
    print("=" * 60)
    print(result)
