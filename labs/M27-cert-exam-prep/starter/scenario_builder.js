/**
 * M27 Lab — Exercise 2: Scenario Builder
 * =======================================
 * Build an architecture recommendation tool for the 6 exam scenarios.
 * Given a scenario number, output the recommended components, tools,
 * hooks, session strategy, and escalation rules.
 *
 * YOUR TASK: Complete the SCENARIOS object (2 examples given, add 4 more)
 * and implement buildArchitecture() and displayScenario().
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
  // TODO: Add scenarios 3-6
  // 3: Multi-Agent Research System
  // 4: Developer Productivity Tools
  // 5: CI/CD Pipeline Integration
  // 6: Structured Data Extraction
};

/**
 * Return the architecture recommendation for a given scenario.
 *
 * TODO: Implement this function. It should:
 * 1. Look up the scenario by number
 * 2. Return the full architecture object
 * 3. Throw an Error if scenario not found
 */
function buildArchitecture(scenarioNum) {
  // YOUR CODE HERE
}

/**
 * Display a scenario's architecture recommendation with formatting.
 *
 * TODO: Implement this function. It should print:
 * - Scenario name and description
 * - Components (agent type, model, tools, hooks)
 * - Session strategy
 * - Escalation rules
 * - Anti-patterns to avoid
 */
function displayScenario(scenario) {
  // YOUR CODE HERE
}

/**
 * Display architecture for all 6 scenarios.
 *
 * TODO: Implement this function.
 */
function runAll() {
  // YOUR CODE HERE
}

runAll();
