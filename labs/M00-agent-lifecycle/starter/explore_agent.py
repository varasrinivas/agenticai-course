"""
M00 Lab: UCC Filing Lookup Agent — Explore a Working Agent
===========================================================
This is a COMPLETE, WORKING agent. You do not need to modify it.
Run it, read it, and trace how it works.

Usage:
    python explore_agent.py "Find filings for Greenfield Logistics"
    python explore_agent.py "Look up filing UCC-2024-001"
    python explore_agent.py                                          # uses default query
"""

import os
import sys
import json
from dotenv import load_dotenv

load_dotenv()

# === COMPONENT 7: Home (Deployment) ===
# The runtime environment: dependencies, config, and entry point.
# In production, this would be a Docker container, a serverless function, or a CLI tool.
# Here it is a simple Python script — the simplest possible "home."

import anthropic


# === COMPONENT 2: Tools ===
# Tools are functions the agent can call to interact with the world.
# Each tool has a name, a description (so the LLM knows when to use it),
# and an input schema (so the LLM knows what arguments to pass).

MOCK_FILINGS = {
    "UCC-2024-001": {
        "filing_number": "UCC-2024-001",
        "filing_date": "2024-01-15",
        "debtor": "Greenfield Logistics LLC",
        "secured_party": "First National Bank of Commerce",
        "collateral": "All inventory, equipment, and accounts receivable",
        "status": "Active",
        "jurisdiction": "Delaware",
        "expiration_date": "2029-01-15",
    },
    "UCC-2024-002": {
        "filing_number": "UCC-2024-002",
        "filing_date": "2024-03-22",
        "debtor": "Greenfield Logistics LLC",
        "secured_party": "Pacific Equipment Leasing Corp",
        "collateral": "Specific equipment: 12 Class-8 trucks, VINs on file",
        "status": "Active",
        "jurisdiction": "Delaware",
        "expiration_date": "2029-03-22",
    },
    "UCC-2024-003": {
        "filing_number": "UCC-2024-003",
        "filing_date": "2024-06-10",
        "debtor": "Apex Manufacturing Inc",
        "secured_party": "Silicon Valley Bank",
        "collateral": "All assets including intellectual property and patents",
        "status": "Active",
        "jurisdiction": "California",
        "expiration_date": "2029-06-10",
    },
    "UCC-2023-047": {
        "filing_number": "UCC-2023-047",
        "filing_date": "2023-09-01",
        "debtor": "Coastal Shipping Partners",
        "secured_party": "Maritime Finance Group",
        "collateral": "Fleet vessels and associated equipment",
        "status": "Terminated",
        "jurisdiction": "New York",
        "expiration_date": "2028-09-01",
    },
    "UCC-2024-005": {
        "filing_number": "UCC-2024-005",
        "filing_date": "2024-08-18",
        "debtor": "Greenfield Logistics LLC",
        "secured_party": "Atlas Capital Partners",
        "collateral": "Accounts receivable and contract rights",
        "status": "Active",
        "jurisdiction": "Delaware",
        "expiration_date": "2029-08-18",
    },
}


def lookup_filing(filing_number: str) -> dict:
    """Look up a single UCC filing by its filing number."""
    filing = MOCK_FILINGS.get(filing_number)
    if filing:
        return {"found": True, "filing": filing}
    return {"found": False, "error": f"No filing found with number {filing_number}"}


def search_filings(debtor_name: str) -> dict:
    """Search for UCC filings by debtor name (case-insensitive partial match)."""
    results = [
        f for f in MOCK_FILINGS.values()
        if debtor_name.lower() in f["debtor"].lower()
    ]
    return {
        "query": debtor_name,
        "count": len(results),
        "filings": results,
    }


# Tool definitions tell the LLM what tools exist and how to call them.
# This is the JSON Schema format required by the Anthropic Messages API.
TOOL_DEFINITIONS = [
    {
        "name": "lookup_filing",
        "description": (
            "Look up a specific UCC filing by its filing number. "
            "Use this when the user provides a specific filing number like UCC-2024-001."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "filing_number": {
                    "type": "string",
                    "description": "The UCC filing number, e.g. UCC-2024-001",
                }
            },
            "required": ["filing_number"],
        },
    },
    {
        "name": "search_filings",
        "description": (
            "Search for UCC filings by debtor name. "
            "Use this when the user wants to find all filings associated with a company or person. "
            "Supports partial name matching."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "debtor_name": {
                    "type": "string",
                    "description": "The name (or partial name) of the debtor to search for",
                }
            },
            "required": ["debtor_name"],
        },
    },
]

# Map tool names to functions so the agent loop can dispatch calls.
TOOL_FUNCTIONS = {
    "lookup_filing": lambda args: lookup_filing(args["filing_number"]),
    "search_filings": lambda args: search_filings(args["debtor_name"]),
}


# === COMPONENT 4: Plan (System Prompt) ===
# The plan tells the agent WHO it is, WHAT it can do, and HOW to behave.
# This is your primary steering mechanism. Change it and the agent changes.

SYSTEM_PROMPT = """\
You are a UCC Filing Research Assistant. Your job is to help users look up and \
understand Uniform Commercial Code (UCC) filings.

You have access to two tools:
- lookup_filing: retrieves a specific filing by its filing number
- search_filings: searches for filings by debtor name

When a user asks about filings, use the appropriate tool to find the data, then \
summarize what you found in clear, plain language. Always mention the filing number, \
debtor, secured party, collateral description, and status.

SCOPE: You ONLY handle UCC filing queries. If the user asks about something unrelated, \
politely explain that you are a specialized UCC filing assistant and cannot help with \
other topics.
"""


# === COMPONENT 5: Guardrails ===
# Guardrails validate inputs, limit behavior, and handle errors.
# Even this simple agent has basic guardrails.

MAX_AGENT_TURNS = 10  # Prevent infinite loops
MAX_QUERY_LENGTH = 500  # Reject excessively long inputs


def validate_query(query: str) -> str | None:
    """Validate user input. Returns an error message or None if valid."""
    if not query or not query.strip():
        return "Query cannot be empty."
    if len(query) > MAX_QUERY_LENGTH:
        return f"Query too long ({len(query)} chars). Maximum is {MAX_QUERY_LENGTH}."
    return None


# === COMPONENT 6: Eyes (Observation) ===
# Observation means logging what the agent does so you can debug and improve it.
# In production you would use structured logging, tracing, and metrics.
# Here we print labeled output so you can follow the agent's reasoning.

def observe(label: str, message: str) -> None:
    """Print an observation with a labeled prefix."""
    print(f"\n{'=' * 60}")
    print(f"[{label}] {message}")
    print(f"{'=' * 60}")


def observe_tool_call(tool_name: str, tool_input: dict) -> None:
    """Log a tool call."""
    print(f"\n{'─' * 60}")
    print(f"[USING TOOL] {tool_name}")
    print(f"[INPUT]      {json.dumps(tool_input, indent=2)}")
    print(f"{'─' * 60}")


def observe_tool_result(result: dict) -> None:
    """Log a tool result."""
    print(f"\n{'─' * 60}")
    print(f"[TOOL RESULT]")
    print(json.dumps(result, indent=2))
    print(f"{'─' * 60}")


def run_agent(user_query: str) -> str:
    """
    Run the agent loop: send message -> check for tool_use -> execute -> repeat.

    This is the CORE PATTERN you will implement yourself in M05.
    """
    # === COMPONENT 5: Guardrails (input validation) ===
    error = validate_query(user_query)
    if error:
        observe("ERROR", error)
        return error

    observe("QUERY", user_query)

    # === COMPONENT 1: Brain (LLM) ===
    # The Anthropic client connects to Claude — the brain of the agent.
    client = anthropic.Anthropic()  # Uses ANTHROPIC_API_KEY from environment

    # === COMPONENT 3: Memory ===
    # Memory is the conversation history. The agent sees ALL previous messages
    # each time it makes a decision, giving it context about what happened.
    messages = [
        {"role": "user", "content": user_query}
    ]

    # === THE AGENT LOOP ===
    # This is the heart of every agent: decide -> act -> observe -> repeat.
    turn = 0
    while turn < MAX_AGENT_TURNS:
        turn += 1
        observe("THINKING", f"Turn {turn} — sending {len(messages)} message(s) to Claude...")

        # DECIDE: Ask the LLM what to do next
        try:
            response = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=1024,
                system=SYSTEM_PROMPT,
                tools=TOOL_DEFINITIONS,
                messages=messages,
            )
        except anthropic.APIError as e:
            observe("ERROR", f"API call failed: {e}")
            return f"Error: API call failed — {e}"

        # Check if the agent wants to use a tool or respond to the user
        if response.stop_reason == "tool_use":
            # ACT: Execute every tool the agent requested
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    observe_tool_call(block.name, block.input)

                    # === COMPONENT 5: Guardrails (tool dispatch validation) ===
                    if block.name not in TOOL_FUNCTIONS:
                        result = {"error": f"Unknown tool: {block.name}"}
                    else:
                        try:
                            result = TOOL_FUNCTIONS[block.name](block.input)
                        except Exception as e:
                            result = {"error": f"Tool execution failed: {str(e)}"}

                    observe_tool_result(result)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": json.dumps(result),
                    })

            # OBSERVE: Append the assistant's message and tool results to memory
            messages.append({"role": "assistant", "content": response.content})
            messages.append({"role": "user", "content": tool_results})

            # REPEAT: The loop continues — the LLM will see the tool results

        elif response.stop_reason == "end_turn":
            # The agent is done — extract and return the final text response
            final_text = ""
            for block in response.content:
                if hasattr(block, "text"):
                    final_text += block.text

            observe("RESPONSE", final_text)
            return final_text

        else:
            observe("WARNING", f"Unexpected stop reason: {response.stop_reason}")
            return "Agent stopped unexpectedly."

    observe("ERROR", f"Agent exceeded maximum turns ({MAX_AGENT_TURNS})")
    return "Error: Agent exceeded maximum number of turns."


# === COMPONENT 7: Home (Deployment) — Entry Point ===
if __name__ == "__main__":
    # Accept a query from command line arguments or use a default
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
    else:
        query = "Find filings for Greenfield Logistics"

    print("╔══════════════════════════════════════════════════════════╗")
    print("║        M00 Lab: UCC Filing Lookup Agent                 ║")
    print("║        Explore the Agent Lifecycle                      ║")
    print("╚══════════════════════════════════════════════════════════╝")

    result = run_agent(query)

    print("\n" + "=" * 60)
    print("FINAL ANSWER:")
    print("=" * 60)
    print(result)
