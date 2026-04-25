"""
M27 Lab — Exercise 1: Anti-Pattern Identification Quiz
=======================================================
Build an interactive display of all 18 certification anti-patterns.
For each anti-pattern, display the number, name, domain, a problematic
scenario, the explanation, and the correct pattern.

YOUR TASK: Complete the ANTI_PATTERNS list (3 examples given, add the
remaining 15) and implement display_anti_pattern() and run_quiz().
"""


# --- Anti-Pattern Data Structure ---
# Each entry: (number, name, domain, domain_name, scenario, correct_pattern)

ANTI_PATTERNS = [
    {
        "number": 1,
        "name": "Text-parsing for loop termination",
        "domain": 1,
        "domain_name": "Agentic Architecture",
        "scenario": (
            "The agent loop checks if the model's text contains 'DONE' or "
            "'Here is your answer' to decide when to stop."
        ),
        "why_wrong": (
            "Natural language parsing is non-deterministic. The model might "
            "say 'done' mid-thought or forget the keyword when actually finished."
        ),
        "correct_pattern": (
            "Check stop_reason field: continue on 'tool_use', stop on 'end_turn'. "
            "This is the ONLY reliable termination signal."
        ),
    },
    {
        "number": 2,
        "name": "Fixed iteration caps as primary stop",
        "domain": 1,
        "domain_name": "Agentic Architecture",
        "scenario": (
            "The agent loop always stops after exactly 5 iterations, regardless "
            "of whether the task is complete."
        ),
        "why_wrong": (
            "Arbitrary caps prevent the agent from finishing complex tasks and "
            "waste resources on simple ones. A 1-step task still runs 5 loops."
        ),
        "correct_pattern": (
            "Use stop_reason as the primary signal. Use max_turns as a SAFETY "
            "NET only — a backstop, not the main mechanism."
        ),
    },
    {
        "number": 3,
        "name": "Prompt-based enforcement for critical rules",
        "domain": 1,
        "domain_name": "Agentic Architecture",
        "scenario": (
            "The system prompt says 'NEVER issue refunds over $500 without "
            "approval' but the agent occasionally does it anyway."
        ),
        "why_wrong": (
            "Prompts are probabilistic. No matter how strongly worded, the "
            "model can be persuaded by context to violate the instruction."
        ),
        "correct_pattern": (
            "Implement PreToolUse hooks that programmatically block the tool "
            "call. Hooks provide 100% deterministic enforcement."
        ),
    },
    # TODO: Add anti-patterns 4 through 18
    # Hint: The remaining anti-patterns cover:
    #   4  - Sentiment-based escalation (Domain 1)
    #   5  - Missing input validation (Domain 2)
    #   6  - Generic error messages (Domain 2)
    #   7  - Empty results without context (Domain 2)
    #   8  - Too many tools on one agent (Domain 2)
    #   9  - Hardcoded secrets in config (Domain 2)
    #   10 - Personal preferences in project CLAUDE.md (Domain 3)
    #   11 - Skipping plan mode for complex changes (Domain 3)
    #   12 - Shared sessions in CI/CD (Domain 3)
    #   13 - Vague instructions (Domain 4)
    #   14 - Session bleed in CI/CD (Domain 3)
    #   15 - No structured output schema (Domain 4)
    #   16 - Progressive summarization of critical details (Domain 5)
    #   17 - Aggregate-only accuracy metrics (Domain 5)
    #   18 - Missing provenance fields (Domain 5)
]


def display_anti_pattern(ap: dict) -> None:
    """Display a single anti-pattern with formatting.

    TODO: Implement this function. It should print:
    - Anti-pattern number and name
    - Domain mapping
    - The problematic scenario
    - Why it's wrong
    - The correct pattern
    """
    pass  # YOUR CODE HERE


def run_quiz() -> None:
    """Iterate through all anti-patterns and display each one.

    TODO: Implement this function. It should:
    1. Print a header
    2. Loop through ANTI_PATTERNS
    3. Call display_anti_pattern() for each
    4. Print a summary with domain counts at the end
    """
    pass  # YOUR CODE HERE


if __name__ == "__main__":
    run_quiz()
