/**
 * M26 Lab — Step 1: Agent SDK Agentic Loop (Node.js)
 *
 * Demonstrates the agentic loop pattern used by the Agent SDK.
 * We simulate the SDK's query() function using the Messages API
 * to show exactly what happens under the hood.
 *
 * Usage:
 *     node agent_loop.js
 */

// --- Mock tool execution ---

const TOOL_HANDLERS = {
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
    last_updated: "2024-12-01",
  }),
  issue_refund: (params) => ({
    refund_id: "REF-2024-0042",
    amount: params.amount || 150.0,
    status: (params.amount || 150) <= 500 ? "processed" : "blocked",
    reason:
      (params.amount || 150) <= 500
        ? "Within limit"
        : "Exceeds $500 limit — requires human approval",
  }),
  escalate_to_human: (params) => ({
    ticket_id: "ESC-2024-0891",
    priority: params.priority || "medium",
    reason: params.reason || "Policy gap detected",
    assigned_to: "support-team-lead",
    eta_minutes: 15,
  }),
};

function executeTool(toolName, toolInput) {
  const handler = TOOL_HANDLERS[toolName];
  if (handler) {
    return JSON.stringify(handler(toolInput));
  }
  return JSON.stringify({ error: `Unknown tool: ${toolName}`, isError: true });
}

// --- Tool definitions ---

const TOOLS = [
  {
    name: "lookup_filing",
    description: "Look up a UCC filing by its filing number.",
    input_schema: {
      type: "object",
      properties: {
        filing_number: {
          type: "string",
          description: "Filing number in format UCC-YYYY-ST-NNNNNNN",
        },
      },
      required: ["filing_number"],
    },
  },
  {
    name: "check_risk_profile",
    description: "Check the risk profile for a debtor or secured party entity.",
    input_schema: {
      type: "object",
      properties: {
        entity_name: { type: "string", description: "Name of the entity" },
      },
      required: ["entity_name"],
    },
  },
  {
    name: "issue_refund",
    description:
      "Issue a refund for a filing service fee. Amounts over $500 require human approval.",
    input_schema: {
      type: "object",
      properties: {
        amount: { type: "number", description: "Refund amount in dollars" },
        reason: { type: "string", description: "Reason for the refund" },
      },
      required: ["amount", "reason"],
    },
  },
  {
    name: "escalate_to_human",
    description: "Escalate the current case to a human agent.",
    input_schema: {
      type: "object",
      properties: {
        priority: {
          type: "string",
          enum: ["low", "medium", "high", "critical"],
        },
        reason: { type: "string", description: "Why this needs human review" },
        context: { type: "string", description: "Summary of attempts so far" },
      },
      required: ["priority", "reason"],
    },
  },
];

// --- Simulated Agent SDK ---

class AgentResponse {
  constructor(stopReason, content, toolCalls = []) {
    this.stopReason = stopReason;
    this.content = content;
    this.toolCalls = toolCalls;
  }
}

class SimulatedAgentSDK {
  /**
   * Simulates the Agent SDK's query() function.
   *
   * In the real Agent SDK:
   *     const result = await query({ prompt: "...", tools: TOOLS, maxTurns: 10 });
   *
   * Under the hood, the SDK runs this exact while loop.
   */

  constructor(tools, maxTurns = 10) {
    this.tools = tools;
    this.maxTurns = maxTurns;
    this.turnCount = 0;
    this.messages = [];
    this.auditLog = [];
  }

  query(prompt, system = null) {
    /**
     * The AGENTIC LOOP:
     * 1. Send message to Claude
     * 2. Check stopReason
     * 3. If stopReason == 'tool_use' -> execute tools, continue loop
     * 4. If stopReason == 'end_turn' -> task complete, return
     * 5. If stopReason == 'max_tokens' -> handle gracefully
     * 6. Safety: stop if turnCount >= maxTurns
     */
    this.messages = [{ role: "user", content: prompt }];
    this.turnCount = 0;

    console.log(`\n${"=".repeat(60)}`);
    console.log(`Agent SDK query() started`);
    console.log(`Prompt: ${prompt.slice(0, 80)}...`);
    console.log(`Max turns: ${this.maxTurns}`);
    console.log(`${"=".repeat(60)}\n`);

    while (this.turnCount < this.maxTurns) {
      this.turnCount++;

      // --- Simulate Claude's response ---
      const response = this._simulateClaudeResponse();

      console.log(`--- Turn ${this.turnCount} ---`);
      console.log(`  stop_reason: ${response.stopReason}`);

      // === THE CRITICAL CHECK ===
      // CORRECT: Check stopReason to decide whether to continue.
      // WRONG: Parse the text output to guess if Claude is "done".

      if (response.stopReason === "end_turn") {
        console.log(`  -> Task complete. Final response delivered.`);
        console.log(`  Content: ${response.content.slice(0, 100)}...`);
        this._log("end_turn", "Task completed naturally");
        return response;
      } else if (response.stopReason === "tool_use") {
        for (const toolCall of response.toolCalls) {
          const { name: toolName, input: toolInput } = toolCall;

          console.log(
            `  -> Tool call: ${toolName}(${JSON.stringify(toolInput).slice(0, 60)}...)`
          );

          const result = executeTool(toolName, toolInput);
          console.log(`  <- Result: ${result.slice(0, 80)}...`);

          this._log("tool_use", `${toolName}: ${result.slice(0, 50)}`);

          // Append tool result to conversation
          this.messages.push({
            role: "assistant",
            content: [
              {
                type: "tool_use",
                id: `call_${this.turnCount}`,
                name: toolName,
                input: toolInput,
              },
            ],
          });
          this.messages.push({
            role: "user",
            content: [
              {
                type: "tool_result",
                tool_use_id: `call_${this.turnCount}`,
                content: result,
              },
            ],
          });
        }
      } else if (response.stopReason === "max_tokens") {
        console.log(
          `  -> Max tokens reached. Attempting graceful recovery.`
        );
        this._log("max_tokens", "Token limit hit");
        return response;
      }
    }

    // Safety net: maxTurns exceeded
    console.log(`\n[!] Max turns (${this.maxTurns}) reached — stopping loop.`);
    console.log(`  This is a SAFETY NET, not the primary stop mechanism.`);
    this._log("max_turns_exceeded", `Hit ${this.maxTurns} turn limit`);
    return new AgentResponse("max_turns", "Reached maximum turn limit.", []);
  }

  _simulateClaudeResponse() {
    if (this.turnCount === 1) {
      return new AgentResponse("tool_use", "", [
        {
          name: "lookup_filing",
          input: { filing_number: "UCC-2024-NY-0012847" },
        },
      ]);
    } else if (this.turnCount === 2) {
      return new AgentResponse("tool_use", "", [
        {
          name: "check_risk_profile",
          input: { entity_name: "Greenfield Logistics LLC" },
        },
      ]);
    } else {
      return new AgentResponse(
        "end_turn",
        "Based on my research:\n\n" +
          "**Filing UCC-2024-NY-0012847** is Active.\n" +
          "- Debtor: Greenfield Logistics LLC\n" +
          "- Secured Party: Atlantic Capital Partners\n" +
          "- Risk Level: LOW (score: 0.35)\n" +
          "- Expires: 2029-03-15\n\n" +
          "No issues found. The filing is current and the debtor has a clean risk profile.",
        []
      );
    }
  }

  _log(eventType, detail) {
    this.auditLog.push({
      turn: this.turnCount,
      timestamp: new Date().toISOString(),
      event: eventType,
      detail,
    });
  }

  getAuditLog() {
    return this.auditLog;
  }
}

// --- Main ---

function main() {
  console.log("=".repeat(60));
  console.log("M26 Lab — Agent SDK Agentic Loop Demo");
  console.log("=".repeat(60));

  const agent = new SimulatedAgentSDK(TOOLS, 10);

  const result = agent.query(
    "Look up filing UCC-2024-NY-0012847 and check if the debtor has any risk flags.",
    "You are a UCC filing support agent."
  );

  console.log(`\n${"=".repeat(60)}`);
  console.log("Audit Log:");
  console.log("=".repeat(60));
  for (const entry of agent.getAuditLog()) {
    console.log(`  Turn ${entry.turn}: [${entry.event}] ${entry.detail}`);
  }

  console.log(`\n${"=".repeat(60)}`);
  console.log("[!] ANTI-PATTERN WARNING");
  console.log("=".repeat(60));
  console.log(`
    X WRONG — Parsing text to determine if done:
        if (response.text.includes("I'm done")) break;

    CORRECT — Checking stopReason:
        if (response.stopReason === "end_turn") break;
        else if (response.stopReason === "tool_use") executeTools(response.toolCalls);

    Why? The model's text is non-deterministic. stop_reason is the
    ONLY reliable termination signal.
  `);

  console.log("[OK] Lab Step 1 complete — agent loop with stop_reason handling\n");
}

main();
