"""
B2B Ecommerce Order Exception Resolution Agent — ReAct Agent (Solution)

Complete implementation of the ReAct loop for investigating order exceptions,
determining root cause, and drafting customer notifications.
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

        try:
            response = client.messages.create(
                model=MODEL,
                max_tokens=4096,
                system=SYSTEM_PROMPT,
                tools=TOOL_SCHEMAS,
                messages=messages,
            )
        except Exception as e:
            print(f"\n[ERROR] API call failed: {e}")
            return f"Agent error: {e}"

        tool_use_blocks = []
        text_parts = []

        for block in response.content:
            if block.type == "text":
                text_parts.append(block.text)
                print(f"\n--- Step {step} ---")
                print(f"[THINK] {block.text}")

            elif block.type == "tool_use":
                tool_use_blocks.append(block)
                print(f"\n--- Step {step} ---")
                print(f"[ACT] Calling tool: {block.name}")
                print(f"      Args: {json.dumps(block.input, indent=2)}")

        if response.stop_reason == "end_turn":
            final_text = "\n".join(text_parts)
            print(f"\n[ANSWER] {final_text[:500]}...")
            return final_text

        if response.stop_reason == "tool_use" and tool_use_blocks:
            messages.append({"role": "assistant", "content": response.content})

            tool_results = []
            for tool_block in tool_use_blocks:
                result = execute_tool(tool_block.name, tool_block.input)
                print(f"[OBSERVE] {tool_block.name} returned: {result[:300]}...")

                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tool_block.id,
                    "content": result,
                })

            messages.append({"role": "user", "content": tool_results})

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
