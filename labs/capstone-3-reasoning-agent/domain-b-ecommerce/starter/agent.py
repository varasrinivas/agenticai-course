"""
B2B Ecommerce Order Exception Resolution Agent — ReAct Agent (Starter)

This agent uses the ReAct pattern to investigate order exceptions,
determine root cause, propose resolutions, and draft customer notifications.

YOUR TASK: Complete the TODO sections to build a working ReAct agent.
"""

import json
import os
import anthropic
from tools import TOOL_SCHEMAS, execute_tool

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
MODEL = "claude-sonnet-4-6"
MAX_ITERATIONS = 15

SYSTEM_PROMPT = """You are a B2B Ecommerce Order Exception Resolution Agent. Your job is to
investigate order exceptions, determine the root cause, propose resolutions,
and draft professional customer notifications.

You MUST follow this reasoning process:
1. FIRST, retrieve the order details to understand the exception type and affected items
2. THEN, investigate the root cause using the appropriate tools:
   - For delayed_shipment: track the shipment, check warehouse inventory
   - For partial_delivery: check warehouse inventory for the short-shipped SKU
   - For pricing_discrepancy: look up the contract pricing agreement
   - For quality_hold: check quality hold status for the affected SKU(s)
3. NEXT, gather any additional context needed (e.g., contract pricing for SLA penalties)
4. FINALLY, draft a customer notification with root cause, resolution, and timeline

Think step-by-step. After each tool call, analyze what you've learned before deciding
your next action. Consider:
- Is there an SLA penalty clause? If so, calculate the potential penalty.
- Are there alternative fulfillment options (other warehouses, replacement SKUs)?
- What is the customer impact and urgency level?

Always provide actionable resolutions, not just problem descriptions."""

# ---------------------------------------------------------------------------
# ReAct Agent Loop
# ---------------------------------------------------------------------------

def run_agent(user_query: str) -> str:
    """
    Run the ReAct agent loop.

    Args:
        user_query: The order exception query to investigate.

    Returns:
        The agent's final response text.
    """
    client = anthropic.Anthropic()

    messages = [{"role": "user", "content": user_query}]

    step = 0
    print("\n" + "=" * 70)
    print("REASONING TRACE")
    print("=" * 70)

    while step < MAX_ITERATIONS:
        step += 1

        # TODO 1: Send the message to Claude with tools
        # Use client.messages.create() with:
        #   - model=MODEL
        #   - max_tokens=4096
        #   - system=SYSTEM_PROMPT
        #   - tools=TOOL_SCHEMAS
        #   - messages=messages
        response = None  # Replace with API call

        # TODO 2: Process the response content blocks
        # For each block in response.content:
        #   - TextBlock → print as [THINK]
        #   - ToolUseBlock → print as [ACT], execute, print as [OBSERVE]

        # TODO 3: Check stop reason
        # If response.stop_reason == "end_turn" → return final text
        # If response.stop_reason == "tool_use" → continue loop

        # TODO 4: Build tool_result messages and append to conversation
        # messages.append({"role": "assistant", "content": response.content})
        # messages.append({"role": "user", "content": [tool_results...]})

        pass  # Remove once TODOs are implemented

    return "Agent reached maximum iterations without completing."


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    query = "Investigate the exception on order ORD-2024-1847 and resolve it."

    result = run_agent(query)
    print("\n" + "=" * 70)
    print("FINAL RESULT")
    print("=" * 70)
    print(result)


if __name__ == "__main__":
    main()
