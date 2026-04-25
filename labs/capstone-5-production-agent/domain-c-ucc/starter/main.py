"""
Main entry point for the UCC Production Agent system.

This orchestrates:
1. Query intake
2. Routing to specialist agents
3. Memory management (working, episodic, procedural)
4. Model selection (cost-optimized)
5. Observability (tracing + metrics)
6. Response delivery

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
from typing import Any, Dict, Optional

from anthropic import Anthropic

from config import ANTHROPIC_API_KEY, APP_CONFIG, OBSERVABILITY, MODEL_TIERS
from memory import WorkingMemory, EpisodicMemory, ProceduralMemory
from agents import RouterAgent, FilingAgent, EntityAgent, RiskAgent
from model_router import ModelRouter
from observability import Tracer, MetricsCollector


class ProductionAgent:
    """
    The top-level production agent that orchestrates the entire system.

    This is the "control tower" — it manages memory, routes queries,
    invokes specialist agents, tracks everything with tracing/metrics,
    and learns from experience.
    """

    def __init__(self):
        # API client
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

        # Model router (cost optimization)
        self.model_router = ModelRouter()

        # Observability
        self.tracer = Tracer()
        self.metrics = MetricsCollector()

    # ------------------------------------------------------------------
    # TODO 1: Implement process_query()
    # The main query processing pipeline:
    #
    # 1. START TRACE — tracer.start_trace("process_query")
    #
    # 2. WORKING MEMORY — set the current query
    #
    # 3. CHECK EPISODIC MEMORY — recall similar past queries
    #    If a highly similar past query exists (score > 0.8), add it
    #    as context to working memory.
    #
    # 4. CHECK PROCEDURAL MEMORY — find applicable rules
    #    Extract keywords from query, find rules, add to working memory.
    #
    # 5. ROUTE — router_agent.route(query) to determine task_type,
    #    complexity, model_tier, and target agent(s)
    #    Start a span for routing.
    #
    # 6. MODEL SELECTION — model_router.route() to select model tier
    #    Record the routing decision.
    #
    # 7. EXECUTE AGENT(S) — call the target agent(s) in sequence
    #    For each agent:
    #      - Start a span
    #      - Set the model tier on the agent
    #      - Call agent.process(query)
    #      - Record tool calls in working memory
    #      - Record intermediate results
    #      - End the span
    #
    # 8. RECORD METRICS — record cost, latency, tokens
    #
    # 9. STORE EPISODE — save this query/response for future recall
    #
    # 10. END TRACE — tracer.end_trace()
    #
    # 11. CLEAR WORKING MEMORY
    #
    # Return the final response dict.
    # ------------------------------------------------------------------
    def process_query(self, query: str) -> Dict[str, Any]:
        """
        Process a user query through the full production pipeline.

        Returns:
            dict with keys:
            - answer: str
            - task_type: str
            - model_tier: str
            - trace_id: str
            - tool_calls: list
            - latency_ms: float
        """
        # TODO: Implement the full processing pipeline
        pass

    # ------------------------------------------------------------------
    # TODO 2: Implement _select_agent()
    # Given an agent name string, return the agent instance.
    # "filing_agent" → self.filing_agent
    # "entity_agent" → self.entity_agent
    # "risk_agent" → self.risk_agent
    # ------------------------------------------------------------------
    def _select_agent(self, agent_name: str):
        """Select an agent instance by name."""
        # TODO: Map agent name to instance
        pass

    # ------------------------------------------------------------------
    # TODO 3: Implement get_dashboard()
    # Return the metrics dashboard string.
    # ------------------------------------------------------------------
    def get_dashboard(self) -> str:
        """Return the metrics dashboard."""
        # TODO: Return self.metrics.format_dashboard()
        pass

    # ------------------------------------------------------------------
    # TODO 4: Implement get_trace()
    # Return the formatted trace for a given trace_id.
    # ------------------------------------------------------------------
    def get_trace(self, trace_id: str) -> str:
        """Return formatted trace for a request."""
        # TODO: Return self.tracer.format_trace(trace_id)
        pass


# ---------------------------------------------------------------------------
# CLI Interface
# ---------------------------------------------------------------------------
def interactive_mode(agent: ProductionAgent):
    """Run the agent in interactive mode."""
    print("=" * 60)
    print("  UCC Production Agent — Interactive Mode")
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
    """Run the evaluation suite."""
    from evaluation import EvaluationHarness

    print("=" * 60)
    print("  UCC Production Agent — Evaluation Mode")
    print("=" * 60)
    print()

    harness = EvaluationHarness()
    print(f"Loaded {harness.test_count} test cases")
    print("Running evaluation...\n")

    report = harness.run_all(
        agent_fn=agent.process_query,
        max_tests=max_tests,
    )

    print(harness.format_report(report))
    print("\nMetrics Dashboard:")
    print(agent.get_dashboard())


def single_query_mode(agent: ProductionAgent, query: str):
    """Process a single query."""
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
