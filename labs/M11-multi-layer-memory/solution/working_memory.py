"""
M11 Lab - Step 1: Working Memory Scratchpad (Solution)
=====================================================
Complete solution: key-value working memory that an agent uses
to track current task state across tool calls and conversation turns.

Usage:
    python working_memory.py
"""

import json
import sys
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import anthropic
from shared.mock_ucc_data import search_filings, get_filing_by_number

client = anthropic.Anthropic()
MODEL = "claude-sonnet-4-6"


# =============================================================================
# OBSERVATION HELPERS
# =============================================================================

def observe(label: str, message: str) -> None:
    print(f"\n{'=' * 60}")
    print(f"[{label}] {message}")
    print(f"{'=' * 60}")


def observe_tool_call(tool_name: str, tool_input: dict) -> None:
    print(f"\n{'─' * 60}")
    print(f"[USING TOOL] {tool_name}")
    print(f"[INPUT]      {json.dumps(tool_input, indent=2)}")
    print(f"{'─' * 60}")


def observe_tool_result(result) -> None:
    print(f"\n{'─' * 60}")
    print(f"[TOOL RESULT]")
    if isinstance(result, str):
        print(result)
    else:
        print(json.dumps(result, indent=2))
    print(f"{'─' * 60}")


def observe_memory(memory_dict: dict) -> None:
    print(f"\n{'─' * 60}")
    print(f"[WORKING MEMORY STATE]")
    for key, value in memory_dict.items():
        if isinstance(value, list):
            print(f"  {key}: [{len(value)} items]")
            for item in value:
                print(f"    - {item}")
        else:
            print(f"  {key}: {value}")
    print(f"{'─' * 60}")


# =============================================================================
# TOOL DEFINITIONS
# =============================================================================

TOOLS = [
    {
        "name": "search_ucc_filings",
        "description": "Search UCC filings by debtor name, state, status, or filing type. Returns matching filings.",
        "input_schema": {
            "type": "object",
            "properties": {
                "debtor_name": {"type": "string", "description": "Debtor name to search for (partial match, case-insensitive)"},
                "state": {"type": "string", "description": "State to filter by, e.g. 'New York', 'California'"},
                "status": {"type": "string", "description": "Filing status: 'Active', 'Terminated', 'Lapsed', 'Amendment'"}
            },
            "required": []
        }
    },
    {
        "name": "get_filing_details",
        "description": "Get full details of a specific UCC filing by its filing number.",
        "input_schema": {
            "type": "object",
            "properties": {
                "filing_number": {"type": "string", "description": "The UCC filing number, e.g. 'UCC-2024-NY-0012847'"}
            },
            "required": ["filing_number"]
        }
    },
    {
        "name": "update_working_memory",
        "description": "Update the agent's working memory with new information. Use this after every tool call to track research state.",
        "input_schema": {
            "type": "object",
            "properties": {
                "key": {"type": "string", "description": "Memory key, e.g. 'current_debtor', 'findings_so_far', 'search_history'"},
                "value": {"type": "string", "description": "Value to store (will be appended if key is 'findings_so_far' or 'search_history')"}
            },
            "required": ["key", "value"]
        }
    }
]


# =============================================================================
# WORKING MEMORY CLASS — SOLUTION
# =============================================================================

class WorkingMemory:
    """
    A key-value scratchpad for tracking current task state.
    """

    def __init__(self):
        self._store: dict = {}

    def set(self, key: str, value) -> None:
        """Set a key-value pair in working memory."""
        self._store[key] = value

    def get(self, key: str, default=None):
        """Get a value by key, returning default if not found."""
        return self._store.get(key, default)

    def delete(self, key: str) -> bool:
        """Delete a key from working memory. Returns True if key existed."""
        if key in self._store:
            del self._store[key]
            return True
        return False

    def clear(self) -> None:
        """Clear all working memory."""
        self._store.clear()

    def get_context(self) -> str:
        """Format all working memory entries into a string for the system prompt."""
        if not self._store:
            return "## Current Working Memory\nNo active research state."

        lines = ["## Current Working Memory"]
        for key, value in self._store.items():
            if isinstance(value, list):
                lines.append(f"- {key}:")
                for i, item in enumerate(value, 1):
                    lines.append(f"  {i}. {item}")
            else:
                lines.append(f"- {key}: {value}")
        return "\n".join(lines)

    def to_dict(self) -> dict:
        """Serialize working memory to a plain dict for JSON persistence."""
        return dict(self._store)

    @classmethod
    def from_dict(cls, data: dict) -> "WorkingMemory":
        """Deserialize working memory from a dict."""
        mem = cls()
        mem._store = dict(data)
        return mem


# =============================================================================
# TOOL EXECUTION
# =============================================================================

def execute_tool(tool_name: str, tool_input: dict, memory: WorkingMemory) -> str:
    """Execute a tool and return the result as a string."""
    try:
        if tool_name == "search_ucc_filings":
            results = search_filings(
                debtor_name=tool_input.get("debtor_name"),
                state=tool_input.get("state"),
                status=tool_input.get("status"),
                filing_type=tool_input.get("filing_type")
            )
            return json.dumps([{
                "filing_number": f["filing_number"],
                "debtor": f["debtor"]["name"],
                "secured_party": f["secured_party"]["name"],
                "state": f["state"],
                "status": f["status"],
                "collateral": f["collateral_description"][:100] + "..."
            } for f in results], indent=2)

        elif tool_name == "get_filing_details":
            filing = get_filing_by_number(tool_input["filing_number"])
            if filing:
                return json.dumps(filing, indent=2, default=str)
            return json.dumps({"error": f"Filing {tool_input['filing_number']} not found"})

        elif tool_name == "update_working_memory":
            key = tool_input["key"]
            value = tool_input["value"]
            if key in ("findings_so_far", "search_history"):
                existing = memory.get(key, [])
                if not isinstance(existing, list):
                    existing = [existing]
                existing.append(value)
                memory.set(key, existing)
            else:
                memory.set(key, value)
            return json.dumps({"status": "ok", "key": key, "value": memory.get(key)})

        else:
            return json.dumps({"error": f"Unknown tool: {tool_name}"})
    except Exception as e:
        return json.dumps({"error": f"Tool execution failed: {str(e)}"})


# =============================================================================
# AGENT WITH WORKING MEMORY — SOLUTION
# =============================================================================

def run_research_agent(user_message: str, memory: WorkingMemory, max_turns: int = 10) -> str:
    """
    Run a research agent that uses working memory to track state.
    Returns Claude's final text response.
    """
    observe("QUERY", user_message)

    # Build system prompt with working memory context
    memory_context = memory.get_context()
    system_prompt = f"""You are a UCC (Uniform Commercial Code) filing research agent. You help users
research UCC filings, track liens, and assess debtor risk.

You have a working memory scratchpad to track your research state. ALWAYS use
the update_working_memory tool to record:
- current_debtor: the name of the entity you are researching
- findings_so_far: each significant finding (appended as a list)
- search_history: each search you perform (appended as a list)

Update working memory AFTER each search or discovery. This ensures you can
resume research across conversation turns.

{memory_context}"""

    messages = [{"role": "user", "content": user_message}]

    # Agent loop
    for turn in range(max_turns):
        response = client.messages.create(
            model=MODEL,
            max_tokens=4096,
            system=system_prompt,
            tools=TOOLS,
            messages=messages,
        )

        # If Claude is done, extract text and return
        if response.stop_reason != "tool_use":
            final_text = ""
            for block in response.content:
                if hasattr(block, "text"):
                    final_text += block.text
            observe("RESPONSE", final_text[:200] + "..." if len(final_text) > 200 else final_text)
            return final_text

        # Process tool calls
        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                observe_tool_call(block.name, block.input)
                result = execute_tool(block.name, block.input, memory)
                observe_tool_result(result)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result,
                })

        # Append assistant message and tool results
        messages.append({"role": "assistant", "content": response.content})
        messages.append({"role": "user", "content": tool_results})

        # Log current memory state
        observe_memory(memory.to_dict())

    return "Agent did not produce a final response within max turns."


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("M11 Lab - Step 1: Working Memory Scratchpad (SOLUTION)")
    print("=" * 60)

    memory = WorkingMemory()

    # Turn 1: Start researching a debtor
    print("\n\n>>> Turn 1: Start research")
    result1 = run_research_agent(
        "Research Greenfield Logistics LLC. Find all their UCC filings and tell me about any liens.",
        memory
    )
    print(f"\nFINAL ANSWER: {result1}")

    # Show memory state after turn 1
    print("\n\n>>> Working Memory after Turn 1:")
    observe_memory(memory.to_dict())

    # Turn 2: Continue research (memory carries forward)
    print("\n\n>>> Turn 2: Follow-up question (memory carries forward)")
    result2 = run_research_agent(
        "What secured parties are involved with this debtor? Are there any blanket liens?",
        memory
    )
    print(f"\nFINAL ANSWER: {result2}")

    # Show final memory state
    print("\n\n>>> Working Memory after Turn 2:")
    observe_memory(memory.to_dict())

    # Demonstrate persistence
    print("\n\n>>> Persistence Test: Serialize and restore")
    saved = json.dumps(memory.to_dict(), indent=2)
    print(f"Saved memory: {saved}")
    restored_memory = WorkingMemory.from_dict(json.loads(saved))
    print(f"Restored memory context:\n{restored_memory.get_context()}")
