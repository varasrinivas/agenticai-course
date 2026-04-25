/**
 * M19 Lab — Trace Data Model (Starter)
 * =====================================
 * Build a trace/span data model from scratch, compatible with
 * OpenTelemetry concepts. No external tracing libraries needed.
 *
 * KEY CONCEPT: A *trace* is one end-to-end request. A *span* is
 * one unit of work inside that trace. Spans nest: a root span
 * contains child spans, forming a tree.
 *
 * Usage:
 *     node trace_model.js
 */

import crypto from "crypto";

// =============================================================================
// SPAN — one unit of work inside a trace
// =============================================================================

// WHAT: A span captures a single operation: its name, timing, attributes,
//   and any events (like errors) that occurred during execution.
// WHY:  Spans are the building blocks of traces. Each API call, tool
//   execution, or processing step becomes its own span.
// GOTCHA: span_id and trace_id should be generated automatically.

class Span {
  /**
   * @param {string} name - Human-readable operation name
   * @param {string} traceId - ID of the parent trace
   * @param {object} options - Optional: spanId, parentSpanId
   */
  constructor(name, traceId, options = {}) {
    this.name = name;
    this.traceId = traceId;
    this.spanId = options.spanId || crypto.randomBytes(8).toString("hex");
    this.parentSpanId = options.parentSpanId || null;
    this.startTime = null;    // Date.now() epoch ms
    this.endTime = null;
    this.durationMs = null;
    this.attributes = {};
    this.events = [];
    this.status = "ok";       // "ok" or "error"
  }

  /**
   * Set a key-value attribute on this span.
   */
  setAttribute(key, value) {
    // TODO: Store the key-value pair in this.attributes
  }

  /**
   * Record a timestamped event (e.g., an error or milestone).
   */
  addEvent(name, attributes = {}) {
    // TODO: Push an object to this.events with:
    //   - name: the event name
    //   - timestamp: new Date().toISOString()
    //   - attributes: the attributes object
  }

  /**
   * Mark the span as finished — set endTime and calculate durationMs.
   */
  finish() {
    // TODO:
    // 1. Set this.endTime to Date.now()
    // 2. Calculate this.durationMs = this.endTime - this.startTime
    // 3. Round to 2 decimal places
  }
}

// =============================================================================
// TRACE — a collection of spans representing one end-to-end request
// =============================================================================

class Trace {
  /**
   * @param {string} name - Human-readable trace name
   * @param {object} metadata - Optional key-value metadata
   */
  constructor(name = "trace", metadata = {}) {
    // TODO: Initialize the following properties:
    // - this.traceId: crypto.randomBytes(8).toString("hex")
    // - this.name: the trace name
    // - this.metadata: the metadata object
    // - this.spans: empty array
    // - this.rootSpan: null
  }

  /**
   * Create and register the root span for this trace.
   */
  createRootSpan(name) {
    // TODO:
    // 1. Create a new Span with the given name and this.traceId
    // 2. Set span.startTime = Date.now()
    // 3. Store as this.rootSpan
    // 4. Push to this.spans
    // 5. Return the span
  }

  /**
   * Create a child span under the given parent span.
   */
  createChildSpan(name, parent) {
    // TODO:
    // 1. Create a new Span with the given name, this.traceId,
    //    and parentSpanId = parent.spanId
    // 2. Set span.startTime = Date.now()
    // 3. Push to this.spans
    // 4. Return the span
  }

  /**
   * Get total trace duration from the root span.
   */
  getDurationMs() {
    // TODO: Return this.rootSpan.durationMs if rootSpan exists, else null
  }

  /**
   * Get all direct children of a given span.
   */
  getChildSpans(parent) {
    // TODO: Return spans whose parentSpanId === parent.spanId
  }
}

// =============================================================================
// SPAN CONTEXT — helper for automatic timing (using callbacks in JS)
// =============================================================================

// WHAT: A helper that wraps a callback with automatic span start/finish
//   and error capture. JS equivalent of Python's context manager.
// WHY:  Manual start/finish calls are error-prone. This helper
//   guarantees every span gets a duration, even if the code throws.

/**
 * Execute a callback within a new span, with automatic timing.
 *
 * @param {Trace} trace - The trace this span belongs to
 * @param {string} name - Span name
 * @param {Span|null} parent - Parent span (null = root)
 * @param {function} callback - Async function receiving the span: (span) => {...}
 * @returns {Promise<any>} The callback's return value
 */
async function withSpan(trace, name, parent, callback) {
  // TODO:
  // 1. If parent is null, create root span; otherwise create child span
  // 2. Try: await callback(span), capture the return value
  // 3. Catch: set span.status = "error", add exception event, re-throw
  // 4. Finally: call span.finish()
  // 5. Return the callback's return value
}

// =============================================================================
// SELF-TEST
// =============================================================================

async function selfTest() {
  console.log("=".repeat(60));
  console.log("M19 Trace Model — Self-Test");
  console.log("=".repeat(60));

  const trace = new Trace("ucc_research_agent", { query: "Find filings for Acme Corp" });

  await withSpan(trace, "agent_request", null, async (root) => {
    root.setAttribute("query", "Find filings for Acme Corp");

    // Simulate LLM call
    await withSpan(trace, "llm_call", root, async (llmSpan) => {
      llmSpan.setAttribute("model", "claude-sonnet-4-20250514");
      llmSpan.setAttribute("input_tokens", 350);
      llmSpan.setAttribute("output_tokens", 120);
      await new Promise((r) => setTimeout(r, 50));
    });

    // Simulate tool execution
    await withSpan(trace, "tool_execution", root, async (toolSpan) => {
      toolSpan.setAttribute("tool_name", "search_filings");
      toolSpan.setAttribute("input", { debtor_name: "Acme Corp" });
      await new Promise((r) => setTimeout(r, 20));
      toolSpan.setAttribute("output_records", 3);
    });

    // Simulate second LLM call
    await withSpan(trace, "llm_call", root, async (llmSpan2) => {
      llmSpan2.setAttribute("model", "claude-sonnet-4-20250514");
      llmSpan2.setAttribute("input_tokens", 800);
      llmSpan2.setAttribute("output_tokens", 200);
      await new Promise((r) => setTimeout(r, 30));
    });
  });

  // Print results
  console.log(`\nTrace ID:    ${trace.traceId}`);
  console.log(`Trace Name:  ${trace.name}`);
  console.log(`Total Spans: ${trace.spans.length}`);
  console.log(`Duration:    ${trace.getDurationMs().toFixed(1)} ms`);
  console.log();

  for (const span of trace.spans) {
    const indent = span.parentSpanId ? "  " : "";
    console.log(`${indent}Span: ${span.name}`);
    console.log(`${indent}  ID:       ${span.spanId}`);
    console.log(`${indent}  Parent:   ${span.parentSpanId || "None (root)"}`);
    console.log(`${indent}  Duration: ${span.durationMs.toFixed(1)} ms`);
    console.log(`${indent}  Status:   ${span.status}`);
    if (Object.keys(span.attributes).length > 0) {
      console.log(`${indent}  Attrs:    ${JSON.stringify(span.attributes)}`);
    }
    console.log();
  }

  const children = trace.getChildSpans(trace.rootSpan);
  console.log(`Root span has ${children.length} children`);
  console.assert(trace.spans.length === 4, `Expected 4 spans, got ${trace.spans.length}`);
  console.assert(children.length === 3, `Expected 3 children, got ${children.length}`);
  console.assert(trace.rootSpan.status === "ok", "Root span should be ok");
  console.log("\nAll assertions passed!");
}

export { Span, Trace, withSpan };

// Run self-test when executed directly
const isMain = process.argv[1] && (
  process.argv[1].endsWith("trace_model.js")
);
if (isMain) {
  selfTest().catch(console.error);
}
