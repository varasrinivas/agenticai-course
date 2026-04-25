"""
Working Memory — short-term context for the current session.
(Solution — fully implemented)
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime


@dataclass
class ToolCallRecord:
    tool_name: str
    arguments: Dict[str, Any]
    result: Any
    timestamp: str
    duration_ms: float = 0.0


@dataclass
class AgentHandoff:
    from_agent: str
    to_agent: str
    reason: str
    context: Dict[str, Any]
    timestamp: str


class WorkingMemory:
    """Short-term memory for the current request."""

    def __init__(self):
        self._context: Dict[str, Any] = {}
        self._tool_calls: List[ToolCallRecord] = []
        self._agent_handoffs: List[AgentHandoff] = []
        self._current_query: Optional[str] = None
        self._intermediate_results: List[Dict[str, Any]] = []
        self._created_at: str = datetime.utcnow().isoformat()

    def set_query(self, query: str) -> None:
        self._current_query = query
        self._intermediate_results = []
        self._tool_calls = []
        self._created_at = datetime.utcnow().isoformat()

    def get_query(self) -> Optional[str]:
        return self._current_query

    def store(self, key: str, value: Any) -> None:
        self._context[key] = value

    def retrieve(self, key: str) -> Optional[Any]:
        return self._context.get(key)

    def record_tool_call(
        self, tool_name: str, arguments: Dict[str, Any],
        result: Any, duration_ms: float = 0.0,
    ) -> None:
        record = ToolCallRecord(
            tool_name=tool_name,
            arguments=arguments,
            result=result,
            timestamp=datetime.utcnow().isoformat(),
            duration_ms=duration_ms,
        )
        self._tool_calls.append(record)

    def record_agent_handoff(
        self, from_agent: str, to_agent: str,
        reason: str, context: Optional[Dict[str, Any]] = None,
    ) -> None:
        handoff = AgentHandoff(
            from_agent=from_agent,
            to_agent=to_agent,
            reason=reason,
            context=context or {},
            timestamp=datetime.utcnow().isoformat(),
        )
        self._agent_handoffs.append(handoff)

    def add_intermediate_result(self, agent_name: str, result: Any) -> None:
        self._intermediate_results.append({
            "agent": agent_name,
            "result": result,
            "timestamp": datetime.utcnow().isoformat(),
        })

    def get_summary(self) -> Dict[str, Any]:
        return {
            "current_query": self._current_query,
            "context_keys": list(self._context.keys()),
            "tool_call_count": len(self._tool_calls),
            "agent_handoff_count": len(self._agent_handoffs),
            "intermediate_result_count": len(self._intermediate_results),
            "created_at": self._created_at,
        }

    def clear(self) -> None:
        self._context = {}
        self._tool_calls = []
        self._agent_handoffs = []
        self._current_query = None
        self._intermediate_results = []
        self._created_at = datetime.utcnow().isoformat()

    @property
    def tool_calls(self) -> List[ToolCallRecord]:
        return self._tool_calls

    @property
    def agent_handoffs(self) -> List[AgentHandoff]:
        return self._agent_handoffs

    @property
    def intermediate_results(self) -> List[Dict[str, Any]]:
        return self._intermediate_results
