"""
Healthcare Pre-Authorization Decision Support Agent — ReAct Agent (Solution)

Complete implementation of the ReAct loop with reasoning trace logging,
multi-step tool chains, termination conditions, and error recovery.
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

SYSTEM_PROMPT = """You are a Healthcare Pre-Authorization Decision Support Agent. Your job is to
process pre-authorization requests by systematically gathering and analyzing information.

You MUST follow this reasoning process:
1. FIRST, look up the clinical criteria for the requested procedure (CPT code)
2. THEN, verify that the submitted diagnosis codes match the required diagnoses
3. NEXT, check the provider and facility network status for the patient's plan
4. THEN, retrieve the patient's benefit summary to confirm coverage
5. FINALLY, generate an authorization recommendation based on ALL gathered evidence

Think step-by-step. After each tool call, analyze the result before deciding your next action.
When you have gathered all necessary information, use the generate_auth_recommendation tool
to produce your final decision.

Always explain your reasoning clearly. If you find issues (e.g., out-of-network provider,
excluded procedure category), note them and factor them into your recommendation.

Do NOT skip steps. Even if the answer seems obvious, gather ALL evidence first."""


# ---------------------------------------------------------------------------
# ReAct Agent Loop
# ---------------------------------------------------------------------------

def run_agent(user_query: str) -> str:
    """
    Run the ReAct agent loop.

    Args:
        user_query: The pre-authorization request or question to process.

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

        # --- Send message to Claude with tools ---
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

        # --- Process response content blocks ---
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

        # --- Check stop reason ---
        if response.stop_reason == "end_turn":
            # Agent is done — return the final text
            final_text = "\n".join(text_parts)
            print(f"\n[ANSWER] {final_text[:500]}...")
            return final_text

        # --- Execute tools and build tool_result messages ---
        if response.stop_reason == "tool_use" and tool_use_blocks:
            # Append assistant message (contains both text and tool_use blocks)
            messages.append({"role": "assistant", "content": response.content})

            # Build tool results
            tool_results = []
            for tool_block in tool_use_blocks:
                result = execute_tool(tool_block.name, tool_block.input)
                print(f"[OBSERVE] {tool_block.name} returned: {result[:300]}...")

                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tool_block.id,
                    "content": result,
                })

            # Append tool results as a user message
            messages.append({"role": "user", "content": tool_results})

    return "Agent reached maximum iterations without completing."


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    query = """Process this pre-authorization request:

Patient: Maria Gonzalez (DOB: 1958-03-14)
Plan: PLAN-PPO-GOLD
Provider: NPI-1234567890
Facility: FAC-001
Procedure: CPT 27447 (Total Knee Arthroplasty)
Diagnosis: M17.11 (Primary osteoarthritis, right knee)

Clinical Notes: Patient is a 68-year-old female with 2-year history of progressive
right knee pain. Kellgren-Lawrence grade 3 on recent X-ray. WOMAC score 52.
Failed 6 months of conservative management including PT (12 sessions), naproxen
500mg BID, and two corticosteroid injections (most recent 3 months ago with
minimal relief). BMI 32.1. Requesting total knee arthroplasty."""

    result = run_agent(query)
    print("\n" + "=" * 70)
    print("FINAL RESULT")
    print("=" * 70)
    print(result)


if __name__ == "__main__":
    main()
