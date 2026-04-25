/**
 * M27 Lab — Exercise 2 SOLUTION: Scenario Builder
 * =================================================
 * Architecture recommendation tool for all 6 exam scenarios.
 */

const SCENARIOS = {
  1: {
    name: "Customer Support Agent",
    description:
      "An AI agent handling customer inquiries for a UCC filing service. " +
      "Handles lookups, risk checks, password resets, and refund requests.",
    components: {
      agentType: "Single ReAct agent with tool loop",
      model: "Claude Sonnet for speed, Opus for complex cases",
      tools: [
        "lookup_filing(filing_id) -> filing details",
        "check_risk_profile(entity_name) -> risk score",
        "issue_refund(amount, reason) -> confirmation",
        "reset_password(user_id) -> temp password",
        "escalate_to_human(reason, context) -> ticket_id",
      ],
      hooks: [
        "PreToolUse on issue_refund: block if amount > $500",
        "PostToolUse on all tools: log tool calls for audit",
      ],
    },
    sessionStrategy: "Single session per customer conversation",
    escalationRules: [
      "Policy gap — agent lacks authority",
      "Explicit customer request for human",
      "Refund > $500 (blocked by hook, needs human approval)",
      "NOT triggered by: sentiment, profanity, repeated questions",
    ],
    antiPatternsToAvoid: [1, 2, 3, 4],
  },
  2: {
    name: "Claude Code Configuration",
    description:
      "Setting up Claude Code for a development team with project " +
      "conventions, personal preferences, and CI/CD integration.",
    components: {
      agentType: "Claude Code with custom commands and skills",
      model: "Claude Sonnet for daily coding, Opus for architecture",
      tools: [
        "Read, Edit, Write for file operations",
        "Grep for content search",
        "Glob for file pattern matching",
        "Bash for shell commands",
      ],
      hooks: [
        "PreToolUse on Bash: block destructive commands in CI",
        "PostToolUse on Write: validate file format",
      ],
    },
    sessionStrategy:
      "Isolated sessions per CI job (--session-id per PR). " +
      "Long-running sessions for interactive development.",
    escalationRules: [
      "Complex architectural decisions -> plan mode",
      "Conflicting CLAUDE.md rules -> human resolution",
      "CI failures after 3 retries -> alert team",
    ],
    antiPatternsToAvoid: [10, 11, 12, 14],
  },
  3: {
    name: "Multi-Agent Research System",
    description:
      "A coordinator agent delegates research tasks to specialist " +
      "subagents for UCC filing analysis, entity resolution, and risk " +
      "scoring. Results are synthesized with source attribution.",
    components: {
      agentType: "Multi-agent: coordinator + 3 specialist subagents",
      model: "Coordinator: Opus (complex reasoning), Subagents: Sonnet (speed)",
      tools: [
        "Coordinator: delegate_research, delegate_entity_resolution, delegate_risk_scoring, aggregate_results",
        "Research subagent: search_state_db, search_federal_db, search_vendor_api",
        "Entity subagent: resolve_entity, match_aliases, verify_identity",
        "Risk subagent: calculate_risk_score, check_lien_history, assess_collateral",
      ],
      hooks: [
        "PreToolUse on all tools: validate inputs, check rate limits",
        "PostToolUse on search tools: add provenance metadata",
        "PostToolUse on aggregate_results: classify findings (Well-established/Contested/Single-source)",
      ],
    },
    sessionStrategy:
      "Coordinator: long-running session with scratchpad for state. " +
      "Subagents: short-lived sessions, one per delegation.",
    escalationRules: [
      "Contested findings (sources disagree) -> flag for human review",
      "Low confidence results -> request additional data sources",
      "Context window > 80% -> write to scratchpad and compact",
    ],
    antiPatternsToAvoid: [8, 16, 17, 18],
  },
  4: {
    name: "Developer Productivity Tools",
    description:
      "MCP servers providing database access, file operations, and " +
      "code analysis tools for a development agent. Focus on local " +
      "development workflow optimization.",
    components: {
      agentType: "Claude Code with MCP servers for extended capabilities",
      model: "Claude Sonnet for routine tasks, Opus for complex analysis",
      tools: [
        "MCP: db_query(sql) -> results (via stdio transport)",
        "MCP: run_tests(path) -> test results",
        "MCP: analyze_dependencies(package) -> dependency tree",
        "Built-in: Read, Edit, Write, Grep, Glob, Bash",
      ],
      hooks: [
        "PreToolUse on db_query: block DROP/DELETE in production",
        "PreToolUse on Bash: sanitize commands",
        "PostToolUse on all: structured error responses",
      ],
    },
    sessionStrategy:
      "Long-running interactive sessions for development. " +
      "Scratchpad files for architectural decisions that survive compaction.",
    escalationRules: [
      "Database schema changes -> require plan mode review",
      "Production access -> require explicit human approval",
      "Test failures after 3 fix attempts -> flag for human review",
    ],
    antiPatternsToAvoid: [5, 6, 7, 9],
  },
  5: {
    name: "CI/CD Pipeline Integration",
    description:
      "Claude Code integrated into CI/CD pipelines for automated code " +
      "review, test generation, migration assistance, and deployment " +
      "validation. Focus on session isolation and batch processing.",
    components: {
      agentType: "Headless Claude Code sessions in CI runners",
      model: "Claude Sonnet for reviews, Batch API for bulk operations",
      tools: [
        "Built-in: Read, Grep, Glob for code analysis",
        "Custom: validate_terraform(config) -> validation results",
        "Custom: check_security(diff) -> security findings",
        "Custom: generate_tests(file) -> test file",
      ],
      hooks: [
        "PreToolUse on Bash: whitelist safe commands only",
        "PostToolUse on all: structured CI-compatible output",
      ],
    },
    sessionStrategy:
      'ISOLATED sessions per CI job: --session-id="pr-${PR_NUMBER}-${RUN_ID}". ' +
      "NEVER reuse sessions across PRs. Batch API for bulk operations.",
    escalationRules: [
      "Security findings (high severity) -> block merge, alert team",
      "Validation failures after retry loop -> human review required",
      "Ambiguous review findings -> add as PR comments, don't block",
    ],
    antiPatternsToAvoid: [3, 12, 13, 14],
  },
  6: {
    name: "Structured Data Extraction",
    description:
      "Extract structured data from legal documents, invoices, and " +
      "filings using tool_use for schema-enforced output. Multi-pass " +
      "extraction with confidence scoring and provenance tracking.",
    components: {
      agentType:
        "Extraction pipeline: single agent with tool_use for output",
      model: "Claude Opus for high-accuracy extraction, Haiku for simple fields",
      tools: [
        "record_entity(name, type, identifiers) -> structured entity",
        "record_filing(number, type, parties, dates) -> structured filing",
        "record_financial(amounts, dates, terms) -> structured financial data",
        "flag_uncertainty(field, reason, confidence) -> uncertainty marker",
      ],
      hooks: [
        "PostToolUse on record_*: validate required fields present",
        "PostToolUse on record_*: add provenance (source, confidence, timestamp, agent_id)",
      ],
    },
    sessionStrategy:
      "One session per document for simple extraction. " +
      "Multi-pass for complex docs: Pass 1 extracts, Pass 2 cross-validates.",
    escalationRules: [
      "Low confidence fields -> flag_uncertainty tool call",
      "Conflicting data within document -> human review",
      "Novel entity types not in schema -> use 'Other' + freetext field",
    ],
    antiPatternsToAvoid: [6, 7, 15, 18],
  },
};

function buildArchitecture(scenarioNum) {
  if (!SCENARIOS[scenarioNum]) {
    throw new Error(
      `Unknown scenario ${scenarioNum}. Valid: ${Object.keys(SCENARIOS).join(", ")}`
    );
  }
  return SCENARIOS[scenarioNum];
}

function displayScenario(scenario) {
  const lines = [];
  lines.push(`  Scenario: ${scenario.name}`);
  lines.push(`  Description: ${scenario.description}`);
  lines.push("");

  const comp = scenario.components;
  lines.push("  Components:");
  lines.push(`    Agent Type: ${comp.agentType}`);
  lines.push(`    Model: ${comp.model}`);
  lines.push("    Tools:");
  for (const tool of comp.tools) {
    lines.push(`      - ${tool}`);
  }
  lines.push("    Hooks:");
  for (const hook of comp.hooks) {
    lines.push(`      - ${hook}`);
  }
  lines.push("");

  lines.push(`  Session Strategy: ${scenario.sessionStrategy}`);
  lines.push("");

  lines.push("  Escalation Rules:");
  for (const rule of scenario.escalationRules) {
    lines.push(`    - ${rule}`);
  }
  lines.push("");

  const apList = scenario.antiPatternsToAvoid.map((n) => `#${n}`).join(", ");
  lines.push(`  Anti-Patterns to Avoid: ${apList}`);

  const output = lines.join("\n");
  console.log(output);
  return output;
}

function runAll() {
  const allOutput = [];

  const header =
    "=".repeat(56) +
    "\n" +
    "  Architecture Recommendations: 6 Exam Scenarios\n" +
    "=".repeat(56);
  console.log(header);
  allOutput.push(header);

  for (const num of Object.keys(SCENARIOS)
    .map(Number)
    .sort((a, b) => a - b)) {
    const separator = "\n" + "-".repeat(56);
    console.log(separator);
    allOutput.push(separator);

    const scenario = buildArchitecture(num);
    const output = displayScenario(scenario);
    allOutput.push(output);
  }

  const footer = "\n" + "=".repeat(56);
  console.log(footer);
  allOutput.push(footer);

  return allOutput.join("\n");
}

runAll();
