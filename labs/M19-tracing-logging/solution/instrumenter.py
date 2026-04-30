"""
M19 Lab — Agent Instrumenter (Solution)
========================================
Complete instrumented agent with tracing and structured logging.

Usage:
    python instrumenter.py
"""

import time
import json
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
from trace_model import Trace, Span, SpanContext
from structured_logger import StructuredLogger, scrub_pii


# =============================================================================
# MOCK AGENT
# =============================================================================

class MockUCCAgent:
    """Simulates a UCC research agent: 2 LLM calls + 1 tool call."""

    def __init__(self):
        self.model = "claude-sonnet-4-6"
        self.call_log = []

    def run(self, query: str) -> dict:
        operations = []

        # Step 1: First LLM call
        time.sleep(0.05)
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

        # Step 2: Tool execution
        time.sleep(0.02)
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

        # Step 3: Second LLM call
        time.sleep(0.03)
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

class InstrumentedAgent:
    """Wraps an agent with automatic tracing and structured logging."""

    def __init__(self, agent, logger: StructuredLogger):
        self.agent = agent
        self.logger = logger

    def run(self, query: str) -> tuple:
        """Execute the agent with full tracing. Returns (result, trace)."""
        trace = Trace(name="agent_request", metadata={"query": query})

        try:
            with SpanContext(trace, "agent_request") as root:
                root.set_attribute("query", query)
                self.logger.log("INFO", "Agent request started",
                                trace_id=trace.trace_id, span_id=root.span_id,
                                query=query)

                result = self.agent.run(query)

                for operation in result["operations"]:
                    if operation["type"] == "llm_call":
                        self._instrument_llm_call(trace, root, operation)
                    elif operation["type"] == "tool_call":
                        self._instrument_tool_call(trace, root, operation)

                root.set_attribute("answer_length", len(result["answer"]))
                self.logger.log("INFO", "Agent request completed",
                                trace_id=trace.trace_id, span_id=root.span_id,
                                total_spans=len(trace.spans))

        except Exception as e:
            self.logger.log_error(e, trace_id=trace.trace_id)
            raise

        return (result, trace)

    def _instrument_llm_call(self, trace: Trace, parent: Span, operation: dict) -> None:
        """Create a span for an LLM API call."""
        with SpanContext(trace, "llm_call", parent=parent) as span:
            span.set_attribute("model", operation["model"])
            span.set_attribute("input_tokens", operation["input_tokens"])
            span.set_attribute("output_tokens", operation["output_tokens"])
            span.set_attribute("total_tokens", operation["input_tokens"] + operation["output_tokens"])
            span.set_attribute("stop_reason", operation["response"]["stop_reason"])

            self.logger.log_llm_call(
                model=operation["model"],
                input_tokens=operation["input_tokens"],
                output_tokens=operation["output_tokens"],
                duration_ms=operation["duration_ms"],
                trace_id=trace.trace_id,
                span_id=span.span_id
            )

            time.sleep(operation["duration_ms"] / 1000)

    def _instrument_tool_call(self, trace: Trace, parent: Span, operation: dict) -> None:
        """Create a span for a tool execution."""
        with SpanContext(trace, "tool_execution", parent=parent) as span:
            span.set_attribute("tool_name", operation["tool_name"])
            span.set_attribute("tool_input", operation["tool_input"])
            span.set_attribute("result_count", len(operation["tool_output"].get("results", [])))

            self.logger.log_tool_call(
                tool_name=operation["tool_name"],
                tool_input=operation["tool_input"],
                tool_output=operation["tool_output"],
                duration_ms=operation["duration_ms"],
                trace_id=trace.trace_id,
                span_id=span.span_id
            )

            time.sleep(operation["duration_ms"] / 1000)


# =============================================================================
# SELF-TEST
# =============================================================================

def self_test():
    """Run the mock agent with full instrumentation."""
    print("=" * 60)
    print("M19 Agent Instrumenter — Self-Test")
    print("=" * 60)
    print()

    logger = StructuredLogger(service_name="ucc_agent")
    agent = MockUCCAgent()
    instrumented = InstrumentedAgent(agent, logger)

    result, trace = instrumented.run("Find all UCC filings for Greenfield Logistics in New York")

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

    print(f"{'=' * 60}")
    print(f"AGENT ANSWER")
    print(f"{'=' * 60}")
    print(result["answer"])
    print()

    assert len(trace.spans) == 4, f"Expected 4 spans (root + 2 LLM + 1 tool), got {len(trace.spans)}"
    span_names = [s.name for s in trace.spans]
    assert "agent_request" in span_names, "Missing root span"
    assert span_names.count("llm_call") == 2, "Expected 2 llm_call spans"
    assert "tool_execution" in span_names, "Missing tool_execution span"
    print("All assertions passed!")


if __name__ == "__main__":
    self_test()
