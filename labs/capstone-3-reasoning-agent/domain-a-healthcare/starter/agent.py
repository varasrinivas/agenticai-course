"""
Healthcare Pre-Authorization Decision Support Agent — ReAct Agent (Starter)

This agent uses the ReAct (Reasoning + Acting) pattern to process
pre-authorization requests by thinking step-by-step, calling tools
to gather information, and producing a final recommendation.

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
    client = anthropic.Anthropic()  # Uses ANTHROPIC_API_KEY env var

    # Build initial messages
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
        # The response.content is a list of blocks. Each block is either:
        #   - TextBlock (type="text") — Claude's reasoning
        #   - ToolUseBlock (type="tool_use") — Claude wants to call a tool
        #
        # For each block:
        #   - If it's text, print it as [THINK] and store it
        #   - If it's tool_use, print as [ACT], execute the tool, print as [OBSERVE]

        # TODO 3: Check stop reason
        # If response.stop_reason == "end_turn", the agent is done.
        # Extract and return the final text response.
        # If response.stop_reason == "tool_use", we need to continue the loop.

        # TODO 4: Build the tool_result messages
        # For each tool_use block in the response:
        #   1. Execute the tool: result = execute_tool(block.name, block.input)
        #   2. Create a tool_result content block:
        #      {"type": "tool_result", "tool_use_id": block.id, "content": result}
        #
        # Append the assistant's response and the tool results to messages:
        #   messages.append({"role": "assistant", "content": response.content})
        #   messages.append({"role": "user", "content": tool_results_list})

        pass  # Remove this once you've implemented the TODOs

    return "Agent reached maximum iterations without completing."


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    # Test with sample request REQ-001
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
