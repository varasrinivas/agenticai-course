"""
M22 Lab — Token Optimizer (Starter)
====================================
Compress system prompts, limit output tokens, and trim conversation
history to reduce the number of tokens sent with every API call.

KEY CONCEPT: Tokens are the unit of cost. Every word in your system
prompt is re-sent on EVERY call. A 2000-token system prompt across
1000 daily calls = 2M extra input tokens/day. Compressing that prompt
by 30% saves 600K tokens/day — real money at scale.

Usage:
    python token_optimizer.py
"""

import re


class TokenOptimizer:
    """
    Reduces token usage through prompt compression, message windowing,
    and output constraints.
    """

    def __init__(self, max_messages: int = 10):
        """
        Args:
            max_messages: Maximum number of messages to keep in the sliding window
        """
        self.max_messages = max_messages
        self.stats = {
            "original_tokens": 0,
            "optimized_tokens": 0,
        }

        # Common phrases that can be abbreviated without losing meaning
        self.compression_rules = [
            # (pattern, replacement)
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
        """
        Rough token count estimate. Claude uses ~4 characters per token
        on average for English text.

        Args:
            text: Input text

        Returns:
            Estimated token count
        """
        # TODO: Implement token estimation
        # Simple heuristic: len(text) / 4, rounded up, minimum 1
        pass

    def compress_system_prompt(self, prompt: str) -> dict:
        """
        Compress a system prompt by removing filler phrases and redundant whitespace.

        Args:
            prompt: Original system prompt

        Returns:
            Dict with: original, compressed, original_tokens, compressed_tokens, reduction_pct
        """
        # TODO: Implement prompt compression
        # 1. Store original for comparison
        # 2. Apply each compression rule (regex substitution, case-insensitive)
        # 3. Collapse multiple spaces into one
        # 4. Collapse multiple newlines into two (paragraph break)
        # 5. Strip leading/trailing whitespace from each line
        # 6. Calculate token counts and reduction percentage
        # 7. Update self.stats
        # 8. Return result dict
        pass

    def set_output_constraints(self, max_tokens: int = 500, format_hint: str = None) -> dict:
        """
        Generate output constraint instructions to add to the prompt.

        Args:
            max_tokens: Maximum output tokens to request
            format_hint: Optional format instruction (e.g., "json", "brief", "bullet_points")

        Returns:
            Dict with: constraint_text, estimated_tokens
        """
        # TODO: Implement output constraints
        # Build a short instruction string like:
        #   "Respond concisely. Max length: ~500 tokens."
        #   If format_hint == "json": add "Return valid JSON only."
        #   If format_hint == "brief": add "Use 2-3 sentences maximum."
        #   If format_hint == "bullet_points": add "Use bullet points, no prose."
        # Return dict with the constraint text and its estimated token count
        pass

    def optimize_messages(self, messages: list[dict]) -> dict:
        """
        Apply sliding window to conversation messages, keeping only the
        most recent ones plus the first message (which often has key context).

        Args:
            messages: List of message dicts (role + content)

        Returns:
            Dict with: original_messages, optimized_messages, original_count,
                       optimized_count, tokens_saved
        """
        # TODO: Implement message windowing
        # 1. If len(messages) <= max_messages, return as-is
        # 2. Otherwise: keep messages[0] (first message) + last (max_messages - 1) messages
        # 3. Calculate token savings
        # 4. Update self.stats
        # 5. Return result dict
        pass

    def get_savings(self) -> dict:
        """
        Return cumulative optimization statistics.

        Returns:
            Dict with: original_tokens, optimized_tokens, saved_tokens, reduction_pct
        """
        # TODO: Calculate and return savings from self.stats
        pass


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
    # First message should be preserved
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
