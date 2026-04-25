"""
M15B — Coordinator + Subagents (Starter)
==========================================
Upgrade from single agent to coordinator + 2 specialist subagents:
- Filing Search Subagent: searches and retrieves filings
- Risk Analysis Subagent: calculates risk scores and profiles

The coordinator receives user questions, delegates to the right
subagent(s), passes context EXPLICITLY, and synthesizes results.

Usage:
    python coordinator.py
"""

import json
import os
from dotenv import load_dotenv

load_dotenv()

import anthropic
from config import MODEL, MAX_SUBAGENT_TURNS, MAX_HISTORY_TURNS
from tools import TOOL_DEFINITIONS, execute_tool

client = anthropic.Anthropic()


# =============================================================================
# OBSERVATION HELPERS (complete — do not modify)
# =============================================================================

def observe(label: str, message: str) -> None:
    print(f"\n{'=' * 60}")
    print(f"[{label}] {message}")
    print(f"{'=' * 60}")


def observe_agent(name: str, action: str) -> None:
    print(f"\n{'─' * 60}")
    print(f"[AGENT: {name}] {action}")
    print(f"{'─' * 60}")


def observe_handoff(from_a: str, to_a: str, size: int) -> None:
    print(f"\n{'─' * 60}")
    print(f"[HANDOFF] {from_a} → {to_a} ({size} chars)")
    print(f"{'─' * 60}")


# =============================================================================
# SUBAGENT TOOL SETS (complete — do not modify)
# =============================================================================

# Filing Search Subagent gets search and details tools
FILING_SEARCH_TOOLS = [t for t in TOOL_DEFINITIONS if t["name"] in ("search_filings", "get_filing_details")]

# Risk Analysis Subagent gets risk and search tools (search for context)
RISK_ANALYSIS_TOOLS = [t for t in TOOL_DEFINITIONS if t["name"] in ("calculate_risk_score", "search_filings")]


# =============================================================================
# SUBAGENT RUNNER — YOUR CODE HERE
# =============================================================================

def run_subagent(agent_name: str, system_prompt: str, task: str,
                 tools: list, max_turns: int = None) -> str:
    """
    Run a specialist subagent with isolated context.

    CRITICAL: Each subagent gets a FRESH conversation. It does NOT see
    the coordinator's history. Context must be in the task string.

    Args:
        agent_name: For logging ("Filing Search", "Risk Analysis")
        system_prompt: The subagent's role and instructions
        task: Specific task including any context from coordinator
        tools: Tool definitions for this subagent
        max_turns: Max ReAct loop iterations

    Returns:
        The subagent's text response
    """
    if max_turns is None:
        max_turns = MAX_SUBAGENT_TURNS

    observe_agent(agent_name, f"Starting: {task[:100]}...")

    # ------------------------------------------------------------------
    # TODO 1: Implement run_subagent()
    #   - Create fresh messages list with task as user message
    #   - ReAct loop: call Claude → check stop_reason → execute tools → loop
    #   - Return final text
    #   - Handle errors gracefully (return error message, don't crash)
    # ------------------------------------------------------------------
    pass


# =============================================================================
# SPECIALIST SUBAGENTS — YOUR CODE HERE
# =============================================================================

def run_filing_search(task: str) -> str:
    """
    Filing Search Subagent — searches for and retrieves UCC filings.
    Tools: search_filings, get_filing_details
    """
    # ------------------------------------------------------------------
    # TODO 2: Implement run_filing_search()
    #   - Define a focused system prompt for the filing search role
    #   - Call run_subagent("Filing Search", system_prompt, task, FILING_SEARCH_TOOLS)
    # ------------------------------------------------------------------
    pass


def run_risk_analysis(task: str) -> str:
    """
    Risk Analysis Subagent — calculates lien risk profiles.
    Tools: calculate_risk_score, search_filings (for context)
    """
    # ------------------------------------------------------------------
    # TODO 3: Implement run_risk_analysis()
    #   - Define a focused system prompt for the risk analysis role
    #   - Call run_subagent("Risk Analysis", system_prompt, task, RISK_ANALYSIS_TOOLS)
    # ------------------------------------------------------------------
    pass


# =============================================================================
# COORDINATOR — YOUR CODE HERE
# =============================================================================

class Coordinator:
    """
    Orchestrates the UCC Filing Research System.

    Receives user questions, decides which subagent(s) to invoke,
    passes context explicitly, and synthesizes results.
    Maintains conversation history for multi-turn follow-ups.
    """

    def __init__(self):
        self.history: list[dict] = []  # [{role, content}, ...]

    def _get_history_context(self) -> str:
        """Format recent history as context for the coordinator."""
        if not self.history:
            return "No previous conversation."
        lines = ["## Previous Conversation"]
        for entry in self.history[-MAX_HISTORY_TURNS * 2:]:
            role = "User" if entry["role"] == "user" else "Assistant"
            lines.append(f"**{role}**: {entry['content'][:200]}")
        return "\n".join(lines)

    def run(self, user_query: str) -> str:
        """
        Process a user query through the coordinator.

        The coordinator:
        1. Looks at the query + conversation history
        2. Decides which subagent(s) to call
        3. Calls subagents with EXPLICIT context
        4. Synthesizes the results
        5. Updates conversation history

        Args:
            user_query: The user's question

        Returns:
            The synthesized response
        """
        observe("COORDINATOR", f"Received: {user_query}")

        # ------------------------------------------------------------------
        # TODO 4: Implement the coordinator
        #   - Add user query to history
        #   - Get history context
        #   - Ask Claude to decide which subagent(s) to invoke:
        #     a) Use a small classification prompt to determine intent
        #     b) Or use simple keyword heuristics (simpler approach):
        #        - "risk" / "exposure" / "assess" → risk analysis
        #        - "find" / "search" / "filings" → filing search
        #        - If both or unclear, call both
        #   - Call the appropriate subagent(s) with context
        #   - If calling both: pass filing results to risk analysis
        #   - Synthesize results with a final Claude call
        #   - Add response to history
        #   - Return the synthesized response
        # ------------------------------------------------------------------
        pass


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("M15B — Coordinator + Subagents")
    print("=" * 60)

    coord = Coordinator()

    # Turn 1: Filing search
    print("\n\n>>> Turn 1: Find Acme filings in New York")
    r1 = coord.run("Find all UCC filings for Acme Corporation in New York")
    print(f"\nANSWER:\n{r1}")

    # Turn 2: Risk assessment (should recall Turn 1 context)
    print("\n\n>>> Turn 2: Risk assessment")
    r2 = coord.run("What's the overall risk level for Acme Corporation?")
    print(f"\nANSWER:\n{r2}")

    # Turn 3: Follow-up (tests conversation memory)
    print("\n\n>>> Turn 3: Follow-up about Texas")
    r3 = coord.run("What about their filings in Texas?")
    print(f"\nANSWER:\n{r3}")

    # Turn 4: Error case
    print("\n\n>>> Turn 4: Nonexistent entity")
    r4 = coord.run("Find filings for NonExistent Corp")
    print(f"\nANSWER:\n{r4}")
