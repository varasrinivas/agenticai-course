/**
 * M27 Lab — Exercise 1 SOLUTION: Anti-Pattern Identification Quiz
 * ================================================================
 * Displays all 18 certification anti-patterns with scenarios,
 * explanations, correct patterns, and domain mappings.
 */

const ANTI_PATTERNS = [
  {
    number: 1,
    name: "Text-parsing for loop termination",
    domain: 1,
    domainName: "Agentic Architecture",
    scenario:
      "The agent loop checks if the model's text contains 'DONE' or " +
      "'Here is your answer' to decide when to stop.",
    whyWrong:
      "Natural language parsing is non-deterministic. The model might " +
      "say 'done' mid-thought or forget the keyword when actually finished.",
    correctPattern:
      "Check stop_reason field: continue on 'tool_use', stop on 'end_turn'. " +
      "This is the ONLY reliable termination signal.",
  },
  {
    number: 2,
    name: "Fixed iteration caps as primary stop",
    domain: 1,
    domainName: "Agentic Architecture",
    scenario:
      "The agent loop always stops after exactly 5 iterations, regardless " +
      "of whether the task is complete.",
    whyWrong:
      "Arbitrary caps prevent the agent from finishing complex tasks and " +
      "waste resources on simple ones. A 1-step task still runs 5 loops.",
    correctPattern:
      "Use stop_reason as the primary signal. Use max_turns as a SAFETY " +
      "NET only — a backstop, not the main mechanism.",
  },
  {
    number: 3,
    name: "Prompt-based enforcement for critical rules",
    domain: 1,
    domainName: "Agentic Architecture",
    scenario:
      "The system prompt says 'NEVER issue refunds over $500 without " +
      "approval' but the agent occasionally does it anyway.",
    whyWrong:
      "Prompts are probabilistic. No matter how strongly worded, the " +
      "model can be persuaded by context to violate the instruction.",
    correctPattern:
      "Implement PreToolUse hooks that programmatically block the tool " +
      "call. Hooks provide 100% deterministic enforcement.",
  },
  {
    number: 4,
    name: "Sentiment-based escalation",
    domain: 1,
    domainName: "Agentic Architecture",
    scenario:
      "The agent escalates to a human whenever the customer uses profanity " +
      "or has a negative sentiment score above 0.8.",
    whyWrong:
      "Angry customers with simple requests (password resets, status checks) " +
      "waste human agent time. Sentiment does not correlate with task complexity.",
    correctPattern:
      "Escalate based on capability limits: policy gaps, authority limits, " +
      "explicit user request, or business thresholds. Never on sentiment alone.",
  },
  {
    number: 5,
    name: "Missing input validation on tools",
    domain: 2,
    domainName: "Tool Design & MCP",
    scenario:
      "The lookup_filing tool accepts any string as a filing ID without " +
      "checking format. The model passes 'show me all filings' as the ID.",
    whyWrong:
      "Without input validation, natural language bleeds into tool parameters. " +
      "The tool executes an invalid query and returns confusing results.",
    correctPattern:
      'Validate inputs against expected patterns (e.g., regex for filing IDs). ' +
      'Return specific errors: {"error": "Invalid filing ID format. Expected: ' +
      'UCC-YYYY-ST-NNNNNNN", "isError": true}.',
  },
  {
    number: 6,
    name: "Generic error messages",
    domain: 2,
    domainName: "Tool Design & MCP",
    scenario:
      'Every tool error returns: {"error": "Something went wrong", ' +
      '"isError": true}. The agent retries permission errors and gives up ' +
      "on transient network errors.",
    whyWrong:
      "Generic errors prevent the model from making intelligent retry decisions. " +
      "It cannot distinguish retryable from non-retryable failures.",
    correctPattern:
      "Return structured errors with errorCategory, isRetryable, and " +
      'retrySuggestion fields. Example: {"error": "DB timeout after 30s", ' +
      '"errorCategory": "connection", "isRetryable": true}.',
  },
  {
    number: 7,
    name: "Empty results without context",
    domain: 2,
    domainName: "Tool Design & MCP",
    scenario:
      'The search tool returns {"results": []} for both \'no matches found\' ' +
      "and 'access denied' cases.",
    whyWrong:
      "The model cannot distinguish between 'searched successfully, found nothing' " +
      "and 'could not execute the search'. It may tell users no results exist " +
      "when the search simply failed.",
    correctPattern:
      'Include access_verified and query echo: {"results": [], "count": 0, ' +
      '"access_verified": true, "query": "..."}. For access failures: ' +
      '{"results": [], "access_verified": false, "reason": "auth expired"}.',
  },
  {
    number: 8,
    name: "Too many tools on one agent",
    domain: 2,
    domainName: "Tool Design & MCP",
    scenario:
      "A coordinator agent has 22 tools. It frequently selects the wrong " +
      "tool, confusing search_by_name with search_by_id.",
    whyWrong:
      "Model accuracy degrades significantly beyond 8-10 tools. The model " +
      "struggles to distinguish between similar tools in a large set.",
    correctPattern:
      "Keep coordinators at 4-5 high-level tools. Distribute specialized " +
      "tools to subagents via the Task tool pattern.",
  },
  {
    number: 9,
    name: "Hardcoded secrets in config files",
    domain: 2,
    domainName: "Tool Design & MCP",
    scenario:
      '.mcp.json contains: {"env": {"DB_PASSWORD": "prod_secret_123"}}. ' +
      "The file is committed to the repository.",
    whyWrong:
      "Config files are often committed to version control. Hardcoded secrets " +
      "are exposed to anyone with repo access and persist in git history.",
    correctPattern:
      "Use environment variable references: ${DB_PASSWORD}. Store actual " +
      "secrets in .env (gitignored), CI secrets, or a secrets manager.",
  },
  {
    number: 10,
    name: "Personal preferences in project CLAUDE.md",
    domain: 3,
    domainName: "Claude Code Configuration",
    scenario:
      "A developer adds 'Use vim keybindings' and 'Sign commits with my " +
      "GPG key ABC123' to the shared project CLAUDE.md.",
    whyWrong:
      "Project CLAUDE.md is shared by the team. Personal preferences imposed " +
      "on everyone cause conflicts and confusion.",
    correctPattern:
      "Personal preferences go in ~/.claude/CLAUDE.md (user-level, not committed). " +
      "Project CLAUDE.md is for team-wide conventions only.",
  },
  {
    number: 11,
    name: "Skipping plan mode for complex changes",
    domain: 3,
    domainName: "Claude Code Configuration",
    scenario:
      "A developer lets Claude directly execute a large architectural " +
      "refactor across 20 files without reviewing a plan first.",
    whyWrong:
      "Without plan review, Claude may choose a technically valid but " +
      "architecturally wrong approach. Rework cost is high for large changes.",
    correctPattern:
      "Use plan mode for complex/risky changes: architectural decisions, " +
      "large refactors, unfamiliar code areas. Skip only for trivial changes.",
  },
  {
    number: 12,
    name: "Shared sessions in CI/CD",
    domain: 3,
    domainName: "Claude Code Configuration",
    scenario:
      "All CI review jobs share one long-running Claude session to 'save " +
      "context'. Reviews reference code from other pull requests.",
    whyWrong:
      "Session bleed: context from PR #1 leaks into the review of PR #2, " +
      "causing cross-contamination of review feedback.",
    correctPattern:
      "Use isolated sessions: --session-id per PR or per CI job. Each " +
      "review starts with a clean context.",
  },
  {
    number: 13,
    name: "Vague instructions",
    domain: 4,
    domainName: "Prompt Engineering & Structured Output",
    scenario:
      "Code review prompt: 'Review this code and make it better.' " +
      "Reviews are inconsistent — sometimes formatting, sometimes logic.",
    whyWrong:
      "'Make it better' gives no criteria for what 'better' means. The model " +
      "picks a random focus area each time.",
    correctPattern:
      "Specify exact criteria: 'Check for: (1) null pointer risks, " +
      "(2) SQL injection, (3) missing error handling, (4) functions > 50 lines. " +
      "Rate each: pass/warn/fail with line numbers.'",
  },
  {
    number: 14,
    name: "Session bleed in CI/CD pipelines",
    domain: 3,
    domainName: "Claude Code Configuration",
    scenario:
      "A CI pipeline reuses the same session across multiple PRs. Claude " +
      "references variable names from a previous PR's code in its review.",
    whyWrong:
      "Without session isolation, the model's context accumulates state " +
      "from prior jobs, leading to incorrect or misleading feedback.",
    correctPattern:
      'Assign unique session IDs per CI job: --session-id="pr-${PR_NUMBER}-${RUN_ID}". ' +
      "Never reuse sessions across independent tasks.",
  },
  {
    number: 15,
    name: "No structured output schema",
    domain: 4,
    domainName: "Prompt Engineering & Structured Output",
    scenario:
      "Extraction prompt: 'Return the data as JSON.' The model wraps JSON " +
      "in markdown fences, adds commentary, or produces invalid JSON.",
    whyWrong:
      "Asking for JSON in text is unreliable. The model may include extra text, " +
      "markdown formatting, or structural errors that break parsers.",
    correctPattern:
      "Define a tool with a strict JSON schema and use tool_use to force " +
      "structured output. The model's tool call always matches the schema.",
  },
  {
    number: 16,
    name: "Progressive summarization of critical details",
    domain: 5,
    domainName: "Context & Reliability",
    scenario:
      "After /compact, the original query's specific filing numbers and " +
      "date ranges are summarized to 'various filings in 2024'.",
    whyWrong:
      "/compact is lossy. Critical details like specific IDs, amounts, " +
      "dates, and thresholds may be generalized beyond usefulness.",
    correctPattern:
      "Write critical facts to a scratchpad file BEFORE compacting. " +
      "Scratchpad files persist on disk and survive context compression.",
  },
  {
    number: 17,
    name: "Aggregate-only accuracy metrics",
    domain: 5,
    domainName: "Context & Reliability",
    scenario:
      "The system reports 94% overall accuracy, but UCC-1 filings are at " +
      "98% while UCC-3 amendments are at 71%.",
    whyWrong:
      "Aggregate metrics hide per-category failures. If most queries are " +
      "easy (UCC-1), the overall number is misleading.",
    correctPattern:
      "Always use stratified metrics: per-document-type, per-domain, " +
      "per-difficulty. Act on the weakest category, not the aggregate.",
  },
  {
    number: 18,
    name: "Missing provenance fields",
    domain: 5,
    domainName: "Context & Reliability",
    scenario:
      "The report states 'The debtor has no active liens' without indicating " +
      "which documents were checked or how confident the finding is.",
    whyWrong:
      "Without provenance, findings cannot be audited, verified, or " +
      "trusted. Users have no way to assess reliability.",
    correctPattern:
      "Every finding must include 4 provenance fields: source (which docs), " +
      "confidence (high/medium/low + reasoning), timestamp, and agent_id.",
  },
];

function displayAntiPattern(ap) {
  const lines = [
    `  Anti-Pattern #${ap.number}: ${ap.name}`,
    `  Domain: ${ap.domain} — ${ap.domainName}`,
    "",
    "  Scenario:",
    `    ${ap.scenario}`,
    "",
    "  Why It's Wrong:",
    `    ${ap.whyWrong}`,
    "",
    "  Correct Pattern:",
    `    ${ap.correctPattern}`,
  ];

  const output = lines.join("\n");
  console.log(output);
  return output;
}

function runQuiz() {
  const allOutput = [];

  const header =
    "=".repeat(56) +
    "\n" +
    "  18 Anti-Patterns for the Claude Certified Architect\n" +
    "=".repeat(56);
  console.log(header);
  allOutput.push(header);

  const domainCounts = {};

  for (const ap of ANTI_PATTERNS) {
    const separator = "\n" + "-".repeat(56);
    console.log(separator);
    allOutput.push(separator);

    const output = displayAntiPattern(ap);
    allOutput.push(output);

    if (!domainCounts[ap.domain]) {
      domainCounts[ap.domain] = { name: ap.domainName, count: 0 };
    }
    domainCounts[ap.domain].count++;
  }

  const summaryLines = [
    "\n" + "=".repeat(56),
    "  Summary: Anti-Patterns by Domain",
    "=".repeat(56),
  ];

  for (const domainNum of Object.keys(domainCounts).sort()) {
    const info = domainCounts[domainNum];
    summaryLines.push(
      `  Domain ${domainNum} (${info.name}): ${info.count} anti-patterns`
    );
  }

  summaryLines.push(
    `\n  Total: ${ANTI_PATTERNS.length} anti-patterns across ` +
      `${Object.keys(domainCounts).length} domains`
  );

  const summary = summaryLines.join("\n");
  console.log(summary);
  allOutput.push(summary);

  return allOutput.join("\n");
}

runQuiz();
