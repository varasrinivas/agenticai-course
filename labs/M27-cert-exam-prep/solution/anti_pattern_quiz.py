"""
M27 Lab — Exercise 1 SOLUTION: Anti-Pattern Identification Quiz
================================================================
Displays all 18 certification anti-patterns with scenarios,
explanations, correct patterns, and domain mappings.
"""


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
    {
        "number": 4,
        "name": "Sentiment-based escalation",
        "domain": 1,
        "domain_name": "Agentic Architecture",
        "scenario": (
            "The agent escalates to a human whenever the customer uses profanity "
            "or has a negative sentiment score above 0.8."
        ),
        "why_wrong": (
            "Angry customers with simple requests (password resets, status checks) "
            "waste human agent time. Sentiment does not correlate with task complexity."
        ),
        "correct_pattern": (
            "Escalate based on capability limits: policy gaps, authority limits, "
            "explicit user request, or business thresholds. Never on sentiment alone."
        ),
    },
    {
        "number": 5,
        "name": "Missing input validation on tools",
        "domain": 2,
        "domain_name": "Tool Design & MCP",
        "scenario": (
            "The lookup_filing tool accepts any string as a filing ID without "
            "checking format. The model passes 'show me all filings' as the ID."
        ),
        "why_wrong": (
            "Without input validation, natural language bleeds into tool parameters. "
            "The tool executes an invalid query and returns confusing results."
        ),
        "correct_pattern": (
            "Validate inputs against expected patterns (e.g., regex for filing IDs). "
            "Return specific errors: {\"error\": \"Invalid filing ID format. Expected: "
            "UCC-YYYY-ST-NNNNNNN\", \"isError\": true}."
        ),
    },
    {
        "number": 6,
        "name": "Generic error messages",
        "domain": 2,
        "domain_name": "Tool Design & MCP",
        "scenario": (
            "Every tool error returns: {\"error\": \"Something went wrong\", "
            "\"isError\": true}. The agent retries permission errors and gives up "
            "on transient network errors."
        ),
        "why_wrong": (
            "Generic errors prevent the model from making intelligent retry decisions. "
            "It cannot distinguish retryable from non-retryable failures."
        ),
        "correct_pattern": (
            "Return structured errors with errorCategory, isRetryable, and "
            "retrySuggestion fields. Example: {\"error\": \"DB timeout after 30s\", "
            "\"errorCategory\": \"connection\", \"isRetryable\": true}."
        ),
    },
    {
        "number": 7,
        "name": "Empty results without context",
        "domain": 2,
        "domain_name": "Tool Design & MCP",
        "scenario": (
            "The search tool returns {\"results\": []} for both 'no matches found' "
            "and 'access denied' cases."
        ),
        "why_wrong": (
            "The model cannot distinguish between 'searched successfully, found nothing' "
            "and 'could not execute the search'. It may tell users no results exist "
            "when the search simply failed."
        ),
        "correct_pattern": (
            "Include access_verified and query echo: {\"results\": [], \"count\": 0, "
            "\"access_verified\": true, \"query\": \"...\"}. For access failures: "
            "{\"results\": [], \"access_verified\": false, \"reason\": \"auth expired\"}."
        ),
    },
    {
        "number": 8,
        "name": "Too many tools on one agent",
        "domain": 2,
        "domain_name": "Tool Design & MCP",
        "scenario": (
            "A coordinator agent has 22 tools. It frequently selects the wrong "
            "tool, confusing search_by_name with search_by_id."
        ),
        "why_wrong": (
            "Model accuracy degrades significantly beyond 8-10 tools. The model "
            "struggles to distinguish between similar tools in a large set."
        ),
        "correct_pattern": (
            "Keep coordinators at 4-5 high-level tools. Distribute specialized "
            "tools to subagents via the Task tool pattern."
        ),
    },
    {
        "number": 9,
        "name": "Hardcoded secrets in config files",
        "domain": 2,
        "domain_name": "Tool Design & MCP",
        "scenario": (
            ".mcp.json contains: {\"env\": {\"DB_PASSWORD\": \"prod_secret_123\"}}. "
            "The file is committed to the repository."
        ),
        "why_wrong": (
            "Config files are often committed to version control. Hardcoded secrets "
            "are exposed to anyone with repo access and persist in git history."
        ),
        "correct_pattern": (
            "Use environment variable references: ${DB_PASSWORD}. Store actual "
            "secrets in .env (gitignored), CI secrets, or a secrets manager."
        ),
    },
    {
        "number": 10,
        "name": "Personal preferences in project CLAUDE.md",
        "domain": 3,
        "domain_name": "Claude Code Configuration",
        "scenario": (
            "A developer adds 'Use vim keybindings' and 'Sign commits with my "
            "GPG key ABC123' to the shared project CLAUDE.md."
        ),
        "why_wrong": (
            "Project CLAUDE.md is shared by the team. Personal preferences imposed "
            "on everyone cause conflicts and confusion."
        ),
        "correct_pattern": (
            "Personal preferences go in ~/.claude/CLAUDE.md (user-level, not committed). "
            "Project CLAUDE.md is for team-wide conventions only."
        ),
    },
    {
        "number": 11,
        "name": "Skipping plan mode for complex changes",
        "domain": 3,
        "domain_name": "Claude Code Configuration",
        "scenario": (
            "A developer lets Claude directly execute a large architectural "
            "refactor across 20 files without reviewing a plan first."
        ),
        "why_wrong": (
            "Without plan review, Claude may choose a technically valid but "
            "architecturally wrong approach. Rework cost is high for large changes."
        ),
        "correct_pattern": (
            "Use plan mode for complex/risky changes: architectural decisions, "
            "large refactors, unfamiliar code areas. Skip only for trivial changes."
        ),
    },
    {
        "number": 12,
        "name": "Shared sessions in CI/CD",
        "domain": 3,
        "domain_name": "Claude Code Configuration",
        "scenario": (
            "All CI review jobs share one long-running Claude session to 'save "
            "context'. Reviews reference code from other pull requests."
        ),
        "why_wrong": (
            "Session bleed: context from PR #1 leaks into the review of PR #2, "
            "causing cross-contamination of review feedback."
        ),
        "correct_pattern": (
            "Use isolated sessions: --session-id per PR or per CI job. Each "
            "review starts with a clean context."
        ),
    },
    {
        "number": 13,
        "name": "Vague instructions",
        "domain": 4,
        "domain_name": "Prompt Engineering & Structured Output",
        "scenario": (
            "Code review prompt: 'Review this code and make it better.' "
            "Reviews are inconsistent — sometimes formatting, sometimes logic."
        ),
        "why_wrong": (
            "'Make it better' gives no criteria for what 'better' means. The model "
            "picks a random focus area each time."
        ),
        "correct_pattern": (
            "Specify exact criteria: 'Check for: (1) null pointer risks, "
            "(2) SQL injection, (3) missing error handling, (4) functions > 50 lines. "
            "Rate each: pass/warn/fail with line numbers.'"
        ),
    },
    {
        "number": 14,
        "name": "Session bleed in CI/CD pipelines",
        "domain": 3,
        "domain_name": "Claude Code Configuration",
        "scenario": (
            "A CI pipeline reuses the same session across multiple PRs. Claude "
            "references variable names from a previous PR's code in its review."
        ),
        "why_wrong": (
            "Without session isolation, the model's context accumulates state "
            "from prior jobs, leading to incorrect or misleading feedback."
        ),
        "correct_pattern": (
            "Assign unique session IDs per CI job: --session-id=\"pr-${PR_NUMBER}-${RUN_ID}\". "
            "Never reuse sessions across independent tasks."
        ),
    },
    {
        "number": 15,
        "name": "No structured output schema",
        "domain": 4,
        "domain_name": "Prompt Engineering & Structured Output",
        "scenario": (
            "Extraction prompt: 'Return the data as JSON.' The model wraps JSON "
            "in markdown fences, adds commentary, or produces invalid JSON."
        ),
        "why_wrong": (
            "Asking for JSON in text is unreliable. The model may include extra text, "
            "markdown formatting, or structural errors that break parsers."
        ),
        "correct_pattern": (
            "Define a tool with a strict JSON schema and use tool_use to force "
            "structured output. The model's tool call always matches the schema."
        ),
    },
    {
        "number": 16,
        "name": "Progressive summarization of critical details",
        "domain": 5,
        "domain_name": "Context & Reliability",
        "scenario": (
            "After /compact, the original query's specific filing numbers and "
            "date ranges are summarized to 'various filings in 2024'."
        ),
        "why_wrong": (
            "/compact is lossy. Critical details like specific IDs, amounts, "
            "dates, and thresholds may be generalized beyond usefulness."
        ),
        "correct_pattern": (
            "Write critical facts to a scratchpad file BEFORE compacting. "
            "Scratchpad files persist on disk and survive context compression."
        ),
    },
    {
        "number": 17,
        "name": "Aggregate-only accuracy metrics",
        "domain": 5,
        "domain_name": "Context & Reliability",
        "scenario": (
            "The system reports 94% overall accuracy, but UCC-1 filings are at "
            "98% while UCC-3 amendments are at 71%."
        ),
        "why_wrong": (
            "Aggregate metrics hide per-category failures. If most queries are "
            "easy (UCC-1), the overall number is misleading."
        ),
        "correct_pattern": (
            "Always use stratified metrics: per-document-type, per-domain, "
            "per-difficulty. Act on the weakest category, not the aggregate."
        ),
    },
    {
        "number": 18,
        "name": "Missing provenance fields",
        "domain": 5,
        "domain_name": "Context & Reliability",
        "scenario": (
            "The report states 'The debtor has no active liens' without indicating "
            "which documents were checked or how confident the finding is."
        ),
        "why_wrong": (
            "Without provenance, findings cannot be audited, verified, or "
            "trusted. Users have no way to assess reliability."
        ),
        "correct_pattern": (
            "Every finding must include 4 provenance fields: source (which docs), "
            "confidence (high/medium/low + reasoning), timestamp, and agent_id."
        ),
    },
]


def display_anti_pattern(ap: dict) -> str:
    """Display a single anti-pattern with formatting. Returns the output string."""
    lines = []
    lines.append(f"  Anti-Pattern #{ap['number']}: {ap['name']}")
    lines.append(f"  Domain: {ap['domain']} — {ap['domain_name']}")
    lines.append(f"")
    lines.append(f"  Scenario:")
    lines.append(f"    {ap['scenario']}")
    lines.append(f"")
    lines.append(f"  Why It's Wrong:")
    lines.append(f"    {ap['why_wrong']}")
    lines.append(f"")
    lines.append(f"  Correct Pattern:")
    lines.append(f"    {ap['correct_pattern']}")

    output = "\n".join(lines)
    print(output)
    return output


def run_quiz() -> str:
    """Iterate through all anti-patterns and display each one."""
    all_output = []

    header = (
        "=" * 56 + "\n"
        "  18 Anti-Patterns for the Claude Certified Architect\n"
        "=" * 56
    )
    print(header)
    all_output.append(header)

    # Domain counters
    domain_counts = {}

    for i, ap in enumerate(ANTI_PATTERNS):
        separator = "\n" + "-" * 56
        print(separator)
        all_output.append(separator)

        output = display_anti_pattern(ap)
        all_output.append(output)

        domain = ap["domain"]
        domain_name = ap["domain_name"]
        if domain not in domain_counts:
            domain_counts[domain] = {"name": domain_name, "count": 0}
        domain_counts[domain]["count"] += 1

    # Summary
    summary_lines = [
        "\n" + "=" * 56,
        "  Summary: Anti-Patterns by Domain",
        "=" * 56,
    ]
    for domain_num in sorted(domain_counts.keys()):
        info = domain_counts[domain_num]
        summary_lines.append(
            f"  Domain {domain_num} ({info['name']}): "
            f"{info['count']} anti-patterns"
        )

    summary_lines.append(f"\n  Total: {len(ANTI_PATTERNS)} anti-patterns across "
                         f"{len(domain_counts)} domains")

    summary = "\n".join(summary_lines)
    print(summary)
    all_output.append(summary)

    return "\n".join(all_output)


if __name__ == "__main__":
    run_quiz()
