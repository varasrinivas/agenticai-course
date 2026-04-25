"""
M22 Lab — Optimized Agent (Starter)
====================================
Compose cache + router + optimizer + tracker into a full optimization
pipeline. Then run a side-by-side cost comparison to prove the savings.

KEY CONCEPT: Each optimization alone saves a little. Combined, they
compound: caching avoids calls entirely, routing picks the cheapest
model for each call, and token optimization shrinks every call that
does happen. The result is typically 60-75% cost reduction.

Usage:
    python optimized_agent.py
"""

import time
import random

# Import the components you built in Steps 1-4
from response_cache import ResponseCache
from model_router import ModelRouter, MODEL_PRICING
from token_optimizer import TokenOptimizer
from cost_tracker import CostTracker


# =============================================================================
# MOCK UCC AGENT (simulates API calls without spending real tokens)
# =============================================================================

# Simulated system prompt for the UCC agent
SYSTEM_PROMPT = """You are an AI assistant that specializes in UCC filing research and analysis.
You should always provide accurate, detailed information about Uniform Commercial Code filings.
Please ensure that you check all relevant databases prior to responding to any query.
It is important that you identify the secured party, debtor, and collateral description
in each filing. Make sure to always include the filing number, jurisdiction, and filing date.
Please provide responses in a clear, structured format with bullet points.
In order to help the user effectively, you must always cross-reference entity names
due to the fact that companies sometimes file under different names or abbreviations.
For the purpose of risk assessment, take into consideration the filing date, the collateral
type, the number of amendments, and whether the filing has been continued or terminated
subsequent to the original filing date. In the event that a filing has the ability to be
matched to multiple entities, please make sure to list all possible matches with regard
to the debtor name. You are an AI assistant that is able to handle complex UCC queries
on a regular basis in a timely manner."""

MOCK_RESPONSES = {
    "filing_lookup": {
        "answer": "Found 3 UCC filings matching your query. Filing #NY-2024-001 "
                  "(Acme Corp, secured by equipment), Filing #NY-2024-089 (Acme Corp, "
                  "secured by inventory), Filing #TX-2024-015 (Acme Corporation, "
                  "secured by accounts receivable).",
        "input_tokens": 850,
        "output_tokens": 380,
    },
    "entity_resolution": {
        "answer": "Entity resolution complete. 'Acme Corp' and 'ACME Corporation' are "
                  "confirmed to be the same legal entity (EIN match: 12-3456789). Found "
                  "under 3 name variants across 2 jurisdictions.",
        "input_tokens": 1200,
        "output_tokens": 520,
    },
    "risk_analysis": {
        "answer": "Risk assessment for Greenfield Logistics: MODERATE risk. Total secured "
                  "debt: $2.4M across 5 filings. Collateral coverage ratio: 1.3x. Two "
                  "filings expire within 90 days. Recommend monitoring for continuation "
                  "statements. Cross-collateralization detected between NY and TX filings.",
        "input_tokens": 2200,
        "output_tokens": 890,
    },
    "general": {
        "answer": "UCC Article 9 governs secured transactions. A UCC filing (or financing "
                  "statement) is a legal notice that a creditor has an interest in a "
                  "debtor's personal property as collateral for a loan.",
        "input_tokens": 650,
        "output_tokens": 280,
    },
}


def mock_api_call(model: str, system_prompt: str, query: str, task_type: str) -> dict:
    """Simulate an API call with realistic token counts."""
    response_data = MOCK_RESPONSES.get(task_type, MOCK_RESPONSES["general"])
    # Add some randomness to token counts
    jitter = random.uniform(0.85, 1.15)
    return {
        "answer": response_data["answer"],
        "input_tokens": int(response_data["input_tokens"] * jitter),
        "output_tokens": int(response_data["output_tokens"] * jitter),
        "model": model,
    }


class OptimizedAgent:
    """
    UCC filing agent with full cost optimization pipeline.

    Pipeline: Cache Check -> Model Routing -> Token Optimization ->
              Execute (mock) -> Cost Tracking -> Cache Response
    """

    def __init__(self, cache_ttl: int = 300, cache_max: int = 1000):
        """
        Initialize all optimization components.

        Args:
            cache_ttl: Cache time-to-live in seconds
            cache_max: Maximum cache entries
        """
        # TODO: Initialize all four components:
        # self.cache = ResponseCache(...)
        # self.router = ModelRouter()
        # self.optimizer = TokenOptimizer(...)
        # self.tracker = CostTracker()
        # self.system_prompt = SYSTEM_PROMPT
        # self.optimized_prompt = None  (will be set after compression)
        #
        # Then compress the system prompt and store the result
        pass

    def run(self, query: str) -> dict:
        """
        Run a query through the full optimization pipeline.

        Args:
            query: User query string

        Returns:
            Dict with: answer, model, task_type, cached, cost, cache_stats
        """
        # TODO: Implement the full pipeline:
        #
        # Step 1: Check cache
        # cached_response = self.cache.get(query)
        # If cache hit:
        #   - Record in tracker (cached=True, use the model from cached response)
        #   - Return result with cached=True, cost=0
        #
        # Step 2: Route to appropriate model
        # routing = self.router.route(query)
        #
        # Step 3: Execute (mock API call)
        # response = mock_api_call(routing["model"], self.optimized_prompt, query, routing["task_type"])
        #
        # Step 4: Track cost
        # self.tracker.record(routing["model"], response["input_tokens"], response["output_tokens"])
        #
        # Step 5: Cache the response
        # self.cache.set(query, {"answer": response["answer"], "model": routing["model"], ...})
        #
        # Step 6: Return result with metadata
        pass

    def run_batch(self, queries: list[str]) -> list[dict]:
        """
        Process multiple queries with batch API pricing (50% discount).

        In production, you'd use Claude's Batch API for non-time-sensitive
        workloads. Here we simulate the cost savings.

        Args:
            queries: List of query strings

        Returns:
            List of result dicts
        """
        # TODO: Implement batch processing
        # For each query:
        # 1. Check cache first (same as run())
        # 2. Route to appropriate model
        # 3. Execute mock API call
        # 4. Record with batch=True for 50% discount
        # 5. Cache the response
        # Return list of results
        pass

    def compare_costs(self, queries: list[str]) -> str:
        """
        Run the same queries with and without optimization, then show savings.

        Args:
            queries: List of query strings

        Returns:
            Formatted comparison report string
        """
        # TODO: Implement side-by-side comparison
        #
        # 1. OPTIMIZED: Run all queries through the optimization pipeline first
        #    Reset self (create fresh cache + tracker)
        #    For each query, call self.run(query)
        #    Some queries will repeat (for cache hits)
        #
        # 2. BASELINE: Use the same token counts from step 1, but assume all
        #    queries go to Sonnet with no caching:
        #    baseline_tracker = CostTracker()
        #    For each record in self.tracker.records:
        #      baseline_tracker.record("claude-sonnet-4", record["input_tokens"], record["output_tokens"])
        #
        # 3. BUILD REPORT:
        #    Compare baseline total cost vs optimized total cost
        #    Show cache hit rate, model distribution, and savings percentage
        #    Return formatted string
        pass


# =============================================================================
# SELF-TEST
# =============================================================================

def self_test():
    """Run 20 queries and show before/after cost comparison."""
    print("=" * 60)
    print("M22 Lab — Optimized Agent Self-Test")
    print("=" * 60)

    random.seed(42)

    # 20 test queries with some repeats (for cache hits)
    test_queries = [
        "Find all UCC filings for Acme Corp in New York",
        "Search for filings in Texas filed in 2024",
        "List all secured parties in California",
        "Resolve entity: is 'Acme Corp' the same as 'ACME Corporation'?",
        "Find all UCC filings for Acme Corp in New York",  # Repeat -> cache hit
        "Assess the risk exposure for Greenfield Logistics",
        "Find filings for Nextera Holdings in Delaware",
        "What is a UCC continuation statement?",
        "Search for filings in Texas filed in 2024",  # Repeat -> cache hit
        "Identify matching debtors across NY and TX jurisdictions",
        "Evaluate collateral coverage for the Acme portfolio",
        "Find all UCC filings for Acme Corp in New York",  # Repeat -> cache hit
        "List amendment history for filing #NY-2024-001",
        "What are the requirements for a UCC-3 filing?",
        "Assess the risk exposure for Greenfield Logistics",  # Repeat -> cache hit
        "Find filings where equipment is listed as collateral",
        "Resolve entity: Nextera Holdings vs NextEra Holdings Inc",
        "Search for filings in Texas filed in 2024",  # Repeat -> cache hit
        "Generate risk report for all NY filings expiring in 90 days",
        "Find all UCC filings for Acme Corp in New York",  # Repeat -> cache hit
    ]

    agent = OptimizedAgent(cache_ttl=300, cache_max=100)

    # Run comparison
    report = agent.compare_costs(test_queries)
    print(report)

    print("\n" + "=" * 60)
    print("Optimization pipeline complete!")
    print("=" * 60)


if __name__ == "__main__":
    self_test()
