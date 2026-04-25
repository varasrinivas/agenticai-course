"""
M27 Lab — Exercise 2: Scenario Builder
=======================================
Build an architecture recommendation tool for the 6 exam scenarios.
Given a scenario number, output the recommended components, tools,
hooks, session strategy, and escalation rules.

YOUR TASK: Complete the SCENARIOS dict (2 examples given, add 4 more)
and implement build_architecture() and display_scenario().
"""


SCENARIOS = {
    1: {
        "name": "Customer Support Agent",
        "description": (
            "An AI agent handling customer inquiries for a UCC filing service. "
            "Handles lookups, risk checks, password resets, and refund requests."
        ),
        "components": {
            "agent_type": "Single ReAct agent with tool loop",
            "model": "Claude Sonnet for speed, Opus for complex cases",
            "tools": [
                "lookup_filing(filing_id) -> filing details",
                "check_risk_profile(entity_name) -> risk score",
                "issue_refund(amount, reason) -> confirmation",
                "reset_password(user_id) -> temp password",
                "escalate_to_human(reason, context) -> ticket_id",
            ],
            "hooks": [
                "PreToolUse on issue_refund: block if amount > $500",
                "PostToolUse on all tools: log tool calls for audit",
            ],
        },
        "session_strategy": "Single session per customer conversation",
        "escalation_rules": [
            "Policy gap — agent lacks authority",
            "Explicit customer request for human",
            "Refund > $500 (blocked by hook, needs human approval)",
            "NOT triggered by: sentiment, profanity, repeated questions",
        ],
        "anti_patterns_to_avoid": [1, 2, 3, 4],
    },
    2: {
        "name": "Claude Code Configuration",
        "description": (
            "Setting up Claude Code for a development team with project "
            "conventions, personal preferences, and CI/CD integration."
        ),
        "components": {
            "agent_type": "Claude Code with custom commands and skills",
            "model": "Claude Sonnet for daily coding, Opus for architecture",
            "tools": [
                "Read, Edit, Write for file operations",
                "Grep for content search",
                "Glob for file pattern matching",
                "Bash for shell commands",
            ],
            "hooks": [
                "PreToolUse on Bash: block destructive commands in CI",
                "PostToolUse on Write: validate file format",
            ],
        },
        "session_strategy": (
            "Isolated sessions per CI job (--session-id per PR). "
            "Long-running sessions for interactive development."
        ),
        "escalation_rules": [
            "Complex architectural decisions -> plan mode",
            "Conflicting CLAUDE.md rules -> human resolution",
            "CI failures after 3 retries -> alert team",
        ],
        "anti_patterns_to_avoid": [10, 11, 12, 14],
    },
    # TODO: Add scenarios 3-6
    # 3: Multi-Agent Research System
    # 4: Developer Productivity Tools
    # 5: CI/CD Pipeline Integration
    # 6: Structured Data Extraction
}


def build_architecture(scenario_num: int) -> dict:
    """Return the architecture recommendation for a given scenario.

    TODO: Implement this function. It should:
    1. Look up the scenario by number
    2. Return the full architecture dict
    3. Raise ValueError if scenario not found
    """
    pass  # YOUR CODE HERE


def display_scenario(scenario: dict) -> None:
    """Display a scenario's architecture recommendation with formatting.

    TODO: Implement this function. It should print:
    - Scenario name and description
    - Components (agent type, model, tools, hooks)
    - Session strategy
    - Escalation rules
    - Anti-patterns to avoid
    """
    pass  # YOUR CODE HERE


def run_all() -> None:
    """Display architecture for all 6 scenarios.

    TODO: Implement this function.
    """
    pass  # YOUR CODE HERE


if __name__ == "__main__":
    run_all()
