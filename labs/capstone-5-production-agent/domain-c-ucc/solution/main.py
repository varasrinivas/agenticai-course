"""
Main entry point for the UCC Production Agent system.
(Solution — fully implemented)

Run:
    python main.py                    # Interactive mode
    python main.py --eval             # Run evaluation suite
    python main.py --query "..."      # Single query mode
    python main.py --dashboard        # Show metrics dashboard
"""

import argparse
import json
import sys
import time
import uuid
from typing import Any, Dict, Optional

from anthropic import Anthropic

from config import ANTHROPIC_API_KEY, APP_CONFIG, OBSERVABILITY, MODEL_TIERS
from memory import WorkingMemory, EpisodicMemory, ProceduralMemory
from agents import RouterAgent, FilingAgent, EntityAgent, RiskAgent
from model_router import ModelRouter
from observability import Tracer, MetricsCollector


class ProductionAgent:
    """Top-level production agent orchestrating the entire system."""

    def __init__(self):
        self.client = Anthropic(api_key=ANTHROPIC_API_KEY)

        # Memory layers
        self.working_memory = WorkingMemory()
        self.episodic_memory = EpisodicMemory(
            max_episodes=APP_CONFIG["episodic_memory_limit"]
        )
        self.procedural_memory = ProceduralMemory(
            max_rules=APP_CONFIG["procedural_memory_limit"]
        )

        # Agents
        self.router_agent = RouterAgent(client=self.client)
        self.filing_agent = FilingAgent(client=self.client)
        self.entity_agent = EntityAgent(client=self.client)
        self.risk_agent = RiskAgent(client=self.client)

        # Model router
        self.model_router = ModelRouter()

        # Observability
        self.tracer = Tracer()
        self.metrics = MetricsCollector()

    def process_query(self, query: str) -> Dict[str, Any]:
        """Process a user query through the full production pipeline."""
        request_id = uuid.uuid4().hex[:12]
        start_time = time.time()

        # 1. Start trace
        trace_id = self.tracer.start_trace("process_query")
        root_span_id = self.tracer.get_trace(trace_id)[0].span_id

        try:
            # 2. Working memory — set current query
            self.working_memory.set_query(query)

            # 3. Check episodic memory
            similar_episodes = self.episodic_memory.recall(query, k=2)
            if similar_episodes:
                best_episode, score = similar_episodes[0]
                if score > 0.8:
                    self.working_memory.store("similar_past_query", {
                        "query": best_episode.query,
                        "response": best_episode.response[:200],
                        "score": score,
                    })

            # 4. Check procedural memory
            keywords = query.lower().split()
            applicable_rules = self.procedural_memory.find_applicable_rules(
                keywords[:10], min_confidence=0.5
            )
            if applicable_rules:
                self.working_memory.store("applicable_rules", [
                    {"rule_id": r.rule_id, "action": r.action}
                    for r in applicable_rules[:3]
                ])

            # 5. Route query
            route_span_id = self.tracer.start_span(
                trace_id, "router_agent.route", kind="agent", parent_id=root_span_id
            )
            routing_decision = self.router_agent.route(query)
            self.tracer.end_span(route_span_id, status="ok")

            task_type = routing_decision["task_type"]
            agents_to_call = routing_decision["agents"]

            self.working_memory.store("routing_decision", routing_decision)

            # 6. Model selection
            model_decision = self.model_router.route(query, task_type)
            model_tier = model_decision["tier"]

            # 7. Execute agents
            all_tool_calls = []
            final_answer = ""

            for agent_name in agents_to_call:
                agent = self._select_agent(agent_name)
                if not agent:
                    continue

                # Set model tier
                agent.model_tier = model_tier
                agent.model_id = MODEL_TIERS[model_tier].model_id

                # Start span
                agent_span_id = self.tracer.start_span(
                    trace_id, f"{agent_name}.process", kind="agent",
                    parent_id=root_span_id,
                    attributes={"model_tier": model_tier},
                )

                self.working_memory.record_agent_handoff(
                    from_agent="router_agent",
                    to_agent=agent_name,
                    reason=routing_decision.get("reasoning", ""),
                )

                # Process
                try:
                    result = agent.process(query)
                    final_answer = result.get("answer", "")
                    tool_calls = result.get("tool_calls_made", [])
                    all_tool_calls.extend(tool_calls)

                    # Record in working memory
                    for tc in tool_calls:
                        self.working_memory.record_tool_call(
                            tool_name=tc.get("name", ""),
                            arguments=tc.get("input", {}),
                            result="(recorded)",
                        )

                    self.working_memory.add_intermediate_result(agent_name, {
                        "answer_preview": final_answer[:200],
                        "tool_count": len(tool_calls),
                    })

                    self.tracer.end_span(agent_span_id, status="ok")
                except Exception as e:
                    self.tracer.end_span(agent_span_id, status="error")
                    final_answer = f"Error in {agent_name}: {e}"

            # 8. Record metrics
            elapsed = (time.time() - start_time) * 1000
            estimated_input_tokens = len(query.split()) * 2 + 500  # Rough estimate
            estimated_output_tokens = len(final_answer.split()) * 2
            cost_estimate = self.model_router.estimate_cost(
                model_tier, estimated_input_tokens, estimated_output_tokens
            )

            self.metrics.record(
                request_id=request_id,
                task_type=task_type,
                model_tier=model_tier,
                model_id=MODEL_TIERS[model_tier].model_id,
                input_tokens=estimated_input_tokens,
                output_tokens=estimated_output_tokens,
                cost_usd=cost_estimate["total_cost"],
                latency_ms=elapsed,
                status="success",
                tool_calls=len(all_tool_calls),
                agent_handoffs=len(agents_to_call),
            )

            # 9. Store episode
            self.episodic_memory.store_episode(
                query=query,
                response=final_answer[:500],
                agent_used=agents_to_call[-1] if agents_to_call else "none",
                tool_calls=[tc.get("name", "") for tc in all_tool_calls],
                task_type=task_type,
                success=True,
            )

            # 10. End trace
            self.tracer.end_trace(trace_id)

            # 11. Clear working memory
            self.working_memory.clear()

            return {
                "answer": final_answer,
                "task_type": task_type,
                "model_tier": model_tier,
                "trace_id": trace_id,
                "tool_calls": [tc.get("name", "") for tc in all_tool_calls],
                "tool_calls_made": all_tool_calls,
                "latency_ms": elapsed,
                "request_id": request_id,
            }

        except Exception as e:
            self.tracer.end_trace(trace_id)
            self.working_memory.clear()

            elapsed = (time.time() - start_time) * 1000
            self.metrics.record(
                request_id=request_id, task_type="unknown", model_tier="balanced",
                model_id="claude-sonnet-4-20250514", input_tokens=0, output_tokens=0,
                cost_usd=0.0, latency_ms=elapsed, status="error",
            )

            return {
                "answer": f"Error processing query: {e}",
                "task_type": "error",
                "model_tier": "unknown",
                "trace_id": trace_id,
                "tool_calls": [],
                "tool_calls_made": [],
                "latency_ms": elapsed,
                "request_id": request_id,
            }

    def _select_agent(self, agent_name: str):
        agents = {
            "filing_agent": self.filing_agent,
            "entity_agent": self.entity_agent,
            "risk_agent": self.risk_agent,
        }
        return agents.get(agent_name)

    def get_dashboard(self) -> str:
        return self.metrics.format_dashboard()

    def get_trace(self, trace_id: str) -> str:
        return self.tracer.format_trace(trace_id)


# ---------------------------------------------------------------------------
# CLI Interface
# ---------------------------------------------------------------------------
def interactive_mode(agent: ProductionAgent):
    print("=" * 60)
    print("  UCC Production Agent -- Interactive Mode")
    print("  Type 'quit' to exit, 'dashboard' for metrics,")
    print("  'trace <id>' to see a request trace")
    print("=" * 60)
    print()

    while True:
        try:
            query = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not query:
            continue
        if query.lower() == "quit":
            print("Goodbye!")
            break
        if query.lower() == "dashboard":
            print(agent.get_dashboard())
            continue
        if query.lower().startswith("trace "):
            trace_id = query.split(" ", 1)[1].strip()
            print(agent.get_trace(trace_id))
            continue

        print("\nProcessing...\n")
        result = agent.process_query(query)

        if result:
            print(f"Agent: {result.get('answer', 'No answer generated')}")
            print(f"\n  [Task: {result.get('task_type', '?')} | "
                  f"Model: {result.get('model_tier', '?')} | "
                  f"Latency: {result.get('latency_ms', 0):.0f}ms | "
                  f"Trace: {result.get('trace_id', '?')}]")
        else:
            print("Agent: Sorry, I couldn't process that query.")
        print()


def eval_mode(agent: ProductionAgent, max_tests: Optional[int] = None):
    from evaluation import EvaluationHarness

    print("=" * 60)
    print("  UCC Production Agent -- Evaluation Mode")
    print("=" * 60)
    print()

    harness = EvaluationHarness()
    print(f"Loaded {harness.test_count} test cases")
    print("Running evaluation...\n")

    report = harness.run_all(agent_fn=agent.process_query, max_tests=max_tests)

    print(harness.format_report(report))
    print("\nMetrics Dashboard:")
    print(agent.get_dashboard())


def single_query_mode(agent: ProductionAgent, query: str):
    print(f"Query: {query}\n")
    result = agent.process_query(query)

    if result:
        print(f"Answer: {result.get('answer', 'No answer')}")
        print(f"\nTrace:")
        print(agent.get_trace(result.get("trace_id", "")))
        print(f"\nDashboard:")
        print(agent.get_dashboard())
    else:
        print("Error: Could not process query.")


def main():
    parser = argparse.ArgumentParser(description="UCC Production Agent")
    parser.add_argument("--eval", action="store_true", help="Run evaluation suite")
    parser.add_argument("--query", type=str, help="Single query mode")
    parser.add_argument("--dashboard", action="store_true", help="Show metrics dashboard")
    parser.add_argument("--max-tests", type=int, help="Max test cases for eval mode")
    args = parser.parse_args()

    agent = ProductionAgent()

    if args.dashboard:
        print(agent.get_dashboard())
    elif args.eval:
        eval_mode(agent, max_tests=args.max_tests)
    elif args.query:
        single_query_mode(agent, args.query)
    else:
        interactive_mode(agent)


if __name__ == "__main__":
    main()
