"""
M22 Lab — Optimized Agent (Solution)
======================================
Complete optimization pipeline composing cache, router, optimizer,
and tracker for side-by-side cost comparison.

Usage:
    python optimized_agent.py
"""

import time
import random

from response_cache import ResponseCache
from model_router import ModelRouter, MODEL_PRICING
from token_optimizer import TokenOptimizer
from cost_tracker import CostTracker


# =============================================================================
# MOCK UCC AGENT
# =============================================================================

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
    jitter = random.uniform(0.85, 1.15)
    return {
        "answer": response_data["answer"],
        "input_tokens": int(response_data["input_tokens"] * jitter),
        "output_tokens": int(response_data["output_tokens"] * jitter),
        "model": model,
    }


class OptimizedAgent:
    """UCC filing agent with full cost optimization pipeline."""

    def __init__(self, cache_ttl: int = 300, cache_max: int = 1000):
        self.cache = ResponseCache(ttl_seconds=cache_ttl, max_entries=cache_max)
        self.router = ModelRouter()
        self.optimizer = TokenOptimizer(max_messages=8)
        self.tracker = CostTracker()
        self.system_prompt = SYSTEM_PROMPT

        # Compress the system prompt once at startup
        compression = self.optimizer.compress_system_prompt(SYSTEM_PROMPT)
        self.optimized_prompt = compression["compressed"]
        self.prompt_savings = compression

    def run(self, query: str) -> dict:
        """Run a query through the full optimization pipeline."""
        # Step 1: Check cache
        cached_response = self.cache.get(query)
        if cached_response is not None:
            # Cache hit — record zero-cost call
            self.tracker.record(
                model=cached_response.get("model", "claude-sonnet-4"),
                input_tokens=cached_response.get("input_tokens", 500),
                output_tokens=cached_response.get("output_tokens", 200),
                cached=True,
            )
            return {
                "answer": cached_response["answer"],
                "model": cached_response.get("model", "unknown"),
                "task_type": cached_response.get("task_type", "unknown"),
                "cached": True,
                "cost": 0.0,
                "cache_stats": self.cache.get_stats(),
            }

        # Step 2: Route to appropriate model
        routing = self.router.route(query)

        # Step 3: Execute (mock API call with optimized prompt)
        response = mock_api_call(
            routing["model"],
            self.optimized_prompt,
            query,
            routing["task_type"],
        )

        # Step 4: Track cost
        record = self.tracker.record(
            model=routing["model"],
            input_tokens=response["input_tokens"],
            output_tokens=response["output_tokens"],
        )

        # Step 5: Cache the response
        self.cache.set(query, {
            "answer": response["answer"],
            "model": routing["model"],
            "task_type": routing["task_type"],
            "input_tokens": response["input_tokens"],
            "output_tokens": response["output_tokens"],
        })

        # Step 6: Return result with metadata
        return {
            "answer": response["answer"],
            "model": routing["model"],
            "model_display": routing["display_name"],
            "task_type": routing["task_type"],
            "routing_reason": routing["reason"],
            "cached": False,
            "cost": record["cost"],
            "input_tokens": response["input_tokens"],
            "output_tokens": response["output_tokens"],
            "cache_stats": self.cache.get_stats(),
        }

    def run_batch(self, queries: list[str]) -> list[dict]:
        """Process multiple queries with batch API pricing (50% discount)."""
        results = []
        for query in queries:
            # Check cache first
            cached_response = self.cache.get(query)
            if cached_response is not None:
                self.tracker.record(
                    model=cached_response.get("model", "claude-sonnet-4"),
                    input_tokens=cached_response.get("input_tokens", 500),
                    output_tokens=cached_response.get("output_tokens", 200),
                    cached=True,
                )
                results.append({
                    "answer": cached_response["answer"],
                    "model": cached_response.get("model"),
                    "cached": True,
                    "batch": True,
                    "cost": 0.0,
                })
                continue

            # Route and execute with batch discount
            routing = self.router.route(query)
            response = mock_api_call(
                routing["model"], self.optimized_prompt, query, routing["task_type"]
            )

            record = self.tracker.record(
                model=routing["model"],
                input_tokens=response["input_tokens"],
                output_tokens=response["output_tokens"],
                batch=True,
            )

            self.cache.set(query, {
                "answer": response["answer"],
                "model": routing["model"],
                "task_type": routing["task_type"],
                "input_tokens": response["input_tokens"],
                "output_tokens": response["output_tokens"],
            })

            results.append({
                "answer": response["answer"],
                "model": routing["model"],
                "model_display": routing["display_name"],
                "task_type": routing["task_type"],
                "cached": False,
                "batch": True,
                "cost": record["cost"],
            })

        return results

    def compare_costs(self, queries: list[str]) -> str:
        """Run the same queries with and without optimization, show savings."""
        # --- OPTIMIZED: Route + cache (run first to collect actual token counts) ---
        self.cache = ResponseCache(ttl_seconds=300, max_entries=1000)
        self.tracker = CostTracker()

        for query in queries:
            self.run(query)

        # --- BASELINE: All Sonnet, no cache, same token counts ---
        # Use actual token counts from optimized run so comparison is fair.
        # Every query hits Sonnet regardless of complexity; no caching.
        baseline_tracker = CostTracker()
        for record in self.tracker.records:
            baseline_tracker.record(
                "claude-sonnet-4",
                record["input_tokens"],
                record["output_tokens"],
            )

        baseline_total = baseline_tracker.get_total_cost()
        baseline_avg = baseline_total / len(queries) if queries else 0

        optimized_total = self.tracker.get_total_cost()
        optimized_avg = optimized_total / len(queries) if queries else 0

        cache_info = self.tracker.get_savings_from_cache()
        by_model = self.tracker.get_cost_by_model()

        savings_amount = baseline_total - optimized_total
        savings_pct = (savings_amount / baseline_total * 100) if baseline_total > 0 else 0

        # Count model distribution (non-cached calls only)
        haiku_calls = by_model.get("claude-haiku-4-5-20251001", {}).get("calls", 0) - \
            sum(1 for r in self.tracker.records if r["model"] == "claude-haiku-4-5-20251001" and r["cached"])
        sonnet_calls = by_model.get("claude-sonnet-4", {}).get("calls", 0) - \
            sum(1 for r in self.tracker.records if r["model"] == "claude-sonnet-4" and r["cached"])
        opus_calls = by_model.get("claude-opus-4", {}).get("calls", 0) - \
            sum(1 for r in self.tracker.records if r["model"] == "claude-opus-4" and r["cached"])

        cache_hit_pct = (cache_info["cache_hits"] / len(queries) * 100) if queries else 0

        # Build report
        lines = [
            "",
            "=" * 50,
            "       COST OPTIMIZATION REPORT",
            "=" * 50,
            "",
            "Baseline (all Sonnet, no cache):",
            f"  Queries:        {len(queries)}",
            f"  Total cost:     ${baseline_total:.4f}",
            f"  Avg cost/query: ${baseline_avg:.4f}",
            "",
            "Optimized (routing + cache):",
            f"  Queries:        {len(queries)}",
            f"  Cache hits:     {cache_info['cache_hits']} ({cache_hit_pct:.0f}%)",
            f"  Model routing:  {haiku_calls} Haiku, {sonnet_calls} Sonnet, {opus_calls} Opus",
            f"  Total cost:     ${optimized_total:.4f}",
            f"  Avg cost/query: ${optimized_avg:.4f}",
            "",
            f"Savings: ${savings_amount:.4f} ({savings_pct:.1f}% reduction)",
            "",
            "--- Prompt Compression ---",
            f"  Original:   {self.prompt_savings['original_tokens']} tokens",
            f"  Compressed: {self.prompt_savings['compressed_tokens']} tokens",
            f"  Reduction:  {self.prompt_savings['reduction_pct']:.1f}%",
            "",
            "=" * 50,
        ]

        return "\n".join(lines)


# =============================================================================
# SELF-TEST
# =============================================================================

def self_test():
    """Run 20 queries and show before/after cost comparison."""
    print("=" * 60)
    print("M22 Lab — Optimized Agent Self-Test")
    print("=" * 60)

    random.seed(42)

    test_queries = [
        "Find all UCC filings for Acme Corp in New York",       # Haiku
        "Search for filings in Texas filed in 2024",            # Haiku
        "List all secured parties in California",               # Haiku
        "Resolve entity: is 'Acme Corp' the same as 'ACME Corporation'?",  # Sonnet
        "Find all UCC filings for Acme Corp in New York",       # cache hit
        "Assess the risk exposure for Greenfield Logistics",    # Opus
        "Find filings for Nextera Holdings in Delaware",        # Haiku
        "What is a UCC continuation statement?",                # Sonnet (general)
        "Search for filings in Texas filed in 2024",            # cache hit
        "Show me the debtor list for filing NY-2024-001",       # Haiku
        "Find filings with equipment as the secured interest",  # Haiku
        "Find all UCC filings for Acme Corp in New York",       # cache hit
        "List amendment history for filing #NY-2024-001",       # Haiku
        "What are the requirements for a UCC-3 filing?",        # Haiku
        "Assess the risk exposure for Greenfield Logistics",    # cache hit
        "Find continuation filings in New York",                # Haiku
        "Resolve entity: Nextera Holdings vs NextEra Holdings Inc",  # Sonnet
        "Search for filings in Texas filed in 2024",            # cache hit
        "What does perfected security interest mean?",          # Sonnet (general)
        "Find all UCC filings for Acme Corp in New York",       # cache hit
    ]

    agent = OptimizedAgent(cache_ttl=300, cache_max=100)

    # Show individual query results
    print("\n--- Query-by-Query Results ---")
    agent_fresh = OptimizedAgent(cache_ttl=300, cache_max=100)
    for i, query in enumerate(test_queries):
        result = agent_fresh.run(query)
        cached_tag = " [CACHED]" if result["cached"] else ""
        model_tag = result.get("model_display", result.get("model", "cached"))
        print(f"  Q{i+1:2d}: {query[:55]:55s} -> {model_tag:10s} ${result['cost']:.4f}{cached_tag}")

    # Run comparison
    report = agent.compare_costs(test_queries)
    print(report)

    print("\n" + "=" * 60)
    print("Optimization pipeline complete!")
    print("=" * 60)


if __name__ == "__main__":
    self_test()
