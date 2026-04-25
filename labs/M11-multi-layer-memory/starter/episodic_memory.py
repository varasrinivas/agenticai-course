"""
M11 Lab - Step 2: Episodic Memory with Vector Search (Starter)
==============================================================
Build an episodic memory backed by ChromaDB that stores past
conversation summaries and retrieves similar experiences when
the agent encounters a related query.

KEY CONCEPT: Episodic memory lets your agent say "I've seen
something like this before." It stores summaries of past research
sessions as vectors and retrieves the most relevant ones when a
new query arrives — giving the agent long-term learning capability.

Usage:
    python episodic_memory.py
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
MODEL = "claude-sonnet-4-20250514"


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


def observe_episodes(episodes: list) -> None:
    """Log recalled episodes with similarity scores."""
    print(f"\n{'─' * 60}")
    print(f"[EPISODIC MEMORY RECALL] Found {len(episodes)} similar episodes")
    for i, ep in enumerate(episodes, 1):
        score = ep.get("similarity", "N/A")
        print(f"  {i}. [score={score:.3f}] {ep['summary']}")
        if ep.get("metadata"):
            print(f"     metadata: {ep['metadata']}")
    print(f"{'─' * 60}")


# =============================================================================
# MOCK EPISODES (complete -- do not modify)
# These simulate past research sessions stored as episodic memories.
# =============================================================================

MOCK_EPISODES = [
    {
        "summary": "Researched Greenfield Logistics — found active filing in NY, blanket lien by Atlantic Capital Partners covering all accounts receivable, inventory, equipment, and general intangibles.",
        "metadata": {"debtor": "Greenfield Logistics LLC", "state": "New York", "risk_level": "high", "timestamp": "2024-08-15T10:30:00Z"}
    },
    {
        "summary": "Investigated Pacific Ridge Technologies — DE incorporation but CA filing, extensive IP collateral including patents and trademarks, secured by Silicon Valley Bank.",
        "metadata": {"debtor": "Pacific Ridge Technologies Inc", "state": "California", "risk_level": "medium", "timestamp": "2024-08-20T14:15:00Z"}
    },
    {
        "summary": "Searched for Lone Star Energy — found equipment-specific lien on Caterpillar excavators and Liebherr crane, secured by Wells Fargo Equipment Finance in Texas.",
        "metadata": {"debtor": "Lone Star Energy Solutions LP", "state": "Texas", "risk_level": "low", "timestamp": "2024-09-02T09:00:00Z"}
    },
    {
        "summary": "Looked into Sunshine Medical Group — found UCC-3 amendment adding MRI equipment and CT scanner to existing lien, TD Bank is secured party in Florida.",
        "metadata": {"debtor": "Sunshine Medical Group PA", "state": "Florida", "risk_level": "medium", "timestamp": "2024-09-10T11:45:00Z"}
    },
    {
        "summary": "Checked Nextera Holdings — massive blanket lien by JPMorgan Chase covering all assets including commercial tort claims, minerals, and investment property in Delaware.",
        "metadata": {"debtor": "Nextera Holdings Corp", "state": "Delaware", "risk_level": "critical", "timestamp": "2024-09-15T16:20:00Z"}
    }
]


# =============================================================================
# EPISODIC MEMORY CLASS — YOUR CODE HERE
# =============================================================================

class EpisodicMemory:
    """
    Vector-backed episodic memory using ChromaDB.

    Stores conversation summaries as embeddings and retrieves
    similar past experiences via semantic search.
    """

    def __init__(self, collection_name: str = "ucc_episodes"):
        # ChromaDB uses its own built-in embedding function by default
        self._client = chromadb.Client()
        self._collection = self._client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        self._episode_count = 0

    def store_episode(self, summary: str, metadata: dict = None) -> str:
        """
        Store a conversation summary as an episode in ChromaDB.

        Args:
            summary: Text summary of the conversation/research session
            metadata: Optional dict with keys like debtor, state, risk_level, timestamp

        Returns:
            The episode ID
        """
        # ------------------------------------------------------------------
        # TODO 1: Implement store_episode()
        #   - Generate a unique episode ID (e.g., f"episode_{self._episode_count}")
        #   - Increment self._episode_count
        #   - Add a timestamp to metadata if not present
        #   - Use self._collection.add() with:
        #     documents=[summary]
        #     metadatas=[metadata] (ensure all values are strings for ChromaDB)
        #     ids=[episode_id]
        #   - Return the episode ID
        #
        # GOTCHA: ChromaDB metadata values must be str, int, float, or bool.
        #   Convert any other types to strings.
        # ------------------------------------------------------------------
        pass

    def recall(self, query: str, n_results: int = 3) -> list[dict]:
        """
        Find similar past episodes via semantic search.

        Args:
            query: The search query (natural language)
            n_results: Number of results to return

        Returns:
            List of dicts with keys: summary, metadata, similarity
        """
        # ------------------------------------------------------------------
        # TODO 2: Implement recall()
        #   - Use self._collection.query() with query_texts=[query], n_results=n_results
        #   - Handle the case where the collection is empty (return [])
        #   - Transform the ChromaDB result into a list of dicts:
        #     [{"summary": doc, "metadata": meta, "similarity": 1 - distance}, ...]
        #   - ChromaDB returns distances (lower = more similar for cosine)
        #     so similarity = 1 - distance
        #   - Return the list sorted by similarity (highest first)
        # ------------------------------------------------------------------
        pass

    def get_recent(self, n: int = 5) -> list[dict]:
        """
        Get the N most recent episodes.

        Returns:
            List of dicts with keys: summary, metadata
        """
        # ------------------------------------------------------------------
        # TODO 3: Implement get_recent()
        #   - Use self._collection.get() to retrieve all episodes
        #   - Sort by timestamp in metadata (most recent first)
        #   - Return the top N as list of dicts: [{"summary": doc, "metadata": meta}, ...]
        #   - Handle empty collection gracefully
        # ------------------------------------------------------------------
        pass

    def populate_mock_episodes(self) -> None:
        """Load the mock episodes into the vector store."""
        print("[EPISODIC MEMORY] Loading mock episodes...")
        for ep in MOCK_EPISODES:
            episode_id = self.store_episode(ep["summary"], ep["metadata"])
            print(f"  Stored: {episode_id} — {ep['summary'][:60]}...")
        print(f"[EPISODIC MEMORY] {len(MOCK_EPISODES)} episodes loaded.\n")


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
        "description": "Search episodic memory for similar past research sessions. Use this FIRST before doing new research to see if we have relevant prior experience.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "What to search for in past research sessions"}
            },
            "required": ["query"]
        }
    }
]


# =============================================================================
# TOOL EXECUTION (complete -- do not modify)
# =============================================================================

def execute_tool(tool_name: str, tool_input: dict, episodic: EpisodicMemory) -> str:
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
            episodes = episodic.recall(tool_input["query"], n_results=3)
            if episodes:
                observe_episodes(episodes)
                return json.dumps([{
                    "summary": ep["summary"],
                    "similarity": round(ep.get("similarity", 0), 3),
                    "metadata": ep.get("metadata", {})
                } for ep in episodes], indent=2)
            return json.dumps({"message": "No similar past research found."})

        else:
            return json.dumps({"error": f"Unknown tool: {tool_name}"})
    except Exception as e:
        return json.dumps({"error": f"Tool execution failed: {str(e)}"})


# =============================================================================
# AGENT WITH EPISODIC MEMORY — YOUR CODE HERE
# =============================================================================

def run_episodic_agent(user_message: str, episodic: EpisodicMemory, max_turns: int = 10) -> str:
    """
    Run a research agent that uses episodic memory to recall similar past research.

    The agent:
    1. First checks episodic memory for similar past research
    2. Uses that context to inform current research
    3. Runs UCC filing searches as needed
    4. Returns findings with context from past sessions

    Returns Claude's final text response.
    """
    observe("QUERY", user_message)

    # ------------------------------------------------------------------
    # TODO 4: Build the system prompt
    #   - Instruct Claude that it is a UCC research agent with episodic memory
    #   - Tell it to ALWAYS call recall_similar_research first before
    #     doing new research, to check for relevant past experience
    #   - Tell it to reference past research in its response when relevant
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
    #     b) Execute with execute_tool (pass episodic memory)
    #     c) Log with observe_tool_result
    #   - Append assistant response and tool results to messages
    # ------------------------------------------------------------------
    pass

    return "Agent did not produce a final response within max turns."


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("M11 Lab - Step 2: Episodic Memory with Vector Search")
    print("=" * 60)

    # Initialize episodic memory and load mock episodes
    episodic = EpisodicMemory()
    episodic.populate_mock_episodes()

    # Test 1: Query about a debtor we've researched before
    print("\n\n>>> Test 1: Query about a previously researched debtor")
    result1 = run_episodic_agent(
        "I need to research Greenfield Logistics. What do we know?",
        episodic
    )
    print(f"\nFINAL ANSWER: {result1}")

    # Test 2: Query about a debtor with similar characteristics
    print("\n\n>>> Test 2: Query about a new debtor (should find similar past research)")
    result2 = run_episodic_agent(
        "Research a company called Midwest Agricultural Cooperative. Are there any equipment liens?",
        episodic
    )
    print(f"\nFINAL ANSWER: {result2}")

    # Test 3: Store a new episode and recall it
    print("\n\n>>> Test 3: Store new episode and verify recall")
    episodic.store_episode(
        "Researched Midwest Agricultural Cooperative — found active filing in IL, farm products collateral including crops and livestock, secured by Farm Credit Services.",
        {"debtor": "Midwest Agricultural Cooperative", "state": "Illinois", "risk_level": "medium", "timestamp": "2024-10-01T10:00:00Z"}
    )
    result3 = run_episodic_agent(
        "What do we know about agricultural companies in our research history?",
        episodic
    )
    print(f"\nFINAL ANSWER: {result3}")

    # Show recent episodes
    print("\n\n>>> Recent Episodes:")
    recent = episodic.get_recent(3)
    for i, ep in enumerate(recent, 1):
        print(f"  {i}. {ep['summary'][:80]}...")
        print(f"     {ep.get('metadata', {})}")
