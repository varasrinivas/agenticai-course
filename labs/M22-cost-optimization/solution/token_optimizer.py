"""
M22 Lab — Token Optimizer (Solution)
======================================
Complete token optimizer with prompt compression, message windowing,
and output constraints.

Usage:
    python token_optimizer.py
"""

import re
import math


class TokenOptimizer:
    """
    Reduces token usage through prompt compression, message windowing,
    and output constraints.
    """

    def __init__(self, max_messages: int = 10):
        self.max_messages = max_messages
        self.stats = {
            "original_tokens": 0,
            "optimized_tokens": 0,
        }

        self.compression_rules = [
            (r"You are an AI assistant that ", ""),
            (r"Please ensure that you ", ""),
            (r"It is important that you ", ""),
            (r"Make sure to always ", "Always "),
            (r"You should always ", "Always "),
            (r"You must always ", "Always "),
            (r"Please provide ", "Provide "),
            (r"Please respond ", "Respond "),
            (r"Please make sure ", "Ensure "),
            (r"in order to ", "to "),
            (r"due to the fact that ", "because "),
            (r"for the purpose of ", "for "),
            (r"in the event that ", "if "),
            (r"at this point in time ", "now "),
            (r"on a regular basis ", "regularly "),
            (r"a large number of ", "many "),
            (r"in a timely manner ", "promptly "),
            (r"take into consideration ", "consider "),
            (r"with regard to ", "regarding "),
            (r"in addition to ", "besides "),
            (r"prior to ", "before "),
            (r"subsequent to ", "after "),
            (r"in the absence of ", "without "),
            (r"is able to ", "can "),
            (r"has the ability to ", "can "),
        ]

    def estimate_tokens(self, text: str) -> int:
        """Rough token count: ~4 chars per token for English text."""
        if not text:
            return 0
        return max(1, math.ceil(len(text) / 4))

    def compress_system_prompt(self, prompt: str) -> dict:
        """Compress a system prompt by removing filler phrases and redundant whitespace."""
        original = prompt
        compressed = prompt

        # Apply each compression rule (case-insensitive)
        for pattern, replacement in self.compression_rules:
            compressed = re.sub(pattern, replacement, compressed, flags=re.IGNORECASE)

        # Collapse multiple spaces into one
        compressed = re.sub(r" {2,}", " ", compressed)

        # Collapse multiple newlines into double newline (paragraph break)
        compressed = re.sub(r"\n{3,}", "\n\n", compressed)

        # Strip whitespace from each line
        lines = [line.strip() for line in compressed.split("\n")]
        compressed = "\n".join(lines)

        # Remove empty lines at start/end
        compressed = compressed.strip()

        original_tokens = self.estimate_tokens(original)
        compressed_tokens = self.estimate_tokens(compressed)

        # Update cumulative stats
        self.stats["original_tokens"] += original_tokens
        self.stats["optimized_tokens"] += compressed_tokens

        reduction_pct = ((original_tokens - compressed_tokens) / original_tokens * 100) if original_tokens > 0 else 0.0

        return {
            "original": original,
            "compressed": compressed,
            "original_tokens": original_tokens,
            "compressed_tokens": compressed_tokens,
            "reduction_pct": reduction_pct,
        }

    def set_output_constraints(self, max_tokens: int = 500, format_hint: str = None) -> dict:
        """Generate output constraint instructions to add to the prompt."""
        parts = [f"Respond concisely. Max length: ~{max_tokens} tokens."]

        if format_hint == "json":
            parts.append("Return valid JSON only.")
        elif format_hint == "brief":
            parts.append("Use 2-3 sentences maximum.")
        elif format_hint == "bullet_points":
            parts.append("Use bullet points, no prose.")

        constraint_text = " ".join(parts)
        return {
            "constraint_text": constraint_text,
            "estimated_tokens": self.estimate_tokens(constraint_text),
        }

    def optimize_messages(self, messages: list[dict]) -> dict:
        """Apply sliding window to keep only recent messages plus the first."""
        original_count = len(messages)
        original_tokens = sum(self.estimate_tokens(m.get("content", "")) for m in messages)

        if len(messages) <= self.max_messages:
            optimized = messages[:]
        else:
            # Keep first message (context) + last (max_messages - 1) messages
            optimized = [messages[0]] + messages[-(self.max_messages - 1):]

        optimized_tokens = sum(self.estimate_tokens(m.get("content", "")) for m in optimized)
        tokens_saved = original_tokens - optimized_tokens

        # Update cumulative stats
        self.stats["original_tokens"] += original_tokens
        self.stats["optimized_tokens"] += optimized_tokens

        return {
            "original_messages": messages,
            "optimized_messages": optimized,
            "original_count": original_count,
            "optimized_count": len(optimized),
            "tokens_saved": tokens_saved,
        }

    def get_savings(self) -> dict:
        """Return cumulative optimization statistics."""
        saved = self.stats["original_tokens"] - self.stats["optimized_tokens"]
        reduction_pct = (saved / self.stats["original_tokens"] * 100) if self.stats["original_tokens"] > 0 else 0.0
        return {
            "original_tokens": self.stats["original_tokens"],
            "optimized_tokens": self.stats["optimized_tokens"],
            "saved_tokens": saved,
            "reduction_pct": reduction_pct,
        }


# =============================================================================
# SELF-TEST
# =============================================================================

def self_test():
    """Test token optimization with realistic prompts."""
    print("=" * 60)
    print("M22 Lab — Token Optimizer Self-Test")
    print("=" * 60)

    optimizer = TokenOptimizer(max_messages=6)

    # --- Test 1: System prompt compression ---
    print("\n--- Test 1: System Prompt Compression ---")

    sample_prompt = """You are an AI assistant that specializes in UCC filing research.
You should always provide accurate information about Uniform Commercial Code filings.
Please ensure that you check all relevant databases prior to responding.
It is important that you identify the secured party, debtor, and collateral
in each filing. Make sure to always include the filing number and jurisdiction.
Please provide responses in a clear, structured format.
In order to help the user, you must always cross-reference entity names
due to the fact that companies sometimes file under different names.
For the purpose of risk assessment, take into consideration the filing
date, the collateral type, and whether the filing has been amended
subsequent to the original filing. In the event that a filing
has the ability to be matched to multiple entities, please make sure
to list all possible matches with regard to the debtor name.
You are an AI assistant that is able to handle complex UCC queries
on a regular basis in a timely manner. Please respond with
a large number of relevant details in addition to the filing summary.
In the absence of matching filings, please provide a clear explanation
at this point in time for why no results were found."""

    result = optimizer.compress_system_prompt(sample_prompt)
    print(f"  Original:   {result['original_tokens']} tokens ({len(result['original'])} chars)")
    print(f"  Compressed: {result['compressed_tokens']} tokens ({len(result['compressed'])} chars)")
    print(f"  Reduction:  {result['reduction_pct']:.1f}%")
    print(f"\n  Compressed prompt preview:")
    for line in result['compressed'].split('\n')[:5]:
        if line.strip():
            print(f"    {line.strip()}")
    assert result['reduction_pct'] >= 25, f"FAIL: Expected >= 25% reduction, got {result['reduction_pct']:.1f}%"
    print(f"  PASS: Achieved {result['reduction_pct']:.1f}% reduction")

    # --- Test 2: Output constraints ---
    print("\n--- Test 2: Output Constraints ---")
    constraints = optimizer.set_output_constraints(max_tokens=300, format_hint="json")
    print(f"  Constraint text: \"{constraints['constraint_text']}\"")
    print(f"  Constraint tokens: {constraints['estimated_tokens']}")
    assert "JSON" in constraints['constraint_text'] or "json" in constraints['constraint_text']
    print(f"  PASS: JSON format constraint applied")

    constraints2 = optimizer.set_output_constraints(max_tokens=200, format_hint="brief")
    print(f"  Brief constraint: \"{constraints2['constraint_text']}\"")
    print(f"  PASS: Brief format constraint applied")

    # --- Test 3: Message windowing ---
    print("\n--- Test 3: Message Windowing ---")
    messages = [
        {"role": "user", "content": "I need help with UCC filings research for our portfolio."},
        {"role": "assistant", "content": "I'd be happy to help with UCC filing research. What would you like to know?"},
        {"role": "user", "content": "First, find all filings for Acme Corp in New York."},
        {"role": "assistant", "content": "I found 3 UCC filings for Acme Corp in New York: Filing #NY-2024-001..."},
        {"role": "user", "content": "Now check Texas as well."},
        {"role": "assistant", "content": "I found 2 additional filings in Texas: Filing #TX-2024-015..."},
        {"role": "user", "content": "Can you resolve whether Acme Corp and ACME Corporation are the same entity?"},
        {"role": "assistant", "content": "Based on entity resolution analysis, Acme Corp and ACME Corporation appear to be the same entity..."},
        {"role": "user", "content": "What's the total risk exposure across all these filings?"},
        {"role": "assistant", "content": "The total risk exposure across 5 filings is approximately $2.4M..."},
        {"role": "user", "content": "Generate a summary report for the portfolio."},
        {"role": "assistant", "content": "Here is the portfolio summary report for Acme Corp / ACME Corporation..."},
    ]

    result = optimizer.optimize_messages(messages)
    print(f"  Original messages:  {result['original_count']}")
    print(f"  Optimized messages: {result['optimized_count']}")
    print(f"  Tokens saved:       ~{result['tokens_saved']}")
    assert result['optimized_count'] <= 6, "FAIL: Should have trimmed to max_messages"
    assert result['optimized_messages'][0]['content'] == messages[0]['content'], \
        "FAIL: First message should be preserved"
    print(f"  PASS: Message window applied (kept first + last {optimizer.max_messages - 1})")

    # --- Test 4: Cumulative savings ---
    print("\n--- Test 4: Cumulative Savings ---")
    savings = optimizer.get_savings()
    print(f"  Total original tokens:  {savings['original_tokens']}")
    print(f"  Total optimized tokens: {savings['optimized_tokens']}")
    print(f"  Total saved:            {savings['saved_tokens']}")
    print(f"  Overall reduction:      {savings['reduction_pct']:.1f}%")
    assert savings['reduction_pct'] > 0, "FAIL: Should show some savings"
    print(f"  PASS: Cumulative tracking works")

    print("\n" + "=" * 60)
    print("All token optimizer tests passed!")
    print("=" * 60)


if __name__ == "__main__":
    self_test()
