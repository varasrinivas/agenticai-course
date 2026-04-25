"""
M19 Lab — Agent Instrumenter (Starter)
=======================================
Wrap a UCC research agent with automatic tracing and structured
logging. Every API call and tool execution gets its own span.

KEY CONCEPT: Instrumentation means adding measurement code around
existing operations WITHOUT changing the operations themselves.
Think of it like wrapping a gift — the gift (your agent logic)
stays the same, but now it's wrapped in timing and logging code
that makes it observable.

Usage:
    python instrumenter.py
"""

import time
import json
import sys
import os

# Import our trace model and logger from the same directory
sys.path.insert(0, os.path.dirname(__file__))
from trace_model import Trace, Span, SpanContext
from structured_logger import StructuredLogger, scrub_pii


# =============================================================================
# MOCK AGENT — simulates a real agent without needing an API key
# =============================================================================

# WHAT: A fake agent that simulates the exact sequence of operations
#   a real Claude-powered UCC research agent would perform:
#   1. Receive a query
#   2. Call Claude (LLM call #1) to decide which tool to use
#   3. Execute the tool (search_filings)
#   4. Call Claude (LLM call #2) to synthesize the answer
# WHY:  You need a realistic agent to instrument, but you don't want
#   to burn API credits or require an API key for a tracing lab.
# GOTCHA: The mock uses time.sleep() to simulate realistic latencies.
#   In production, these would be real network calls.

class MockUCCAgent:
    """Simulates a UCC research agent: 2 LLM calls + 1 tool call."""

    def __init__(self):
        self.model = "claude-sonnet-4-20250514"
        self.call_log = []  # Records every operation for verification

    def run(self, query: str) -> dict:
        """
        Execute a mock agent run. Returns a dict with:
        - "answer": the final text response
        - "operations": list of dicts describing each operation
        """
        operations = []

        # --- Step 1: First LLM call (decide which tool to use) ---
        time.sleep(0.05)  # simulate API latency
        llm_call_1 = {
            "type": "llm_call",
            "model": self.model,
            "input_tokens": 350,
            "output_tokens": 85,
            "duration_ms": 50.0,
            "response": {
                "stop_reason": "tool_use",
                "tool_name": "search_filings",
                "tool_input": {"debtor_name": "Greenfield Logistics", "state": "New York"}
            }
        }
        operations.append(llm_call_1)

        # --- Step 2: Tool execution ---
        time.sleep(0.02)  # simulate tool latency
        tool_call = {
            "type": "tool_call",
            "tool_name": "search_filings",
            "tool_input": {"debtor_name": "Greenfield Logistics", "state": "New York"},
            "tool_output": {
                "results": [
                    {
                        "filing_number": "NY-2024-001234",
                        "debtor": "Greenfield Logistics LLC",
                        "secured_party": "First National Bank",
                        "collateral": "All inventory and equipment",
                        "filing_date": "2024-03-15",
                        "status": "active"
                    },
                    {
                        "filing_number": "NY-2024-005678",
                        "debtor": "Greenfield Logistics LLC",
                        "secured_party": "Atlas Capital Partners",
                        "collateral": "Accounts receivable",
                        "filing_date": "2024-07-22",
                        "status": "active"
                    }
                ]
            },
            "duration_ms": 20.0
        }
        operations.append(tool_call)

        # --- Step 3: Second LLM call (synthesize the answer) ---
        time.sleep(0.03)  # simulate API latency
        llm_call_2 = {
            "type": "llm_call",
            "model": self.model,
            "input_tokens": 820,
            "output_tokens": 210,
            "duration_ms": 30.0,
            "response": {
                "stop_reason": "end_turn",
                "text": (
                    "I found 2 active UCC filings for Greenfield Logistics LLC "
                    "in New York:\n\n"
                    "1. NY-2024-001234 — Filed 2024-03-15 by First National Bank "
                    "against all inventory and equipment.\n"
                    "2. NY-2024-005678 — Filed 2024-07-22 by Atlas Capital Partners "
                    "against accounts receivable.\n\n"
                    "Both filings are currently active."
                )
            }
        }
        operations.append(llm_call_2)

        self.call_log = operations
        return {
            "answer": llm_call_2["response"]["text"],
            "operations": operations
        }


# =============================================================================
# INSTRUMENTED AGENT
# =============================================================================

# WHAT: A wrapper that takes any agent function, creates a trace for
#   each run, and wraps every operation in a measured span.
# WHY:  Without instrumentation, you have no idea how long each step
#   takes, which tokens were used, or where errors occurred. The
#   instrumenter adds this visibility automatically.
# GOTCHA: The instrumenter should NOT change the agent's behavior —
#   it only adds measurement. If the agent would return X without
#   instrumentation, it must still return X with it.

class InstrumentedAgent:
    """Wraps an agent with automatic tracing and structured logging."""

    def __init__(self, agent, logger: StructuredLogger):
        """
        Args:
            agent: Any object with a .run(query) method
            logger: StructuredLogger instance for JSON log output
        """
        # TODO: Store agent and logger as instance attributes
        pass

    def run(self, query: str) -> tuple:
        """
        Execute the agent with full tracing.

        Returns:
            (result, trace) — the agent's result and the complete trace
        """
        # TODO: Implement instrumented agent execution:
        #
        # 1. Create a new Trace with name="agent_request"
        #    and metadata={"query": query}
        #
        # 2. Use SpanContext to create the root span "agent_request"
        #    Set attribute "query" on the root span
        #    Log an INFO message "Agent request started"
        #
        # 3. Inside the root span context:
        #    a. Call self.agent.run(query) to get the result
        #    b. Iterate over result["operations"]
        #    c. For each operation, call the appropriate _instrument_* method
        #       based on operation["type"]:
        #       - "llm_call" -> self._instrument_llm_call(trace, root, operation)
        #       - "tool_call" -> self._instrument_tool_call(trace, root, operation)
        #    d. Set attribute "answer_length" on root span = len(result["answer"])
        #    e. Log an INFO message "Agent request completed"
        #
        # 4. If any exception occurs:
        #    a. Log the error with self.logger.log_error()
        #    b. Re-raise the exception
        #
        # 5. Return (result, trace)
        pass

    def _instrument_llm_call(self, trace: Trace, parent: Span, operation: dict) -> None:
        """Create a span for an LLM API call."""
        # TODO:
        # 1. Use SpanContext to create a child span named "llm_call"
        #    under parent
        # 2. Set these attributes on the span:
        #    - "model": operation["model"]
        #    - "input_tokens": operation["input_tokens"]
        #    - "output_tokens": operation["output_tokens"]
        #    - "total_tokens": input + output
        #    - "stop_reason": operation["response"]["stop_reason"]
        # 3. Log the LLM call using self.logger.log_llm_call()
        #    with trace_id and span_id
        # 4. Sleep for operation["duration_ms"] / 1000 to simulate timing
        pass

    def _instrument_tool_call(self, trace: Trace, parent: Span, operation: dict) -> None:
        """Create a span for a tool execution."""
        # TODO:
        # 1. Use SpanContext to create a child span named "tool_execution"
        #    under parent
        # 2. Set these attributes on the span:
        #    - "tool_name": operation["tool_name"]
        #    - "tool_input": operation["tool_input"]
        #    - "result_count": number of results in tool_output["results"]
        # 3. Log the tool call using self.logger.log_tool_call()
        #    with trace_id and span_id
        # 4. Sleep for operation["duration_ms"] / 1000 to simulate timing
        pass


# =============================================================================
# SELF-TEST
# =============================================================================

def self_test():
    """Run the mock agent with full instrumentation."""
    print("=" * 60)
    print("M19 Agent Instrumenter — Self-Test")
    print("=" * 60)
    print()

    # Create logger and mock agent
    logger = StructuredLogger(service_name="ucc_agent")
    agent = MockUCCAgent()
    instrumented = InstrumentedAgent(agent, logger)

    # Run the instrumented agent
    result, trace = instrumented.run("Find all UCC filings for Greenfield Logistics in New York")

    # Print trace summary
    print(f"\n{'=' * 60}")
    print(f"TRACE SUMMARY")
    print(f"{'=' * 60}")
    print(f"  Trace ID:    {trace.trace_id}")
    print(f"  Total Spans: {len(trace.spans)}")
    print(f"  Duration:    {trace.get_duration_ms():.1f} ms")
    print()

    for span in trace.spans:
        indent = "    " if span.parent_span_id else "  "
        status_icon = "OK" if span.status == "ok" else "ERR"
        print(f"{indent}[{status_icon}] {span.name} — {span.duration_ms:.1f} ms")
        if span.attributes:
            for k, v in span.attributes.items():
                print(f"{indent}     {k}: {v}")
        print()

    # Print the answer
    print(f"{'=' * 60}")
    print(f"AGENT ANSWER")
    print(f"{'=' * 60}")
    print(result["answer"])
    print()

    # Verify
    assert len(trace.spans) == 4, f"Expected 4 spans (root + 2 LLM + 1 tool), got {len(trace.spans)}"
    span_names = [s.name for s in trace.spans]
    assert "agent_request" in span_names, "Missing root span"
    assert span_names.count("llm_call") == 2, "Expected 2 llm_call spans"
    assert "tool_execution" in span_names, "Missing tool_execution span"
    print("All assertions passed!")


if __name__ == "__main__":
    self_test()
