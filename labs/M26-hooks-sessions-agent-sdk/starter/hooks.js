/**
 * M26 Lab — Step 2: Pre/Post Tool Use Hooks (Node.js)
 *
 * Hooks provide PROGRAMMATIC enforcement — guaranteed to run,
 * unlike prompt instructions which are probabilistic.
 *
 * YOUR TASK: Fill in the TODO sections to implement hooks.
 *
 * Usage:
 *     node hooks.js
 */

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

  runPreHooks(toolName, toolInput) {
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
            hook: hook.description,
          });
          return { allowed: false, reason: result.reason };
        }
      }
    }
    return { allowed: true, reason: "All pre-hooks passed" };
  }

  runPostHooks(toolName, toolInput, toolOutput) {
    for (const hook of this.postHooks) {
      if (hook.matcher === "*" || hook.matcher === toolName) {
        hook.handler(toolName, toolInput, toolOutput);
        this.auditTrail.push({
          timestamp: new Date().toISOString(),
          phase: "PostToolUse",
          tool: toolName,
          action: "LOGGED",
          hook: hook.description,
        });
      }
    }
  }

  executeWithHooks(toolName, toolInput, toolExecutor) {
    console.log(`\n  [Hook] Tool call: ${toolName}`);
    console.log(`     Input: ${JSON.stringify(toolInput).slice(0, 80)}`);

    // TODO: Implement the full hook lifecycle:
    //
    // Step 1: Run pre-hooks
    //   - Call this.runPreHooks(toolName, toolInput)
    //   - Destructure { allowed, reason } from result
    //   - If not allowed, console.log the block reason, return { blocked: true, reason }
    //   - If allowed, console.log "[OK] PreToolUse hooks passed"
    //
    // Step 2: Execute the tool
    //   - Call toolExecutor(toolName, toolInput)
    //   - console.log the result (first 80 chars of JSON.stringify)
    //
    // Step 3: Run post-hooks
    //   - Call this.runPostHooks(toolName, toolInput, result)
    //   - console.log "[OK] PostToolUse hooks completed"
    //
    // Step 4: Return the result

    // Replace the line below with your implementation
    return { error: "Not implemented" };
  }
}

// --- Hook implementations ---

function refundLimitHook(toolName, toolInput) {
  // TODO: Implement the refund limit check
  //
  // 1. If toolName is not "issue_refund", return { allowed: true }
  // 2. Get the amount from toolInput (default to 0)
  // 3. If amount > 500, return:
  //    { allowed: false, reason: `Refund amount $${amount.toFixed(2)} exceeds $500 limit. Requires human approval.` }
  // 4. Otherwise return { allowed: true }

  // Replace the line below with your implementation
  return { allowed: true };
}

function productionWriteGuard(toolName, toolInput) {
  // TODO: Implement the production write guard
  //
  // 1. If toolName is not "Write", return { allowed: true }
  // 2. Get file_path from toolInput (default to "")
  // 3. If file_path includes "data/production", return:
  //    { allowed: false, reason: `Cannot write to production data path: ${filePath}` }
  // 4. Otherwise return { allowed: true }

  // Replace the line below with your implementation
  return { allowed: true };
}

function auditLogHook(toolName, toolInput, toolOutput) {
  // TODO: Implement the audit log hook
  //
  // 1. Determine status: "blocked" if toolOutput has a "blocked" property, else "success"
  // 2. console.log: `     [Audit] ${toolName} -> ${status}`

  // Replace the line below with your implementation
}

// --- Mock tool executor ---

function mockToolExecutor(toolName, toolInput) {
  const handlers = {
    issue_refund: (inp) => ({
      refund_id: "REF-2024-0042",
      amount: inp.amount || 0,
      status: "processed",
    }),
    lookup_filing: (inp) => ({
      filing_number: inp.filing_number,
      status: "Active",
      debtor: "Greenfield Logistics LLC",
    }),
    escalate_to_human: (inp) => ({
      ticket_id: "ESC-2024-0891",
      priority: inp.priority || "medium",
      status: "created",
    }),
  };
  const handler = handlers[toolName] || ((inp) => ({ error: `Unknown tool: ${toolName}` }));
  return handler(toolInput);
}

// --- Main ---

function main() {
  console.log("=".repeat(60));
  console.log("M26 Lab — Hooks: Programmatic Enforcement");
  console.log("=".repeat(60));

  const engine = new HookEngine();

  engine.registerPreHook("issue_refund", refundLimitHook, "Block refunds > $500");
  engine.registerPreHook("Write", productionWriteGuard, "Block production data writes");
  engine.registerPostHook("*", auditLogHook, "Audit trail logger");

  console.log("\n--- Scenario 1: Small refund (should PASS) ---");
  engine.executeWithHooks(
    "issue_refund",
    { amount: 150.0, reason: "Duplicate filing fee" },
    mockToolExecutor
  );

  console.log("\n--- Scenario 2: Large refund (should BLOCK) ---");
  engine.executeWithHooks(
    "issue_refund",
    { amount: 750.0, reason: "Customer dispute" },
    mockToolExecutor
  );

  console.log("\n--- Scenario 3: Filing lookup (no refund hook, should PASS) ---");
  engine.executeWithHooks(
    "lookup_filing",
    { filing_number: "UCC-2024-NY-0012847" },
    mockToolExecutor
  );

  console.log("\n--- Scenario 4: Write to production (should BLOCK) ---");
  engine.executeWithHooks(
    "Write",
    { file_path: "data/production/filings.db" },
    mockToolExecutor
  );

  // Summary
  console.log(`\n${"=".repeat(60)}`);
  console.log("Hook Execution Summary");
  console.log("=".repeat(60));
  console.log(`  Total hook events: ${engine.auditTrail.length}`);
  console.log(`  Blocked calls: ${engine.blockedCount}`);
  console.log(`  Audit trail entries:`);
  for (const entry of engine.auditTrail) {
    console.log(`    [${entry.phase}] ${entry.tool} -> ${entry.action}`);
  }

  console.log(`\n${"=".repeat(60)}`);
  console.log("Key Takeaway: Hooks vs Prompts");
  console.log("=".repeat(60));
  console.log(`
    Use PROMPTS for:          Use HOOKS for:
    ----------------------    ----------------------
    Style & tone              Spending limits
    Response format           Data access control
    Personality               Compliance rules
    Non-critical guidance     Audit logging
                              PII redaction

    Prompts = suggestions (probabilistic, ~95%)
    Hooks  = rules (deterministic, 100%)
  `);

  console.log("[OK] Lab Step 2 complete — Pre/Post tool use hooks\n");
}

main();
