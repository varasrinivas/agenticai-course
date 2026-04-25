/**
 * M26 Lab — Step 5: Full Customer Support Agent (Node.js)
 *
 * Composes all previous steps into a production-grade UCC filing
 * customer support agent with hooks, sessions, and subagent delegation.
 *
 * Usage:
 *     node support_agent.js
 */

// --- Mock tools ---

const MOCK_TOOLS = {
  lookup_filing: (params) => ({
    filing_number: params.filing_number || "UCC-2024-NY-0012847",
    status: "Active",
    debtor: "Greenfield Logistics LLC",
    secured_party: "Atlantic Capital Partners",
    filing_date: "2024-03-15",
    expiration_date: "2029-03-15",
    collateral: "All accounts receivable, inventory, equipment",
  }),
  check_risk_profile: (params) => ({
    entity: params.entity_name || "Greenfield Logistics LLC",
    risk_score: 0.35,
    risk_level: "LOW",
    factors: ["No prior defaults", "Active 5+ years", "Single active lien"],
  }),
  issue_refund: (params) => ({
    refund_id: "REF-2024-0042",
    amount: params.amount || 150,
    status: (params.amount || 150) <= 500 ? "processed" : "blocked",
  }),
  escalate_to_human: (params) => ({
    ticket_id: "ESC-2024-0891",
    priority: params.priority || "medium",
    reason: params.reason || "Policy gap",
    assigned_to: "support-team-lead",
    eta_minutes: 15,
  }),
  resolve_entity: (params) => ({
    canonical_name: params.entity_name || "",
    related_entities: ["Greenfield Logistics West LLC"],
    states: ["NY", "CA"],
    confidence: 0.95,
  }),
};

// --- Hook Engine ---

class HookEngine {
  constructor() {
    this.preHooks = [];
    this.postHooks = [];
    this.auditTrail = [];
    this.blockedCount = 0;
  }

  registerPreHook(matcher, handler, description = "") {
    this.preHooks.push({ matcher, handler, description });
  }

  registerPostHook(matcher, handler, description = "") {
    this.postHooks.push({ matcher, handler, description });
  }

  executeWithHooks(toolName, toolInput, toolExecutor) {
    for (const hook of this.preHooks) {
      if (hook.matcher === "*" || hook.matcher === toolName) {
        const result = hook.handler(toolName, toolInput);
        if (!result.allowed) {
          this.blockedCount++;
          this.auditTrail.push({
            timestamp: new Date().toISOString(),
            phase: "PreToolUse",
            tool: toolName,
            action: "BLOCKED",
            reason: result.reason,
          });
          return { blocked: true, reason: result.reason };
        }
      }
    }

    const toolResult = toolExecutor(toolName, toolInput);

    for (const hook of this.postHooks) {
      if (hook.matcher === "*" || hook.matcher === toolName) {
        hook.handler(toolName, toolInput, toolResult);
        this.auditTrail.push({
          timestamp: new Date().toISOString(),
          phase: "PostToolUse",
          tool: toolName,
          action: "LOGGED",
        });
      }
    }

    return toolResult;
  }
}

// --- Session Manager ---

class SessionManager {
  constructor() {
    this.sessions = new Map();
  }

  createSession(name, systemPrompt = "") {
    const session = {
      name,
      systemPrompt,
      messages: [],
      tokenCount: 0,
      createdAt: new Date().toISOString(),
    };
    this.sessions.set(name, session);
    return session;
  }

  addMessage(sessionName, role, content) {
    const session = this.sessions.get(sessionName);
    if (session) {
      session.messages.push({ role, content, timestamp: new Date().toISOString() });
      session.tokenCount += Math.floor(content.length / 4);
    }
  }

  forkSession(sourceName, forkName) {
    const source = this.sessions.get(sourceName);
    if (source) {
      const forked = structuredClone(source);
      forked.name = forkName;
      forked.parent = sourceName;
      this.sessions.set(forkName, forked);
      return forked;
    }
    return null;
  }

  getSession(name) {
    return this.sessions.get(name);
  }
}

// --- SubAgent Coordinator ---

class SubAgentCoordinator {
  delegateEntityResearch(entityName) {
    console.log(`      [Coordinator] Decomposing entity research for: ${entityName}`);

    const entityResult = MOCK_TOOLS.resolve_entity({ entity_name: entityName });
    console.log(`      [EntityAgent] Resolved: ${entityResult.canonical_name} -> ${entityResult.related_entities}`);

    const allFilings = [];
    const allEntities = [entityName, ...entityResult.related_entities];
    for (const ent of allEntities) {
      const filing = MOCK_TOOLS.lookup_filing({ filing_number: `search:${ent}` });
      allFilings.push({ entity: ent, filing });
      console.log(`      [FilingAgent] Found filing for ${ent}: ${filing.status}`);
    }

    const riskProfiles = [];
    for (const ent of allEntities) {
      const risk = MOCK_TOOLS.check_risk_profile({ entity_name: ent });
      riskProfiles.push({ entity: ent, risk });
      console.log(`      [RiskAgent] ${ent}: ${risk.risk_level} (${risk.risk_score})`);
    }

    const avgRisk = riskProfiles.reduce((s, r) => s + r.risk.risk_score, 0) / riskProfiles.length;

    return {
      entities: allEntities,
      states: entityResult.states,
      filings: allFilings,
      risk_profiles: riskProfiles,
      aggregate_risk: Math.round(avgRisk * 1000) / 1000,
      aggregate_level: avgRisk < 0.4 ? "LOW" : avgRisk < 0.7 ? "MEDIUM" : "HIGH",
    };
  }
}

// --- Support Agent ---

class SupportAgent {
  constructor() {
    this.hooks = new HookEngine();
    this.sessions = new SessionManager();
    this.coordinator = new SubAgentCoordinator();
    this.requestCount = 0;

    this.hooks.registerPreHook("issue_refund", (toolName, toolInput) => {
      if (toolName !== "issue_refund") return { allowed: true };
      const amount = toolInput.amount || 0;
      if (amount > 500) {
        return {
          allowed: false,
          reason: `Refund $${amount.toFixed(2)} exceeds $500 limit. Requires human approval.`,
        };
      }
      return { allowed: true };
    }, "Block refunds > $500");

    this.hooks.registerPostHook("*", () => {}, "Audit trail");

    console.log("  [SupportAgent] Initialized with hooks, sessions, and subagent coordinator");
  }

  _executeTool(toolName, toolInput) {
    const handler = MOCK_TOOLS[toolName];
    return handler ? handler(toolInput) : { error: `Unknown tool: ${toolName}` };
  }

  handleRequest(requestText, customerId = "CUST-001") {
    this.requestCount++;
    const sessionName = `session-${customerId}-${this.requestCount}`;

    console.log(`\n  --- Request #${this.requestCount} ---`);
    console.log(`  Customer: ${customerId}`);
    console.log(`  Request: ${requestText}`);
    console.log(`  Session: ${sessionName}`);

    this.sessions.createSession(sessionName, "You are a UCC filing support agent.");
    this.sessions.addMessage(sessionName, "user", requestText);

    const requestType = this._classifyRequest(requestText);
    console.log(`  Classified as: ${requestType}`);

    const executor = (name, input) => this._executeTool(name, input);

    if (requestType === "filing_lookup") {
      return this._handleFilingLookup(sessionName, executor);
    } else if (requestType === "refund") {
      return this._handleRefund(sessionName, requestText, executor);
    } else if (requestType === "entity_research") {
      return this._handleEntityResearch(sessionName, requestText);
    }
    return this._handleGeneral(sessionName);
  }

  _classifyRequest(text) {
    const lower = text.toLowerCase();
    if (lower.includes("refund")) return "refund";
    if ((lower.includes("look up") || lower.includes("filing")) && !lower.includes("research")) return "filing_lookup";
    if (lower.includes("research") || lower.includes("cross-state") || lower.includes("entity")) return "entity_research";
    return "general";
  }

  _handleFilingLookup(sessionName, executor) {
    console.log(`\n  [AgentLoop] Starting filing lookup (max 3 turns)`);

    const result = this.hooks.executeWithHooks("lookup_filing", { filing_number: "UCC-2024-NY-0012847" }, executor);
    console.log(`    Turn 1: lookup_filing -> ${result.status}`);

    const risk = this.hooks.executeWithHooks("check_risk_profile", { entity_name: result.debtor || "Unknown" }, executor);
    console.log(`    Turn 2: check_risk_profile -> ${risk.risk_level || "N/A"}`);

    const response = [
      `Filing ${result.filing_number} is ${result.status}.`,
      `Debtor: ${result.debtor || "N/A"}`,
      `Risk: ${risk.risk_level || "N/A"} (score: ${risk.risk_score || "N/A"})`,
      `Expires: ${result.expiration_date || "N/A"}`,
    ].join("\n");

    this.sessions.addMessage(sessionName, "assistant", response);
    console.log(`    Turn 3: end_turn -> response delivered`);
    console.log(`\n  Response: ${response}`);
    return { status: "completed", response };
  }

  _handleRefund(sessionName, requestText, executor) {
    const amount = requestText.includes("750") ? 750.0 : 150.0;
    console.log(`\n  [AgentLoop] Processing refund of $${amount.toFixed(2)}`);

    const result = this.hooks.executeWithHooks("issue_refund", { amount, reason: "Customer request" }, executor);

    if (result.blocked) {
      console.log(`    Refund BLOCKED: ${result.reason}`);

      const escalation = this.hooks.executeWithHooks(
        "escalate_to_human",
        {
          priority: "high",
          reason: `Refund of $${amount.toFixed(2)} exceeds automated limit`,
          context: "Customer requested refund. Amount exceeds $500 hook limit.",
        },
        executor
      );

      const response = [
        `I apologize, but I cannot process a refund of $${amount.toFixed(2)} automatically.`,
        "Refunds over $500 require human approval.",
        `I have escalated your request (ticket: ${escalation.ticket_id || "N/A"}).`,
        `Expected response time: ${escalation.eta_minutes || "N/A"} minutes.`,
      ].join("\n");

      this.sessions.addMessage(sessionName, "assistant", response);
      console.log(`\n  Response: ${response}`);
      return { status: "escalated", response, ticket_id: escalation.ticket_id };
    }

    const response = `Refund of $${amount.toFixed(2)} has been processed.\nRefund ID: ${result.refund_id || "N/A"}`;
    this.sessions.addMessage(sessionName, "assistant", response);
    console.log(`\n  Response: ${response}`);
    return { status: "completed", response };
  }

  _handleEntityResearch(sessionName, requestText) {
    const entityName = "Greenfield Logistics LLC";
    console.log(`\n  [AgentLoop] Delegating to subagent coordinator`);
    console.log(`    Entity: ${entityName}`);

    const forkName = `${sessionName}-research-fork`;
    this.sessions.forkSession(sessionName, forkName);
    console.log(`    Forked session: ${forkName}`);

    const research = this.coordinator.delegateEntityResearch(entityName);

    const lines = [
      `Cross-state research complete for ${entityName}:`,
      `- Entities found: ${research.entities.length} (${research.entities.join(", ")})`,
      `- States covered: ${research.states.join(", ")}`,
      `- Total filings: ${research.filings.length}`,
      `- Aggregate risk: ${research.aggregate_level} (score: ${research.aggregate_risk})`,
    ];
    for (const rp of research.risk_profiles) {
      lines.push(`  - ${rp.entity}: ${rp.risk.risk_level} (${rp.risk.risk_score})`);
    }
    const response = lines.join("\n");

    this.sessions.addMessage(sessionName, "assistant", response);
    console.log(`\n  Response:\n${response}`);
    return { status: "completed", response };
  }

  _handleGeneral(sessionName) {
    const response = "I can help with filing lookups, refund requests, and entity research. How can I assist you?";
    this.sessions.addMessage(sessionName, "assistant", response);
    console.log(`\n  Response: ${response}`);
    return { status: "completed", response };
  }
}

// --- Main ---

function main() {
  console.log("=".repeat(60));
  console.log("M26 Lab — Full Customer Support Agent");
  console.log("=".repeat(60));

  const agent = new SupportAgent();

  // Scenario 1
  console.log(`\n${"=".repeat(60)}`);
  console.log("SCENARIO 1: Simple Filing Lookup");
  console.log("=".repeat(60));
  const r1 = agent.handleRequest("Look up filing UCC-2024-NY-0012847 and check for risk flags.", "CUST-100");
  console.log(`\n  Status: ${r1.status}`);

  // Scenario 2
  console.log(`\n${"=".repeat(60)}`);
  console.log("SCENARIO 2: Refund Request Over $500");
  console.log("=".repeat(60));
  const r2 = agent.handleRequest("I need a refund of $750 for duplicate filing charges.", "CUST-200");
  console.log(`\n  Status: ${r2.status}`);
  if (r2.ticket_id) console.log(`  Escalation ticket: ${r2.ticket_id}`);

  // Scenario 3
  console.log(`\n${"=".repeat(60)}`);
  console.log("SCENARIO 3: Cross-State Entity Research");
  console.log("=".repeat(60));
  const r3 = agent.handleRequest("Research Greenfield Logistics LLC across all states. Find related entities and aggregate risk.", "CUST-300");
  console.log(`\n  Status: ${r3.status}`);

  // Summary
  console.log(`\n${"=".repeat(60)}`);
  console.log("Agent Execution Summary");
  console.log("=".repeat(60));
  console.log(`  Total requests handled: ${agent.requestCount}`);
  console.log(`  Hook audit trail entries: ${agent.hooks.auditTrail.length}`);
  console.log(`  Hooks blocked: ${agent.hooks.blockedCount}`);
  console.log(`  Sessions created: ${agent.sessions.sessions.size}`);

  console.log(`\n  Audit trail:`);
  for (const entry of agent.hooks.auditTrail) {
    console.log(`    [${entry.phase}] ${entry.tool} -> ${entry.action}`);
  }

  console.log(`\n  Sessions:`);
  for (const [name, session] of agent.sessions.sessions) {
    const parentLabel = session.parent ? ` [forked from ${session.parent}]` : "";
    console.log(`    ${name}${parentLabel}: ${session.messages.length} messages`);
  }

  console.log(`\n${"=".repeat(60)}`);
  console.log("Key Takeaways — Composition");
  console.log("=".repeat(60));
  console.log(`
    1. Agent loop: stop_reason drives the control flow (not text parsing)
    2. Hooks: Refund blocked DETERMINISTICALLY by PreToolUse hook (not prompt)
    3. Sessions: Each request gets its own session; research gets a fork
    4. Subagents: Complex research delegated to specialized subagents
    5. Escalation: Triggered by POLICY GAPS ($750 > $500), not customer sentiment
  `);

  console.log("[OK] Lab Step 5 complete — Full customer support agent\n");
}

main();
