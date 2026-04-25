"""
M11 Lab - Step 1: Working Memory Scratchpad (Starter)
=====================================================
Build a key-value working memory that an agent uses to track
current task state across tool calls and conversation turns.

KEY CONCEPT: Working memory is the agent's "scratchpad" — it holds
the current debtor being researched, findings so far, and search
history. This context is injected into every system prompt so Claude
always knows where it left off.

Usage:
    python working_memory.py
"""

import json
import sys
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Add parent directories so shared imports work when run from any location
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import anthropic
from shared.mock_ucc_data import search_filings, get_filing_by_number

client = anthropic.Anthropic()
MODEL = "claude-sonnet-4-20250514"


# =============================================================================
# OBSERVATION HELPERS (complete -- do not modify)
# =============================================================================

def observe(label: str, message: str) -> None:
    """Print a labeled observation line."""
    print(f"\n{'=' * 60}")
    print(f"[{label}] {message}")
    print(f"{'=' * 60}")


def observe_tool_call(tool_name: str, tool_input: dict) -> None:
    """Log a tool call."""
    print(f"\n{'─' * 60}")
    print(f"[USING TOOL] {tool_name}")
    print(f"[INPUT]      {json.dumps(tool_input, indent=2)}")
    print(f"{'─' * 60}")


def observe_tool_result(result) -> None:
    """Log a tool result."""
    print(f"\n{'─' * 60}")
    print(f"[TOOL RESULT]")
    if isinstance(result, str):
        print(result)
    else:
        print(json.dumps(result, indent=2))
    print(f"{'─' * 60}")


def observe_memory(memory_dict: dict) -> None:
    """Log the current state of working memory."""
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
# TOOL DEFINITIONS (complete -- do not modify)
# =============================================================================

TOOLS = [
    {
        "name": "search_ucc_filings",
        "description": "Search UCC filings by debtor name, state, status, or filing type. Returns matching filings.",
        "input_schema": {
            "type": "object",
            "properties": {
                "debtor_name": {
                    "type": "string",
                    "description": "Debtor name to search for (partial match, case-insensitive)"
                },
                "state": {
                    "type": "string",
                    "description": "State to filter by, e.g. 'New York', 'California'"
                },
                "status": {
                    "type": "string",
                    "description": "Filing status: 'Active', 'Terminated', 'Lapsed', 'Amendment'"
                }
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
                "filing_number": {
                    "type": "string",
                    "description": "The UCC filing number, e.g. 'UCC-2024-NY-0012847'"
                }
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
                "key": {
                    "type": "string",
                    "description": "Memory key, e.g. 'current_debtor', 'findings_so_far', 'search_history'"
                },
                "value": {
                    "type": "string",
                    "description": "Value to store (will be appended if key is 'findings_so_far' or 'search_history')"
                }
            },
            "required": ["key", "value"]
        }
    }
]


# =============================================================================
# WORKING MEMORY CLASS — YOUR CODE HERE
# =============================================================================

class WorkingMemory:
    """
    A key-value scratchpad for tracking current task state.

    The agent uses this to remember:
    - current_debtor: who we are researching
    - findings_so_far: list of discoveries made during research
    - search_history: list of searches performed
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
        """
        Format all working memory entries into a string suitable for
        injection into the system prompt.

        Returns a string like:
            ## Current Working Memory
            - current_debtor: Greenfield Logistics LLC
            - findings_so_far:
              1. Found active filing in NY
              2. Blanket lien by Atlantic Capital
            - search_history:
              1. Searched by debtor name 'Greenfield'
        """
        # ------------------------------------------------------------------
        # TODO 1: Implement get_context()
        #   - If memory is empty, return "## Current Working Memory\nNo active research state."
        #   - Otherwise, build a formatted string with all key-value pairs
        #   - For list values, number each item
        #   - For string/other values, display directly
        # ------------------------------------------------------------------
        pass

    def to_dict(self) -> dict:
        """
        Serialize working memory to a plain dict for JSON persistence.
        """
        # ------------------------------------------------------------------
        # TODO 2: Implement to_dict()
        #   - Return a copy of the internal store
        #   - This should be JSON-serializable
        # ------------------------------------------------------------------
        pass

    @classmethod
    def from_dict(cls, data: dict) -> "WorkingMemory":
        """
        Deserialize working memory from a dict.
        """
        # ------------------------------------------------------------------
        # TODO 3: Implement from_dict()
        #   - Create a new WorkingMemory instance
        #   - Populate its _store with the provided data
        #   - Return the instance
        # ------------------------------------------------------------------
        pass


# =============================================================================
# TOOL EXECUTION (complete -- do not modify)
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
            # Append-style keys accumulate into lists
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
# AGENT WITH WORKING MEMORY — YOUR CODE HERE
# =============================================================================

def run_research_agent(user_message: str, memory: WorkingMemory, max_turns: int = 10) -> str:
    """
    Run a research agent that uses working memory to track state.

    The agent:
    1. Gets the current working memory context
    2. Includes it in the system prompt
    3. Runs the tool loop
    4. Updates working memory after each tool call
    5. Returns the final response

    Returns Claude's final text response.
    """
    observe("QUERY", user_message)

    # ------------------------------------------------------------------
    # TODO 4: Build the system prompt with working memory context
    #   - Start with a base system prompt explaining the agent's role
    #   - Call memory.get_context() and append it to the system prompt
    #   - The system prompt should instruct Claude to:
    #     a) Research UCC filings as requested
    #     b) Use update_working_memory after each search/finding
    #     c) Track current_debtor, findings_so_far, search_history
    # ------------------------------------------------------------------
    system_prompt = ""  # Replace with your system prompt
    pass

    messages = [{"role": "user", "content": user_message}]

    # ------------------------------------------------------------------
    # TODO 5: Implement the agent loop
    #   - Loop up to max_turns
    #   - Call client.messages.create with model, max_tokens, system, tools, messages
    #   - If stop_reason != "tool_use", extract text and return
    #   - Otherwise, process each tool_use block:
    #     a) Log with observe_tool_call
    #     b) Execute with execute_tool
    #     c) Log with observe_tool_result
    #   - Append assistant response and tool results to messages
    #   - After each loop iteration, log memory state with observe_memory
    # ------------------------------------------------------------------
    pass

    return "Agent did not produce a final response within max turns."


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("M11 Lab - Step 1: Working Memory Scratchpad")
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
