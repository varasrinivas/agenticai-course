"""
M11 Lab - Step 2: Episodic Memory with Vector Search (Solution)
==============================================================
Complete solution: episodic memory backed by ChromaDB for storing
and recalling past conversation summaries via semantic search.

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


def observe_episodes(episodes: list) -> None:
    print(f"\n{'─' * 60}")
    print(f"[EPISODIC MEMORY RECALL] Found {len(episodes)} similar episodes")
    for i, ep in enumerate(episodes, 1):
        score = ep.get("similarity", "N/A")
        print(f"  {i}. [score={score:.3f}] {ep['summary']}")
        if ep.get("metadata"):
            print(f"     metadata: {ep['metadata']}")
    print(f"{'─' * 60}")


# =============================================================================
# MOCK EPISODES
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
# EPISODIC MEMORY CLASS — SOLUTION
# =============================================================================

class EpisodicMemory:
    """Vector-backed episodic memory using ChromaDB."""

    def __init__(self, collection_name: str = "ucc_episodes"):
        self._client = chromadb.Client()
        self._collection = self._client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        self._episode_count = 0

    def store_episode(self, summary: str, metadata: dict = None) -> str:
        """Store a conversation summary as an episode in ChromaDB."""
        episode_id = f"episode_{self._episode_count}"
        self._episode_count += 1

        if metadata is None:
            metadata = {}
        if "timestamp" not in metadata:
            metadata["timestamp"] = datetime.now().isoformat()

        # ChromaDB metadata values must be str, int, float, or bool
        clean_metadata = {}
        for k, v in metadata.items():
            if isinstance(v, (str, int, float, bool)):
                clean_metadata[k] = v
            else:
                clean_metadata[k] = str(v)

        self._collection.add(
            documents=[summary],
            metadatas=[clean_metadata],
            ids=[episode_id]
        )
        return episode_id

    def recall(self, query: str, n_results: int = 3) -> list[dict]:
        """Find similar past episodes via semantic search."""
        try:
            count = self._collection.count()
            if count == 0:
                return []

            # Don't request more results than exist
            n = min(n_results, count)
            results = self._collection.query(
                query_texts=[query],
                n_results=n
            )

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
        """Get the N most recent episodes."""
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

            # Sort by timestamp (most recent first)
            episodes.sort(
                key=lambda x: x.get("metadata", {}).get("timestamp", ""),
                reverse=True
            )
            return episodes[:n]
        except Exception:
            return []

    def populate_mock_episodes(self) -> None:
        """Load the mock episodes into the vector store."""
        print("[EPISODIC MEMORY] Loading mock episodes...")
        for ep in MOCK_EPISODES:
            episode_id = self.store_episode(ep["summary"], ep["metadata"])
            print(f"  Stored: {episode_id} — {ep['summary'][:60]}...")
        print(f"[EPISODIC MEMORY] {len(MOCK_EPISODES)} episodes loaded.\n")


# =============================================================================
# TOOL DEFINITIONS
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
# TOOL EXECUTION
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
# AGENT WITH EPISODIC MEMORY — SOLUTION
# =============================================================================

def run_episodic_agent(user_message: str, episodic: EpisodicMemory, max_turns: int = 10) -> str:
    """Run a research agent that uses episodic memory to recall similar past research."""
    observe("QUERY", user_message)

    system_prompt = """You are a UCC (Uniform Commercial Code) filing research agent with episodic memory.
You can recall similar past research sessions to inform your current work.

IMPORTANT WORKFLOW:
1. ALWAYS call recall_similar_research FIRST before doing any new research.
   This checks if you have relevant prior experience with this debtor or topic.
2. If past research is found, reference it in your response and note what's new vs. already known.
3. Then proceed with any additional searches needed.
4. Provide a comprehensive summary that integrates both past and current findings."""

    messages = [{"role": "user", "content": user_message}]

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
                result = execute_tool(block.name, block.input, episodic)
                observe_tool_result(result)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result,
                })

        messages.append({"role": "assistant", "content": response.content})
        messages.append({"role": "user", "content": tool_results})

    return "Agent did not produce a final response within max turns."


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("M11 Lab - Step 2: Episodic Memory with Vector Search (SOLUTION)")
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
