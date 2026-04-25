"""
M15B — Coordinator + Subagents (Solution)
===========================================
Complete coordinator with 2 specialist subagents and conversation memory.

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
# OBSERVATION HELPERS
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
# SUBAGENT TOOL SETS
# =============================================================================

FILING_SEARCH_TOOLS = [t for t in TOOL_DEFINITIONS if t["name"] in ("search_filings", "get_filing_details")]
RISK_ANALYSIS_TOOLS = [t for t in TOOL_DEFINITIONS if t["name"] in ("calculate_risk_score", "search_filings")]


# =============================================================================
# SUBAGENT RUNNER
# =============================================================================

def run_subagent(agent_name: str, system_prompt: str, task: str,
                 tools: list, max_turns: int = None) -> str:
    """Run a specialist subagent with isolated context."""
    if max_turns is None:
        max_turns = MAX_SUBAGENT_TURNS

    observe_agent(agent_name, f"Starting: {task[:100]}...")
    messages = [{"role": "user", "content": task}]

    try:
        for turn in range(max_turns):
            response = client.messages.create(
                model=MODEL,
                max_tokens=4096,
                system=system_prompt,
                tools=tools,
                messages=messages,
            )

            if response.stop_reason != "tool_use":
                text = ""
                for block in response.content:
                    if hasattr(block, "text"):
                        text += block.text
                observe_agent(agent_name, f"Complete ({len(text)} chars)")
                return text

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

        return f"{agent_name} did not complete within {max_turns} turns."

    except Exception as e:
        observe_agent(agent_name, f"Error: {str(e)}")
        return json.dumps({"error": f"{agent_name} failed: {str(e)}"})


# =============================================================================
# SPECIALIST SUBAGENTS
# =============================================================================

def run_filing_search(task: str) -> str:
    """Filing Search Subagent."""
    system_prompt = """You are a UCC filing search specialist. Your ONLY job is to search for
and retrieve UCC filing records. Use search_filings to find filings by debtor name
and/or state, then use get_filing_details for full information.

Report your findings as structured data: list each filing with its number, debtor,
secured party, state, status, type, filing date, and collateral description.
Be thorough but concise. If no filings found, say so clearly."""

    return run_subagent("Filing Search", system_prompt, task, FILING_SEARCH_TOOLS)


def run_risk_analysis(task: str) -> str:
    """Risk Analysis Subagent."""
    system_prompt = """You are a UCC lien risk analysis specialist. Your ONLY job is to
assess lien risk for entities. Use calculate_risk_score to get quantitative risk profiles.
If needed, use search_filings for additional context.

Focus on: risk score, risk level, number of liens, collateral breadth (blanket vs specific),
number of jurisdictions, secured party concentration. Always include the recommendation.
Cite specific numbers and filing details."""

    return run_subagent("Risk Analysis", system_prompt, task, RISK_ANALYSIS_TOOLS)


# =============================================================================
# COORDINATOR
# =============================================================================

class Coordinator:
    """Orchestrates the UCC Filing Research System with conversation memory."""

    def __init__(self):
        self.history: list[dict] = []

    def _get_history_context(self) -> str:
        if not self.history:
            return "No previous conversation."
        lines = ["## Previous Conversation"]
        for entry in self.history[-MAX_HISTORY_TURNS * 2:]:
            role = "User" if entry["role"] == "user" else "Assistant"
            content = entry["content"][:200]
            lines.append(f"**{role}**: {content}")
        return "\n".join(lines)

    def _classify_intent(self, query: str) -> str:
        """Determine which subagent(s) to invoke based on the query."""
        q = query.lower()
        needs_risk = any(w in q for w in ["risk", "exposure", "assess", "evaluate", "how risky", "risk level"])
        needs_search = any(w in q for w in ["find", "search", "filing", "filings", "look up", "what about"])

        if needs_risk and needs_search:
            return "both"
        elif needs_risk:
            return "risk"
        elif needs_search:
            return "search"
        else:
            # Default: do both for comprehensive research
            return "both"

    def run(self, user_query: str) -> str:
        """Process a user query through the coordinator."""
        observe("COORDINATOR", f"Received: {user_query}")

        # Add to history
        self.history.append({"role": "user", "content": user_query})
        history_context = self._get_history_context()

        # Classify intent
        intent = self._classify_intent(user_query)
        observe("COORDINATOR", f"Intent: {intent}")

        # Build task with conversation context
        task_with_context = f"""{user_query}

{history_context}"""

        # Execute subagent(s)
        filing_results = None
        risk_results = None

        if intent in ("search", "both"):
            observe("COORDINATOR", "Dispatching Filing Search subagent")
            filing_results = run_filing_search(task_with_context)
            observe_handoff("Filing Search", "Coordinator", len(filing_results))

        if intent in ("risk", "both"):
            # If we have filing results, pass them as context
            risk_task = task_with_context
            if filing_results:
                risk_task += f"\n\n## Filing Data (from search)\n{filing_results}"
            observe("COORDINATOR", "Dispatching Risk Analysis subagent")
            risk_results = run_risk_analysis(risk_task)
            observe_handoff("Risk Analysis", "Coordinator", len(risk_results))

        # Synthesize results
        observe("COORDINATOR", "Synthesizing results")
        synthesis_parts = [f"User query: {user_query}"]
        if filing_results:
            synthesis_parts.append(f"## Filing Search Results\n{filing_results}")
        if risk_results:
            synthesis_parts.append(f"## Risk Analysis Results\n{risk_results}")
        synthesis_parts.append(f"\n{history_context}")

        synthesis = client.messages.create(
            model=MODEL,
            max_tokens=4096,
            system="""You are a coordinator synthesizing research results about UCC filings.
Combine the subagent findings into a clear, comprehensive response.
Cite specific filing numbers and data. If referencing previous conversation, be explicit about what changed.""",
            messages=[{"role": "user", "content": "\n\n".join(synthesis_parts)}],
        )

        final = ""
        for block in synthesis.content:
            if hasattr(block, "text"):
                final += block.text

        # Add to history
        self.history.append({"role": "assistant", "content": final[:500]})

        observe("COORDINATOR", "Complete")
        return final


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("M15B — Coordinator + Subagents (SOLUTION)")
    print("=" * 60)

    coord = Coordinator()

    print("\n\n>>> Turn 1: Find Acme filings in New York")
    r1 = coord.run("Find all UCC filings for Acme Corporation in New York")
    print(f"\nANSWER:\n{r1}")

    print("\n\n>>> Turn 2: Risk assessment")
    r2 = coord.run("What's the overall risk level for Acme Corporation?")
    print(f"\nANSWER:\n{r2}")

    print("\n\n>>> Turn 3: Follow-up about Texas")
    r3 = coord.run("What about their filings in Texas?")
    print(f"\nANSWER:\n{r3}")

    print("\n\n>>> Turn 4: Nonexistent entity")
    r4 = coord.run("Find filings for NonExistent Corp")
    print(f"\nANSWER:\n{r4}")
