"""
M27 Lab — Exercise 2 SOLUTION: Scenario Builder
=================================================
Architecture recommendation tool for all 6 exam scenarios.
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
    3: {
        "name": "Multi-Agent Research System",
        "description": (
            "A coordinator agent delegates research tasks to specialist "
            "subagents for UCC filing analysis, entity resolution, and risk "
            "scoring. Results are synthesized with source attribution."
        ),
        "components": {
            "agent_type": "Multi-agent: coordinator + 3 specialist subagents",
            "model": "Coordinator: Opus (complex reasoning), Subagents: Sonnet (speed)",
            "tools": [
                "Coordinator: delegate_research, delegate_entity_resolution, delegate_risk_scoring, aggregate_results",
                "Research subagent: search_state_db, search_federal_db, search_vendor_api",
                "Entity subagent: resolve_entity, match_aliases, verify_identity",
                "Risk subagent: calculate_risk_score, check_lien_history, assess_collateral",
            ],
            "hooks": [
                "PreToolUse on all tools: validate inputs, check rate limits",
                "PostToolUse on search tools: add provenance metadata",
                "PostToolUse on aggregate_results: classify findings (Well-established/Contested/Single-source)",
            ],
        },
        "session_strategy": (
            "Coordinator: long-running session with scratchpad for state. "
            "Subagents: short-lived sessions, one per delegation."
        ),
        "escalation_rules": [
            "Contested findings (sources disagree) -> flag for human review",
            "Low confidence results -> request additional data sources",
            "Context window > 80% -> write to scratchpad and compact",
        ],
        "anti_patterns_to_avoid": [8, 16, 17, 18],
    },
    4: {
        "name": "Developer Productivity Tools",
        "description": (
            "MCP servers providing database access, file operations, and "
            "code analysis tools for a development agent. Focus on local "
            "development workflow optimization."
        ),
        "components": {
            "agent_type": "Claude Code with MCP servers for extended capabilities",
            "model": "Claude Sonnet for routine tasks, Opus for complex analysis",
            "tools": [
                "MCP: db_query(sql) -> results (via stdio transport)",
                "MCP: run_tests(path) -> test results",
                "MCP: analyze_dependencies(package) -> dependency tree",
                "Built-in: Read, Edit, Write, Grep, Glob, Bash",
            ],
            "hooks": [
                "PreToolUse on db_query: block DROP/DELETE in production",
                "PreToolUse on Bash: sanitize commands",
                "PostToolUse on all: structured error responses",
            ],
        },
        "session_strategy": (
            "Long-running interactive sessions for development. "
            "Scratchpad files for architectural decisions that survive compaction."
        ),
        "escalation_rules": [
            "Database schema changes -> require plan mode review",
            "Production access -> require explicit human approval",
            "Test failures after 3 fix attempts -> flag for human review",
        ],
        "anti_patterns_to_avoid": [5, 6, 7, 9],
    },
    5: {
        "name": "CI/CD Pipeline Integration",
        "description": (
            "Claude Code integrated into CI/CD pipelines for automated code "
            "review, test generation, migration assistance, and deployment "
            "validation. Focus on session isolation and batch processing."
        ),
        "components": {
            "agent_type": "Headless Claude Code sessions in CI runners",
            "model": "Claude Sonnet for reviews, Batch API for bulk operations",
            "tools": [
                "Built-in: Read, Grep, Glob for code analysis",
                "Custom: validate_terraform(config) -> validation results",
                "Custom: check_security(diff) -> security findings",
                "Custom: generate_tests(file) -> test file",
            ],
            "hooks": [
                "PreToolUse on Bash: whitelist safe commands only",
                "PostToolUse on all: structured CI-compatible output",
            ],
        },
        "session_strategy": (
            "ISOLATED sessions per CI job: --session-id=\"pr-${PR_NUMBER}-${RUN_ID}\". "
            "NEVER reuse sessions across PRs. Batch API for bulk operations."
        ),
        "escalation_rules": [
            "Security findings (high severity) -> block merge, alert team",
            "Validation failures after retry loop -> human review required",
            "Ambiguous review findings -> add as PR comments, don't block",
        ],
        "anti_patterns_to_avoid": [3, 12, 13, 14],
    },
    6: {
        "name": "Structured Data Extraction",
        "description": (
            "Extract structured data from legal documents, invoices, and "
            "filings using tool_use for schema-enforced output. Multi-pass "
            "extraction with confidence scoring and provenance tracking."
        ),
        "components": {
            "agent_type": "Extraction pipeline: single agent with tool_use for output",
            "model": "Claude Opus for high-accuracy extraction, Haiku for simple fields",
            "tools": [
                "record_entity(name, type, identifiers) -> structured entity",
                "record_filing(number, type, parties, dates) -> structured filing",
                "record_financial(amounts, dates, terms) -> structured financial data",
                "flag_uncertainty(field, reason, confidence) -> uncertainty marker",
            ],
            "hooks": [
                "PostToolUse on record_*: validate required fields present",
                "PostToolUse on record_*: add provenance (source, confidence, timestamp, agent_id)",
            ],
        },
        "session_strategy": (
            "One session per document for simple extraction. "
            "Multi-pass for complex docs: Pass 1 extracts, Pass 2 cross-validates."
        ),
        "escalation_rules": [
            "Low confidence fields -> flag_uncertainty tool call",
            "Conflicting data within document -> human review",
            "Novel entity types not in schema -> use 'Other' + freetext field",
        ],
        "anti_patterns_to_avoid": [6, 7, 15, 18],
    },
}


def build_architecture(scenario_num: int) -> dict:
    """Return the architecture recommendation for a given scenario."""
    if scenario_num not in SCENARIOS:
        raise ValueError(
            f"Unknown scenario {scenario_num}. Valid: {list(SCENARIOS.keys())}"
        )
    return SCENARIOS[scenario_num]


def display_scenario(scenario: dict) -> str:
    """Display a scenario's architecture recommendation."""
    lines = []
    lines.append(f"  Scenario: {scenario['name']}")
    lines.append(f"  Description: {scenario['description']}")
    lines.append("")

    comp = scenario["components"]
    lines.append("  Components:")
    lines.append(f"    Agent Type: {comp['agent_type']}")
    lines.append(f"    Model: {comp['model']}")
    lines.append("    Tools:")
    for tool in comp["tools"]:
        lines.append(f"      - {tool}")
    lines.append("    Hooks:")
    for hook in comp["hooks"]:
        lines.append(f"      - {hook}")
    lines.append("")

    lines.append(f"  Session Strategy: {scenario['session_strategy']}")
    lines.append("")

    lines.append("  Escalation Rules:")
    for rule in scenario["escalation_rules"]:
        lines.append(f"    - {rule}")
    lines.append("")

    ap_list = ", ".join(f"#{n}" for n in scenario["anti_patterns_to_avoid"])
    lines.append(f"  Anti-Patterns to Avoid: {ap_list}")

    output = "\n".join(lines)
    print(output)
    return output


def run_all() -> str:
    """Display architecture for all 6 scenarios."""
    all_output = []

    header = (
        "=" * 56 + "\n"
        "  Architecture Recommendations: 6 Exam Scenarios\n"
        "=" * 56
    )
    print(header)
    all_output.append(header)

    for num in sorted(SCENARIOS.keys()):
        separator = "\n" + "-" * 56
        print(separator)
        all_output.append(separator)

        scenario = build_architecture(num)
        output = display_scenario(scenario)
        all_output.append(output)

    footer = "\n" + "=" * 56
    print(footer)
    all_output.append(footer)

    return "\n".join(all_output)


if __name__ == "__main__":
    run_all()
