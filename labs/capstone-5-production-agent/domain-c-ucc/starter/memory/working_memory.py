"""
Working Memory — short-term context for the current session.

Holds:
- Current query being processed
- Intermediate results from agent calls
- Active conversation context
- Tool call history for this request

Clears at the end of each session/request.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime


@dataclass
class ToolCallRecord:
    """Record of a single tool call within the current request."""
    tool_name: str
    arguments: Dict[str, Any]
    result: Any
    timestamp: str
    duration_ms: float = 0.0


@dataclass
class AgentHandoff:
    """Record of a handoff between agents."""
    from_agent: str
    to_agent: str
    reason: str
    context: Dict[str, Any]
    timestamp: str


class WorkingMemory:
    """
    Short-term memory that holds context for the current request.

    Think of this like a whiteboard in a meeting room — it holds everything
    relevant to the current discussion, and gets wiped clean when the meeting
    (request) ends.
    """

    def __init__(self):
        self._context: Dict[str, Any] = {}
        self._tool_calls: List[ToolCallRecord] = []
        self._agent_handoffs: List[AgentHandoff] = []
        self._current_query: Optional[str] = None
        self._intermediate_results: List[Dict[str, Any]] = []
        self._created_at: str = datetime.utcnow().isoformat()

    # ------------------------------------------------------------------
    # TODO 1: Implement set_query()
    # Store the current user query being processed.
    # Also reset intermediate results and tool calls (new query = fresh start).
    # ------------------------------------------------------------------
    def set_query(self, query: str) -> None:
        """Set the current query and reset per-query state."""
        # TODO: Store query in self._current_query
        # TODO: Clear self._intermediate_results
        # TODO: Clear self._tool_calls
        # TODO: Update self._created_at to current time
        pass

    # ------------------------------------------------------------------
    # TODO 2: Implement get_query()
    # Return the current query being processed.
    # ------------------------------------------------------------------
    def get_query(self) -> Optional[str]:
        """Return the current query."""
        # TODO: Return self._current_query
        pass

    # ------------------------------------------------------------------
    # TODO 3: Implement store() and retrieve()
    # store(key, value) — save a value by key in the context dict
    # retrieve(key) — get a value by key, return None if missing
    # ------------------------------------------------------------------
    def store(self, key: str, value: Any) -> None:
        """Store a key-value pair in working memory."""
        # TODO: Save value in self._context under the given key
        pass

    def retrieve(self, key: str) -> Optional[Any]:
        """Retrieve a value from working memory by key."""
        # TODO: Return value from self._context, or None if not found
        pass

    # ------------------------------------------------------------------
    # TODO 4: Implement record_tool_call()
    # Create a ToolCallRecord and append it to self._tool_calls.
    # ------------------------------------------------------------------
    def record_tool_call(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        result: Any,
        duration_ms: float = 0.0,
    ) -> None:
        """Record a tool call made during this request."""
        # TODO: Create a ToolCallRecord with the given parameters
        # TODO: Use datetime.utcnow().isoformat() for the timestamp
        # TODO: Append to self._tool_calls
        pass

    # ------------------------------------------------------------------
    # TODO 5: Implement record_agent_handoff()
    # Create an AgentHandoff and append it to self._agent_handoffs.
    # ------------------------------------------------------------------
    def record_agent_handoff(
        self,
        from_agent: str,
        to_agent: str,
        reason: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Record a handoff between agents."""
        # TODO: Create an AgentHandoff record
        # TODO: Append to self._agent_handoffs
        pass

    # ------------------------------------------------------------------
    # TODO 6: Implement add_intermediate_result()
    # Append a dict with agent_name, result, and timestamp to
    # self._intermediate_results.
    # ------------------------------------------------------------------
    def add_intermediate_result(self, agent_name: str, result: Any) -> None:
        """Store an intermediate result from an agent."""
        # TODO: Append {"agent": agent_name, "result": result, "timestamp": ...}
        pass

    # ------------------------------------------------------------------
    # TODO 7: Implement get_summary()
    # Return a dict summarizing the current working memory state:
    # - current_query, context_keys, tool_call_count,
    #   agent_handoff_count, intermediate_result_count
    # ------------------------------------------------------------------
    def get_summary(self) -> Dict[str, Any]:
        """Return a summary of the current working memory state."""
        # TODO: Return a summary dict
        pass

    # ------------------------------------------------------------------
    # TODO 8: Implement clear()
    # Reset ALL internal state to empty/default values.
    # This is called at the end of each request.
    # ------------------------------------------------------------------
    def clear(self) -> None:
        """Clear all working memory (end of session)."""
        # TODO: Reset all internal state
        pass

    @property
    def tool_calls(self) -> List[ToolCallRecord]:
        """Return the list of tool calls."""
        return self._tool_calls

    @property
    def agent_handoffs(self) -> List[AgentHandoff]:
        """Return the list of agent handoffs."""
        return self._agent_handoffs

    @property
    def intermediate_results(self) -> List[Dict[str, Any]]:
        """Return intermediate results."""
        return self._intermediate_results
