"""
M11 Lab - Step 3: Full 3-Tier Memory Agent (Starter)
====================================================
Combine working memory, episodic memory, and procedural memory
into a single agent that orchestrates all three tiers during
UCC research sessions.

KEY CONCEPT: A production agent needs all three memory tiers
working together. Procedural memory tells it HOW to research
(learned patterns). Episodic memory tells it WHAT it has seen
before (past experience). Working memory tracks WHERE it is
right now (current state). The orchestration layer decides
which tier to consult at each step.

Usage:
    python memory_agent.py
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
import chromadb
from shared.mock_ucc_data import search_filings, get_filing_by_number

client = anthropic.Anthropic()
MODEL = "claude-sonnet-4-6"


# =============================================================================
# OBSERVATION HELPERS (complete -- do not modify)
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


def observe_memory(label: str, data) -> None:
    print(f"\n{'─' * 60}")
    print(f"[{label}]")
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, list):
                print(f"  {key}: [{len(value)} items]")
                for item in value:
                    if isinstance(item, str):
                        print(f"    - {item}")
                    else:
                        print(f"    - {json.dumps(item, default=str)}")
            else:
                print(f"  {key}: {value}")
    else:
        print(f"  {data}")
    print(f"{'─' * 60}")


# =============================================================================
# PROCEDURAL MEMORY (complete -- do not modify)
# These are learned patterns that encode HOW to do UCC research.
# =============================================================================

PROCEDURAL_MEMORY = {
    "entity_search": {
        "description": "Standard entity research workflow",
        "steps": [
            "search by debtor name",
            "get filing details",
            "check for amendments",
            "assess risk"
        ],
        "triggers": ["research", "investigate", "look up", "find", "search for"]
    },
    "risk_assessment": {
        "description": "Lien risk evaluation pattern",
        "steps": [
            "count active filings",
            "check for blanket liens",
            "check expiration dates",
            "flag multiple secured parties"
        ],
        "triggers": ["risk", "assess", "evaluate", "how risky", "lien risk"]
    },
    "amendment_tracking": {
        "description": "Track changes to UCC filings over time",
        "steps": [
            "find original filing",
            "search for UCC-3 amendments",
            "compare collateral descriptions",
            "build timeline"
        ],
        "triggers": ["amendment", "changed", "modified", "updated", "history"]
    },
    "multi_state_search": {
        "description": "Search across multiple states for related filings",
        "steps": [
            "search debtor in primary state",
            "check state of incorporation",
            "search in Delaware (common incorporation state)",
            "search in other likely states",
            "consolidate findings"
        ],
        "triggers": ["multi-state", "all states", "everywhere", "nationwide", "cross-state"]
    }
}


# =============================================================================
# WORKING MEMORY CLASS (complete -- from Step 1)
# =============================================================================

class WorkingMemory:
    def __init__(self):
        self._store: dict = {}

    def set(self, key: str, value) -> None:
        self._store[key] = value

    def get(self, key: str, default=None):
        return self._store.get(key, default)

    def delete(self, key: str) -> bool:
        if key in self._store:
            del self._store[key]
            return True
        return False

    def clear(self) -> None:
        self._store.clear()

    def get_context(self) -> str:
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
        return dict(self._store)

    @classmethod
    def from_dict(cls, data: dict) -> "WorkingMemory":
        mem = cls()
        mem._store = dict(data)
        return mem


# =============================================================================
# EPISODIC MEMORY CLASS (complete -- from Step 2)
# =============================================================================

class EpisodicMemory:
    def __init__(self, collection_name: str = "ucc_agent_episodes"):
        self._client = chromadb.Client()
        self._collection = self._client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        self._episode_count = 0

    def store_episode(self, summary: str, metadata: dict = None) -> str:
        episode_id = f"episode_{self._episode_count}"
        self._episode_count += 1
        if metadata is None:
            metadata = {}
        if "timestamp" not in metadata:
            metadata["timestamp"] = datetime.now().isoformat()
        clean_meta = {k: str(v) if not isinstance(v, (str, int, float, bool)) else v for k, v in metadata.items()}
        self._collection.add(
            documents=[summary],
            metadatas=[clean_meta],
            ids=[episode_id]
        )
        return episode_id

    def recall(self, query: str, n_results: int = 3) -> list[dict]:
        try:
            count = self._collection.count()
            if count == 0:
                return []
            n = min(n_results, count)
            results = self._collection.query(query_texts=[query], n_results=n)
            episodes = []
            for i in range(len(results["documents"][0])):
                episodes.append({
                    "summary": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                    "similarity": 1 - results["distances"][0][i] if results["distances"] else 0
                })
            return sorted(episodes, key=lambda x: x["similarity"], reverse=True)
        except Exception:
            return []

    def get_recent(self, n: int = 5) -> list[dict]:
        try:
            all_data = self._collection.get()
            if not all_data["documents"]:
                return []
            episodes = []
            for i in range(len(all_data["documents"])):
                episodes.append({
                    "summary": all_data["documents"][i],
                    "metadata": all_data["metadatas"][i] if all_data["metadatas"] else {}
                })
            episodes.sort(key=lambda x: x.get("metadata", {}).get("timestamp", ""), reverse=True)
            return episodes[:n]
        except Exception:
            return []

    def populate_mock_episodes(self) -> None:
        mock = [
            {"summary": "Researched Greenfield Logistics — found active filing in NY, blanket lien by Atlantic Capital Partners covering all accounts receivable, inventory, equipment, and general intangibles.", "metadata": {"debtor": "Greenfield Logistics LLC", "state": "New York", "risk_level": "high", "timestamp": "2024-08-15T10:30:00Z"}},
            {"summary": "Investigated Pacific Ridge Technologies — DE incorporation but CA filing, extensive IP collateral including patents and trademarks, secured by Silicon Valley Bank.", "metadata": {"debtor": "Pacific Ridge Technologies Inc", "state": "California", "risk_level": "medium", "timestamp": "2024-08-20T14:15:00Z"}},
            {"summary": "Searched for Lone Star Energy — found equipment-specific lien on Caterpillar excavators and Liebherr crane, secured by Wells Fargo Equipment Finance in Texas.", "metadata": {"debtor": "Lone Star Energy Solutions LP", "state": "Texas", "risk_level": "low", "timestamp": "2024-09-02T09:00:00Z"}},
            {"summary": "Looked into Sunshine Medical Group — found UCC-3 amendment adding MRI equipment and CT scanner to existing lien, TD Bank is secured party in Florida.", "metadata": {"debtor": "Sunshine Medical Group PA", "state": "Florida", "risk_level": "medium", "timestamp": "2024-09-10T11:45:00Z"}},
            {"summary": "Checked Nextera Holdings — massive blanket lien by JPMorgan Chase covering all assets including commercial tort claims, minerals, and investment property in Delaware.", "metadata": {"debtor": "Nextera Holdings Corp", "state": "Delaware", "risk_level": "critical", "timestamp": "2024-09-15T16:20:00Z"}},
        ]
        print("[EPISODIC MEMORY] Loading mock episodes...")
        for ep in mock:
            eid = self.store_episode(ep["summary"], ep["metadata"])
            print(f"  Stored: {eid} — {ep['summary'][:60]}...")
        print(f"[EPISODIC MEMORY] {len(mock)} episodes loaded.\n")


# =============================================================================
# TOOL DEFINITIONS (complete -- do not modify)
# =============================================================================

TOOLS = [
    {
        "name": "search_ucc_filings",
        "description": "Search UCC filings by debtor name, state, status, or filing type.",
        "input_schema": {
            "type": "object",
            "properties": {
                "debtor_name": {"type": "string", "description": "Debtor name to search for"},
                "state": {"type": "string", "description": "State to filter by"},
                "status": {"type": "string", "description": "Filing status filter"}
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
                "filing_number": {"type": "string", "description": "The UCC filing number"}
            },
            "required": ["filing_number"]
        }
    },
    {
        "name": "recall_similar_research",
        "description": "Search episodic memory for similar past research sessions.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "What to search for in past research sessions"}
            },
            "required": ["query"]
        }
    },
    {
        "name": "update_working_memory",
        "description": "Update the agent's working memory with new information.",
        "input_schema": {
            "type": "object",
            "properties": {
                "key": {"type": "string", "description": "Memory key"},
                "value": {"type": "string", "description": "Value to store"}
            },
            "required": ["key", "value"]
        }
    },
    {
        "name": "get_procedural_pattern",
        "description": "Look up a procedural memory pattern for a given task type. Returns the step-by-step workflow.",
        "input_schema": {
            "type": "object",
            "properties": {
                "task_description": {"type": "string", "description": "Description of the task to find a pattern for"}
            },
            "required": ["task_description"]
        }
    }
]


# =============================================================================
# TOOL EXECUTION (complete -- do not modify)
# =============================================================================

def execute_tool(tool_name: str, tool_input: dict, agent: "MemoryAgent") -> str:
    """Execute a tool and return the result as a string."""
    try:
        if tool_name == "search_ucc_filings":
            results = search_filings(
                debtor_name=tool_input.get("debtor_name"),
                state=tool_input.get("state"),
                status=tool_input.get("status")
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

        elif tool_name == "recall_similar_research":
            episodes = agent.episodic_memory.recall(tool_input["query"], n_results=3)
            if episodes:
                return json.dumps([{
                    "summary": ep["summary"],
                    "similarity": round(ep.get("similarity", 0), 3),
                    "metadata": ep.get("metadata", {})
                } for ep in episodes], indent=2)
            return json.dumps({"message": "No similar past research found."})

        elif tool_name == "update_working_memory":
            key = tool_input["key"]
            value = tool_input["value"]
            if key in ("findings_so_far", "search_history"):
                existing = agent.working_memory.get(key, [])
                if not isinstance(existing, list):
                    existing = [existing]
                existing.append(value)
                agent.working_memory.set(key, existing)
            else:
                agent.working_memory.set(key, value)
            return json.dumps({"status": "ok", "key": key, "value": agent.working_memory.get(key)})

        elif tool_name == "get_procedural_pattern":
            task = tool_input["task_description"].lower()
            matched = []
            for pattern_name, pattern in PROCEDURAL_MEMORY.items():
                for trigger in pattern["triggers"]:
                    if trigger in task:
                        matched.append({
                            "pattern": pattern_name,
                            "description": pattern["description"],
                            "steps": pattern["steps"]
                        })
                        break
            if matched:
                observe_memory("PROCEDURAL MEMORY MATCH", {"patterns": matched})
                return json.dumps(matched, indent=2)
            return json.dumps({"message": "No matching procedural pattern found.", "available_patterns": list(PROCEDURAL_MEMORY.keys())})

        else:
            return json.dumps({"error": f"Unknown tool: {tool_name}"})
    except Exception as e:
        return json.dumps({"error": f"Tool execution failed: {str(e)}"})


# =============================================================================
# MEMORY AGENT CLASS — YOUR CODE HERE
# =============================================================================

class MemoryAgent:
    """
    A 3-tier memory agent that combines:
    - Working memory: current task state (key-value scratchpad)
    - Episodic memory: past research sessions (vector DB)
    - Procedural memory: learned research patterns (JSON)

    The agent orchestrates all three tiers during each research session.
    """

    def __init__(self):
        self.working_memory = WorkingMemory()
        self.episodic_memory = EpisodicMemory()
        self.procedural_memory = PROCEDURAL_MEMORY

    def initialize(self) -> None:
        """Load mock episodes into episodic memory."""
        self.episodic_memory.populate_mock_episodes()

    def get_system_prompt(self) -> str:
        """
        Build the full system prompt incorporating all three memory tiers.

        Returns a system prompt that includes:
        1. Agent role and capabilities
        2. Current working memory state
        3. Available procedural patterns
        4. Instructions to use episodic memory via recall tool
        """
        # ------------------------------------------------------------------
        # TODO 1: Build the system prompt
        #   - Start with the agent's role description
        #   - Include self.working_memory.get_context()
        #   - Include a summary of available procedural patterns
        #   - Instruct the agent to:
        #     a) FIRST check for a procedural pattern matching the task
        #     b) THEN recall similar past research from episodic memory
        #     c) Use working memory to track state throughout
        #     d) Follow the procedural pattern steps if one matches
        # ------------------------------------------------------------------
        pass

    def run(self, user_message: str, max_turns: int = 15) -> str:
        """
        Run a research session using all 3 memory tiers.

        The orchestration:
        1. Build system prompt with working memory + procedural patterns
        2. Agent checks procedural memory for relevant workflow
        3. Agent checks episodic memory for similar past research
        4. Agent uses working memory to track current research state
        5. Agent runs research with tools
        6. After completion, store the session as a new episode

        Returns Claude's final text response.
        """
        observe("QUERY", user_message)

        # ------------------------------------------------------------------
        # TODO 2: Implement the agent run method
        #   - Get the system prompt from self.get_system_prompt()
        #   - Create the messages list with the user message
        #   - Run the agent loop (up to max_turns):
        #     a) Call client.messages.create
        #     b) If stop_reason != "tool_use", extract text and break
        #     c) Process tool_use blocks, execute tools, collect results
        #     d) Append to messages
        #     e) Log memory state after each iteration
        #   - Return the final text response
        # ------------------------------------------------------------------
        pass

    def store_session_as_episode(self, user_query: str, final_response: str) -> str:
        """
        After a research session completes, store it as a new episodic memory.

        Args:
            user_query: The original user question
            final_response: The agent's final response

        Returns:
            The episode ID
        """
        # ------------------------------------------------------------------
        # TODO 3: Implement store_session_as_episode()
        #   - Build a summary from the user query and key findings
        #   - Include relevant metadata from working memory:
        #     current_debtor, risk_level, etc.
        #   - Call self.episodic_memory.store_episode()
        #   - Return the episode ID
        # ------------------------------------------------------------------
        pass


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("M11 Lab - Step 3: Full 3-Tier Memory Agent")
    print("=" * 60)

    agent = MemoryAgent()
    agent.initialize()

    # Session 1: Research a debtor
    print("\n\n>>> Session 1: Research Greenfield Logistics")
    result1 = agent.run(
        "Research Greenfield Logistics LLC and assess their lien risk."
    )
    print(f"\nFINAL ANSWER: {result1}")

    # Store session 1 as an episode
    print("\n\n>>> Storing Session 1 as episode...")
    episode_id = agent.store_session_as_episode(
        "Research Greenfield Logistics LLC and assess their lien risk.",
        result1
    )
    print(f"Stored as: {episode_id}")

    # Show all memory states
    print("\n\n>>> Memory State After Session 1:")
    observe_memory("WORKING MEMORY", agent.working_memory.to_dict())
    observe_memory("PROCEDURAL MEMORY", {k: v["description"] for k, v in agent.procedural_memory.items()})
    recent = agent.episodic_memory.get_recent(3)
    observe_memory("EPISODIC MEMORY (recent)", {f"episode_{i+1}": ep["summary"][:80] + "..." for i, ep in enumerate(recent)})

    # Clear working memory for session 2
    agent.working_memory.clear()

    # Session 2: Research another debtor (should recall session 1)
    print("\n\n>>> Session 2: Research Peachtree Ventures (should recall past sessions)")
    result2 = agent.run(
        "Research Peachtree Ventures LLC. I need to evaluate their lien risk and compare to other companies we've researched."
    )
    print(f"\nFINAL ANSWER: {result2}")

    # Store session 2
    episode_id2 = agent.store_session_as_episode(
        "Research Peachtree Ventures LLC lien risk",
        result2
    )
    print(f"\nStored as: {episode_id2}")

    # Final memory summary
    print("\n\n>>> Final Memory Summary:")
    observe_memory("WORKING MEMORY", agent.working_memory.to_dict())
    all_recent = agent.episodic_memory.get_recent(5)
    print(f"\n[EPISODIC MEMORY] Total episodes: {len(all_recent)}")
    for i, ep in enumerate(all_recent, 1):
        print(f"  {i}. {ep['summary'][:80]}...")
