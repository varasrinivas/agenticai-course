"""
M15 Lab — Code Interpreter & Sandbox Execution (Starter)
==========================================================
Build an agent that writes and executes Python code to analyze
UCC filing data. Code runs in a sandboxed subprocess with timeout.

KEY CONCEPT: LLMs can't reliably do math or data analysis —
they predict tokens, not compute results. The solution: let the
agent WRITE Python code, EXECUTE it in a sandbox, and READ the
output. This is the "code interpreter" pattern used by ChatGPT,
Claude Artifacts, and every serious data analysis agent.

Usage:
    python code_interpreter.py
"""

import json
import sys
import os
import subprocess
import tempfile
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import anthropic
from shared.mock_ucc_data import search_filings, get_filing_by_number, ALL_FILINGS

client = anthropic.Anthropic()
MODEL = "claude-sonnet-4-20250514"


# =============================================================================
# OBSERVATION HELPERS (complete — do not modify)
# =============================================================================

def observe(label: str, message: str) -> None:
    print(f"\n{'=' * 60}")
    print(f"[{label}] {message}")
    print(f"{'=' * 60}")


def observe_code(code: str) -> None:
    print(f"\n{'─' * 60}")
    print("[CODE] Agent-generated Python:")
    for i, line in enumerate(code.split("\n"), 1):
        print(f"  {i:3d} | {line}")
    print(f"{'─' * 60}")


def observe_execution(stdout: str, stderr: str, success: bool) -> None:
    print(f"\n{'─' * 60}")
    status = "SUCCESS" if success else "ERROR"
    print(f"[EXECUTION: {status}]")
    if stdout:
        print(f"[STDOUT]\n{stdout}")
    if stderr:
        print(f"[STDERR]\n{stderr}")
    print(f"{'─' * 60}")


# =============================================================================
# MOCK DATA AS INJECTABLE STRING
# Agents can't import our modules, so we serialize the data as a Python variable
# that gets prepended to every code execution.
# =============================================================================

def get_data_preamble() -> str:
    """Generate a Python code preamble that defines FILINGS as a variable."""
    # Serialize filings to a format the generated code can use
    serializable = []
    for f in ALL_FILINGS:
        serializable.append({
            "filing_number": f["filing_number"],
            "type": f["type"],
            "state": f["state"],
            "filing_date": f["filing_date"],
            "expiration_date": f["expiration_date"],
            "status": f["status"],
            "debtor_name": f["debtor"]["name"],
            "secured_party_name": f["secured_party"]["name"],
            "collateral_description": f["collateral_description"],
        })
    return f"FILINGS = {json.dumps(serializable, indent=2)}\n\n"


DATA_PREAMBLE = get_data_preamble()


# =============================================================================
# CODE EXECUTION — YOUR CODE HERE
# =============================================================================

def execute_python(code: str, timeout: int = 10) -> dict:
    """
    Execute Python code in a sandboxed subprocess.

    The code gets the DATA_PREAMBLE prepended (which defines FILINGS variable).
    Runs in a temporary file with a timeout. Captures stdout and stderr.

    Args:
        code: The Python code to execute
        timeout: Maximum execution time in seconds

    Returns:
        dict with keys: "success" (bool), "stdout" (str), "stderr" (str)
    """
    # ------------------------------------------------------------------
    # TODO 1: Implement execute_python()
    #   - Prepend DATA_PREAMBLE to the code
    #   - Write the full code to a temporary .py file
    #   - Run it with subprocess.run():
    #     * Use sys.executable as the Python interpreter
    #     * Set timeout=timeout
    #     * Capture stdout and stderr (text mode)
    #   - Return {"success": True, "stdout": ..., "stderr": ...}
    #   - Handle subprocess.TimeoutExpired → return error result
    #   - Handle other exceptions → return error result
    #   - Clean up the temp file in a finally block
    #
    # SECURITY NOTE: In production, you'd use Docker or E2B for isolation.
    # subprocess is sufficient for this lab's mock data scenario.
    # ------------------------------------------------------------------
    pass


# =============================================================================
# TOOL DEFINITIONS (complete — do not modify)
# =============================================================================

TOOLS = [
    {
        "name": "run_python_code",
        "description": "Write and execute Python code to analyze UCC filing data. The code has access to a FILINGS variable — a list of dicts with keys: filing_number, type, state, filing_date, expiration_date, status, debtor_name, secured_party_name, collateral_description. Print results to stdout.",
        "input_schema": {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "Python code to execute. Use print() for output. FILINGS variable is pre-loaded."
                }
            },
            "required": ["code"]
        }
    },
    {
        "name": "search_filings",
        "description": "Search UCC filings by debtor name and/or state.",
        "input_schema": {
            "type": "object",
            "properties": {
                "debtor_name": {"type": "string", "description": "Debtor name"},
                "state": {"type": "string", "description": "State filter"}
            },
            "required": []
        }
    }
]


# =============================================================================
# TOOL EXECUTION (complete — do not modify)
# =============================================================================

def execute_tool(tool_name: str, tool_input: dict) -> str:
    try:
        if tool_name == "run_python_code":
            code = tool_input["code"]
            observe_code(code)
            result = execute_python(code)
            if result is None:
                return json.dumps({"error": "execute_python returned None — is it implemented?"})
            observe_execution(result["stdout"], result["stderr"], result["success"])
            if result["success"]:
                return result["stdout"] if result["stdout"] else "(no output)"
            else:
                return json.dumps({
                    "error": "Code execution failed",
                    "stderr": result["stderr"],
                    "hint": "Fix the error and try again."
                })
        elif tool_name == "search_filings":
            results = search_filings(
                debtor_name=tool_input.get("debtor_name"),
                state=tool_input.get("state")
            )
            return json.dumps([{
                "filing_number": f["filing_number"],
                "debtor": f["debtor"]["name"],
                "state": f["state"], "status": f["status"]
            } for f in results], indent=2)
        else:
            return json.dumps({"error": f"Unknown tool: {tool_name}"})
    except Exception as e:
        return json.dumps({"error": str(e)})


# =============================================================================
# SYSTEM PROMPT (complete — do not modify)
# =============================================================================

SYSTEM_PROMPT = """You are a UCC filing data analyst agent. You can write and execute Python code
to analyze UCC filing data, and you can search for specific filings.

## Available Data
When you use run_python_code, a variable called FILINGS is pre-loaded. It's a list of dicts,
each with these keys:
- filing_number, type, state, filing_date, expiration_date, status
- debtor_name, secured_party_name, collateral_description

## How to Work
1. For analytical questions (counts, averages, comparisons), write Python code
2. For specific filing lookups, use search_filings
3. Always print() your results in the code — that's how you see the output
4. If your code has an error, read the error message and fix it
5. Include your analysis in your final response, citing the computed numbers

## Important
- Use print() for output — don't just compute, print the results
- Handle edge cases: some fields may be None
- Use standard library only (datetime, collections, etc.)
"""


# =============================================================================
# REACT AGENT LOOP — YOUR CODE HERE
# =============================================================================

def run_code_agent(user_query: str, max_turns: int = 8) -> str:
    """
    Run a ReAct agent that can write and execute Python code.

    Same loop structure as M12, but now one of the tools executes code.
    """
    observe("QUERY", user_query)

    # ------------------------------------------------------------------
    # TODO 2: Implement the ReAct loop (same pattern as M12)
    #   - Initialize messages with user query
    #   - Loop: call Claude → check stop_reason → execute tools or return
    #   - Return final text response
    # ------------------------------------------------------------------
    pass


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("M15 Lab — Code Interpreter & Sandbox Execution")
    print("=" * 60)

    # Query 1: Count by state
    print("\n\n>>> Query 1: Count filings by state")
    result1 = run_code_agent(
        "Count UCC filings by state and show the results"
    )
    print(f"\nFINAL ANSWER:\n{result1}")

    # Query 2: Date calculation
    print("\n\n>>> Query 2: Average days until expiration")
    result2 = run_code_agent(
        "Calculate the average number of days until expiration for all active filings"
    )
    print(f"\nFINAL ANSWER:\n{result2}")

    # Query 3: Collateral analysis
    print("\n\n>>> Query 3: Blanket vs specific collateral")
    result3 = run_code_agent(
        "What percentage of filings have blanket liens (covering 'all assets' or 'all accounts') vs specific collateral?"
    )
    print(f"\nFINAL ANSWER:\n{result3}")
