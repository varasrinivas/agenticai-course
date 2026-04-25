/**
 * M19 Lab — Agent Instrumenter (Solution)
 * ========================================
 * Complete instrumented agent with tracing and structured logging.
 *
 * Usage:
 *     node instrumenter.js
 */

import { Trace, Span, withSpan } from "./trace_model.js";
import { StructuredLogger, scrubPii } from "./structured_logger.js";

// =============================================================================
// MOCK AGENT
// =============================================================================

class MockUCCAgent {
  constructor() {
    this.model = "claude-sonnet-4-20250514";
    this.callLog = [];
  }

  async run(query) {
    const operations = [];

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
  constructor(agent, logger) {
    this.agent = agent;
    this.logger = logger;
  }

  async run(query) {
    const trace = new Trace("agent_request", { query });
    let finalResult;

    try {
      await withSpan(trace, "agent_request", null, async (root) => {
        root.setAttribute("query", query);
        this.logger.log("INFO", "Agent request started", {
          traceId: trace.traceId,
          spanId: root.spanId,
          query,
        });

        const result = await this.agent.run(query);

        for (const operation of result.operations) {
          if (operation.type === "llm_call") {
            await this._instrumentLlmCall(trace, root, operation);
          } else if (operation.type === "tool_call") {
            await this._instrumentToolCall(trace, root, operation);
          }
        }

        root.setAttribute("answer_length", result.answer.length);
        this.logger.log("INFO", "Agent request completed", {
          traceId: trace.traceId,
          spanId: root.spanId,
          totalSpans: trace.spans.length,
        });

        finalResult = result;
      });
    } catch (err) {
      this.logger.logError(err, { traceId: trace.traceId });
      throw err;
    }

    return [finalResult, trace];
  }

  async _instrumentLlmCall(trace, parent, operation) {
    await withSpan(trace, "llm_call", parent, async (span) => {
      span.setAttribute("model", operation.model);
      span.setAttribute("input_tokens", operation.inputTokens);
      span.setAttribute("output_tokens", operation.outputTokens);
      span.setAttribute(
        "total_tokens",
        operation.inputTokens + operation.outputTokens
      );
      span.setAttribute("stop_reason", operation.response.stopReason);

      this.logger.logLlmCall({
        model: operation.model,
        inputTokens: operation.inputTokens,
        outputTokens: operation.outputTokens,
        durationMs: operation.durationMs,
        traceId: trace.traceId,
        spanId: span.spanId,
      });

      await new Promise((r) => setTimeout(r, operation.durationMs));
    });
  }

  async _instrumentToolCall(trace, parent, operation) {
    await withSpan(trace, "tool_execution", parent, async (span) => {
      span.setAttribute("tool_name", operation.toolName);
      span.setAttribute("tool_input", operation.toolInput);
      span.setAttribute(
        "result_count",
        (operation.toolOutput.results || []).length
      );

      this.logger.logToolCall({
        toolName: operation.toolName,
        toolInput: operation.toolInput,
        toolOutput: operation.toolOutput,
        durationMs: operation.durationMs,
        traceId: trace.traceId,
        spanId: span.spanId,
      });

      await new Promise((r) => setTimeout(r, operation.durationMs));
    });
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
    console.log(
      `${indent}[${icon}] ${span.name} \u2014 ${span.durationMs.toFixed(1)} ms`
    );
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

  console.assert(
    trace.spans.length === 4,
    `Expected 4 spans, got ${trace.spans.length}`
  );
  const spanNames = trace.spans.map((s) => s.name);
  console.assert(spanNames.includes("agent_request"), "Missing root span");
  console.assert(
    spanNames.filter((n) => n === "llm_call").length === 2,
    "Expected 2 llm_call spans"
  );
  console.assert(
    spanNames.includes("tool_execution"),
    "Missing tool_execution span"
  );
  console.log("All assertions passed!");
}

export { MockUCCAgent, InstrumentedAgent };

const isMain =
  process.argv[1] && process.argv[1].endsWith("instrumenter.js");
if (isMain) {
  selfTest().catch(console.error);
}
