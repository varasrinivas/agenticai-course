"""
M15 Lab — Code Interpreter Agent (Starter)
============================================
Build an agent that writes and executes Python code in a sandbox
to analyze UCC filing data.

KEY CONCEPT: LLMs predict tokens — they can't reliably do math,
count items, or aggregate data. The solution: let the agent WRITE
Python code, EXECUTE it in a sandbox, and READ the output. This is
the "code interpreter" pattern used by ChatGPT, Claude Artifacts,
and every serious data analysis agent.

Usage:
    python code_agent.py
"""

import json
import sys
import os
from dotenv import load_dotenv

load_dotenv()

# Allow imports from the lab directory
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import anthropic
from sandbox import run_in_sandbox

client = anthropic.Anthropic()
MODEL = "claude-sonnet-4-20250514"


# =============================================================================
# OBSERVATION HELPERS (complete — do not modify)
# =============================================================================

def observe(label: str, message: str) -> None:
    """Print a labelled observation line."""
    print(f"\n{'=' * 60}")
    print(f"[{label}] {message}")
    print(f"{'=' * 60}")


def observe_code(code: str) -> None:
    """Print the agent-generated code with line numbers."""
    print(f"\n{'─' * 60}")
    print("[CODE] Agent-generated Python:")
    for i, line in enumerate(code.split("\n"), 1):
        print(f"  {i:3d} | {line}")
    print(f"{'─' * 60}")


def observe_execution(stdout: str, stderr: str, returncode: int) -> None:
    """Print the sandbox execution result."""
    print(f"\n{'─' * 60}")
    status = "SUCCESS" if returncode == 0 else "ERROR"
    print(f"[EXECUTION: {status}]")
    if stdout:
        print(f"[STDOUT]\n{stdout}")
    if stderr:
        print(f"[STDERR]\n{stderr}")
    print(f"{'─' * 60}")


# =============================================================================
# TOOL DEFINITIONS (complete — do not modify)
# =============================================================================

TOOL_DEFINITIONS = [
    {
        "name": "execute_python",
        "description": (
            "Write and execute Python code to analyze UCC filing data. "
            "A variable called MOCK_FILINGS is pre-loaded — it is a list of dicts, "
            "each with keys: filing_number, type, state, filing_date, expiration_date, "
            "status, debtor_name, debtor_address, debtor_org_type, debtor_jurisdiction, "
            "secured_party_name, secured_party_address, collateral_description. "
            "Use print() to produce output — that is the only way to see results. "
            "Only the Python standard library is available (no pip packages)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "Python code to execute. MOCK_FILINGS is pre-loaded. Use print() for output."
                }
            },
            "required": ["code"]
        }
    }
]


# =============================================================================
# TOOL EXECUTION (complete — do not modify)
# =============================================================================

def execute_tool(tool_name: str, tool_input: dict) -> str:
    """
    Dispatch a tool call to the sandbox. Returns the result as a string.
    On success: returns stdout. On failure: returns JSON with error details.
    """
    if tool_name != "execute_python":
        return json.dumps({"error": f"Unknown tool: {tool_name}"})

    code = tool_input.get("code", "")
    if not code.strip():
        return json.dumps({"error": "Empty code string provided."})

    observe_code(code)

    result = run_in_sandbox(code)
    observe_execution(result["stdout"], result["stderr"], result["returncode"])

    if result["returncode"] == 0:
        return result["stdout"] if result["stdout"] else "(no output — did you forget to print()?)"
    else:
        return json.dumps({
            "error": "Code execution failed",
            "stderr": result["stderr"],
            "hint": "Read the error message, fix the code, and try again."
        })


# =============================================================================
# SYSTEM PROMPT (complete — do not modify)
# =============================================================================

SYSTEM_PROMPT = """You are a UCC filing data analyst agent. You analyze UCC (Uniform Commercial Code)
filing data by writing and executing Python code.

## Your Tool
You have one tool: execute_python. It runs Python code in a sandbox with a
pre-loaded variable called MOCK_FILINGS — a list of dicts with 11 UCC filings.

Each filing dict has these keys:
  filing_number, type, state, filing_date, expiration_date, status,
  debtor_name, debtor_address, debtor_org_type, debtor_jurisdiction,
  secured_party_name, secured_party_address, collateral_description

## How to Work
1. Write Python code that analyzes MOCK_FILINGS using the standard library
2. Always use print() to output results — that is the only way you can see them
3. If your code errors, read the error message and write corrected code
4. After getting results, incorporate the exact numbers into your final answer
5. Use collections.Counter, datetime, etc. from the standard library as needed

## Important Rules
- NEVER guess or make up numbers — always compute them with code
- Handle edge cases: some expiration_date values are None
- Some debtor_name values may be empty strings
- Cite specific numbers from your code output in your final answer
"""


# =============================================================================
# REACT AGENT LOOP — YOUR CODE HERE
# =============================================================================

def run_code_agent(query: str, max_turns: int = 5) -> str:
    """
    Run a ReAct agent that writes and executes Python code to answer queries.

    The loop:
    1. Send the user query (+ conversation history) and tools to Claude
    2. If Claude responds with tool_use → execute the tool, send result back
    3. If Claude responds with end_turn → extract and return the text
    4. Repeat until done or max_turns reached

    Args:
        query:     The user's analysis question
        max_turns: Maximum number of tool-use round trips

    Returns:
        Claude's final text answer (with computed data)
    """
    observe("QUERY", query)

    # ------------------------------------------------------------------
    # TODO: Implement the ReAct loop
    #
    # 1. Initialize messages = [{"role": "user", "content": query}]
    #
    # 2. Loop up to max_turns times:
    #    a. Call client.messages.create() with:
    #       - model=MODEL
    #       - max_tokens=4096
    #       - system=SYSTEM_PROMPT
    #       - tools=TOOL_DEFINITIONS
    #       - messages=messages
    #
    #    b. Check response.stop_reason:
    #       - If NOT "tool_use": extract text blocks, return the text
    #       - If "tool_use": process each tool_use block:
    #         * Call execute_tool(block.name, block.input)
    #         * Collect results as tool_result dicts
    #
    #    c. Append assistant response + tool results to messages:
    #       - messages.append({"role": "assistant", "content": response.content})
    #       - messages.append({"role": "user", "content": tool_results})
    #
    # 3. If loop exhausts max_turns, return a fallback message
    #
    # HINT: This is the exact same ReAct pattern from M12, just with
    # a different tool (execute_python instead of search_filings).
    # ------------------------------------------------------------------
    pass


# =============================================================================
# MAIN — Test Queries
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("M15 Lab — Code Interpreter & Sandbox Execution")
    print("=" * 60)

    # Query 1: Count filings by state
    print("\n\n>>> Query 1: Count filings by state")
    result1 = run_code_agent("Count UCC filings by state and display the results as a table")
    print(f"\nFINAL ANSWER:\n{result1}")

    # Query 2: Blanket liens
    print("\n\n>>> Query 2: Blanket lien percentage")
    result2 = run_code_agent(
        "What percentage of filings are blanket liens "
        "(collateral description contains 'all assets' or 'all accounts')?"
    )
    print(f"\nFINAL ANSWER:\n{result2}")

    # Query 3: Most filings by debtor
    print("\n\n>>> Query 3: Debtor with most filings")
    result3 = run_code_agent("Which debtor has the most filings? Show the debtor name and count.")
    print(f"\nFINAL ANSWER:\n{result3}")

    # Query 4: Average filings per state
    print("\n\n>>> Query 4: Average filings per state")
    result4 = run_code_agent("Calculate the average number of filings per state")
    print(f"\nFINAL ANSWER:\n{result4}")
