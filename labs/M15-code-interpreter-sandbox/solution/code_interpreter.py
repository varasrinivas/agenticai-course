"""
M15 Lab — Code Interpreter & Sandbox Execution (Solution)
===========================================================
Agent that writes and executes Python to analyze UCC filing data.

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
# OBSERVATION HELPERS
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
# DATA PREAMBLE
# =============================================================================

def get_data_preamble() -> str:
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
# CODE EXECUTION — SOLUTION
# =============================================================================

def execute_python(code: str, timeout: int = 10) -> dict:
    """Execute Python code in a sandboxed subprocess."""
    full_code = DATA_PREAMBLE + code
    tmp_path = None

    try:
        # Write code to a temporary file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(full_code)
            tmp_path = f.name

        # Execute in subprocess with timeout
        result = subprocess.run(
            [sys.executable, tmp_path],
            capture_output=True,
            text=True,
            timeout=timeout,
        )

        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }

    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "stdout": "",
            "stderr": f"Execution timed out after {timeout} seconds",
        }
    except Exception as e:
        return {
            "success": False,
            "stdout": "",
            "stderr": f"Execution error: {str(e)}",
        }
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)


# =============================================================================
# TOOLS
# =============================================================================

TOOLS = [
    {
        "name": "run_python_code",
        "description": "Write and execute Python code to analyze UCC filing data. A FILINGS variable (list of dicts) is pre-loaded. Print results to stdout.",
        "input_schema": {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "Python code to execute. Use print() for output. FILINGS is pre-loaded."
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
                "debtor_name": {"type": "string"},
                "state": {"type": "string"}
            },
            "required": []
        }
    }
]


def execute_tool(tool_name: str, tool_input: dict) -> str:
    try:
        if tool_name == "run_python_code":
            code = tool_input["code"]
            observe_code(code)
            result = execute_python(code)
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


SYSTEM_PROMPT = """You are a UCC filing data analyst agent. You can write and execute Python code
to analyze UCC filing data, and you can search for specific filings.

## Available Data
When you use run_python_code, a variable called FILINGS is pre-loaded. It's a list of dicts:
- filing_number, type, state, filing_date, expiration_date, status
- debtor_name, secured_party_name, collateral_description

## How to Work
1. For analytical questions (counts, averages, comparisons), write Python code
2. For specific filing lookups, use search_filings
3. Always print() your results — that's how you see the output
4. If your code errors, read the message and fix it
5. Use standard library only (datetime, collections, etc.)
"""


# =============================================================================
# REACT AGENT LOOP — SOLUTION
# =============================================================================

def run_code_agent(user_query: str, max_turns: int = 8) -> str:
    """Run a ReAct agent that can write and execute Python code."""
    observe("QUERY", user_query)

    messages = [{"role": "user", "content": user_query}]

    for turn in range(max_turns):
        response = client.messages.create(
            model=MODEL,
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=messages,
        )

        if response.stop_reason != "tool_use":
            final_text = ""
            for block in response.content:
                if hasattr(block, "text"):
                    final_text += block.text
            observe("RESPONSE", final_text[:200] + "..." if len(final_text) > 200 else final_text)
            return final_text

        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                result = execute_tool(block.name, block.input)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result,
                })

        messages.append({"role": "assistant", "content": response.content})
        messages.append({"role": "user", "content": tool_results})

    return "Agent did not complete within max turns."


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("M15 Lab — Code Interpreter & Sandbox Execution (SOLUTION)")
    print("=" * 60)

    print("\n\n>>> Query 1: Count filings by state")
    result1 = run_code_agent("Count UCC filings by state and show the results")
    print(f"\nFINAL ANSWER:\n{result1}")

    print("\n\n>>> Query 2: Average days until expiration")
    result2 = run_code_agent("Calculate the average number of days until expiration for all active filings")
    print(f"\nFINAL ANSWER:\n{result2}")

    print("\n\n>>> Query 3: Blanket vs specific collateral")
    result3 = run_code_agent("What percentage of filings have blanket liens vs specific collateral?")
    print(f"\nFINAL ANSWER:\n{result3}")
