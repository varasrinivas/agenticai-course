/**
 * M19 Lab — Agent Instrumenter (Starter)
 * =======================================
 * Wrap a UCC research agent with automatic tracing and structured
 * logging. Every API call and tool execution gets its own span.
 *
 * KEY CONCEPT: Instrumentation means adding measurement code around
 * existing operations WITHOUT changing the operations themselves.
 *
 * Usage:
 *     node instrumenter.js
 */

import { Trace, Span, withSpan } from "./trace_model.js";
import { StructuredLogger, scrubPii } from "./structured_logger.js";

// =============================================================================
// MOCK AGENT
// =============================================================================

// WHAT: A fake agent that simulates a real Claude-powered UCC research agent.
// WHY:  Realistic agent to instrument without needing an API key.

class MockUCCAgent {
  constructor() {
    this.model = "claude-sonnet-4-20250514";
    this.callLog = [];
  }

  async run(query) {
    const operations = [];

    // Step 1: First LLM call
    await new Promise((r) => setTimeout(r, 50));
    operations.push({
      type: "llm_call",
      model: this.model,
      inputTokens: 350,
      outputTokens: 85,
      durationMs: 50.0,
      response: {
        stopReason: "tool_use",
        toolName: "search_filings",
        toolInput: { debtor_name: "Greenfield Logistics", state: "New York" },
      },
    });

    // Step 2: Tool execution
    await new Promise((r) => setTimeout(r, 20));
    operations.push({
      type: "tool_call",
      toolName: "search_filings",
      toolInput: { debtor_name: "Greenfield Logistics", state: "New York" },
      toolOutput: {
        results: [
          {
            filing_number: "NY-2024-001234",
            debtor: "Greenfield Logistics LLC",
            secured_party: "First National Bank",
            collateral: "All inventory and equipment",
            filing_date: "2024-03-15",
            status: "active",
          },
          {
            filing_number: "NY-2024-005678",
            debtor: "Greenfield Logistics LLC",
            secured_party: "Atlas Capital Partners",
            collateral: "Accounts receivable",
            filing_date: "2024-07-22",
            status: "active",
          },
        ],
      },
      durationMs: 20.0,
    });

    // Step 3: Second LLM call
    await new Promise((r) => setTimeout(r, 30));
    const answerText =
      "I found 2 active UCC filings for Greenfield Logistics LLC in New York:\n\n" +
      "1. NY-2024-001234 \u2014 Filed 2024-03-15 by First National Bank against all inventory and equipment.\n" +
      "2. NY-2024-005678 \u2014 Filed 2024-07-22 by Atlas Capital Partners against accounts receivable.\n\n" +
      "Both filings are currently active.";

    operations.push({
      type: "llm_call",
      model: this.model,
      inputTokens: 820,
      outputTokens: 210,
      durationMs: 30.0,
      response: { stopReason: "end_turn", text: answerText },
    });

    this.callLog = operations;
    return { answer: answerText, operations };
  }
}

// =============================================================================
// INSTRUMENTED AGENT
// =============================================================================

class InstrumentedAgent {
  /**
   * @param {object} agent - Any object with a .run(query) method
   * @param {StructuredLogger} logger
   */
  constructor(agent, logger) {
    // TODO: Store agent and logger as instance properties
  }

  /**
   * Execute the agent with full tracing.
   * @returns {Promise<[object, Trace]>} [result, trace]
   */
  async run(query) {
    // TODO: Implement instrumented agent execution:
    //
    // 1. Create a new Trace with name "agent_request"
    //    and metadata { query }
    //
    // 2. Use withSpan to create the root span "agent_request":
    //    await withSpan(trace, "agent_request", null, async (root) => { ... })
    //
    // 3. Inside the callback:
    //    a. Set attribute "query" on root
    //    b. Log "Agent request started"
    //    c. const result = await this.agent.run(query)
    //    d. For each operation in result.operations:
    //       - "llm_call" -> await this._instrumentLlmCall(trace, root, op)
    //       - "tool_call" -> await this._instrumentToolCall(trace, root, op)
    //    e. Set attribute "answer_length" on root
    //    f. Log "Agent request completed"
    //    g. Return result
    //
    // 4. Return [result, trace]
  }

  async _instrumentLlmCall(trace, parent, operation) {
    // TODO:
    // 1. Use withSpan to create "llm_call" child span
    // 2. Set attributes: model, inputTokens, outputTokens, totalTokens, stopReason
    // 3. Log with this.logger.logLlmCall()
    // 4. Sleep for operation.durationMs
  }

  async _instrumentToolCall(trace, parent, operation) {
    // TODO:
    // 1. Use withSpan to create "tool_execution" child span
    // 2. Set attributes: toolName, toolInput, resultCount
    // 3. Log with this.logger.logToolCall()
    // 4. Sleep for operation.durationMs
  }
}

// =============================================================================
// SELF-TEST
// =============================================================================

async function selfTest() {
  console.log("=".repeat(60));
  console.log("M19 Agent Instrumenter \u2014 Self-Test");
  console.log("=".repeat(60));
  console.log();

  const logger = new StructuredLogger("ucc_agent");
  const agent = new MockUCCAgent();
  const instrumented = new InstrumentedAgent(agent, logger);

  const [result, trace] = await instrumented.run(
    "Find all UCC filings for Greenfield Logistics in New York"
  );

  console.log(`\n${"=".repeat(60)}`);
  console.log("TRACE SUMMARY");
  console.log("=".repeat(60));
  console.log(`  Trace ID:    ${trace.traceId}`);
  console.log(`  Total Spans: ${trace.spans.length}`);
  console.log(`  Duration:    ${trace.getDurationMs().toFixed(1)} ms`);
  console.log();

  for (const span of trace.spans) {
    const indent = span.parentSpanId ? "    " : "  ";
    const icon = span.status === "ok" ? "OK" : "ERR";
    console.log(`${indent}[${icon}] ${span.name} \u2014 ${span.durationMs.toFixed(1)} ms`);
    if (Object.keys(span.attributes).length > 0) {
      for (const [k, v] of Object.entries(span.attributes)) {
        console.log(`${indent}     ${k}: ${JSON.stringify(v)}`);
      }
    }
    console.log();
  }

  console.log("=".repeat(60));
  console.log("AGENT ANSWER");
  console.log("=".repeat(60));
  console.log(result.answer);
  console.log();

  console.assert(trace.spans.length === 4, `Expected 4 spans, got ${trace.spans.length}`);
  const spanNames = trace.spans.map((s) => s.name);
  console.assert(spanNames.includes("agent_request"), "Missing root span");
  console.assert(spanNames.filter((n) => n === "llm_call").length === 2, "Expected 2 llm_call spans");
  console.assert(spanNames.includes("tool_execution"), "Missing tool_execution span");
  console.log("All assertions passed!");
}

export { MockUCCAgent, InstrumentedAgent };

const isMain = process.argv[1] && process.argv[1].endsWith("instrumenter.js");
if (isMain) {
  selfTest().catch(console.error);
}
