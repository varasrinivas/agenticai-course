/**
 * M19 Lab — Trace Data Model (Solution)
 * ======================================
 * Complete trace/span data model compatible with OpenTelemetry concepts.
 *
 * Usage:
 *     node trace_model.js
 */

import crypto from "crypto";

// =============================================================================
// SPAN
// =============================================================================

class Span {
  constructor(name, traceId, options = {}) {
    this.name = name;
    this.traceId = traceId;
    this.spanId = options.spanId || crypto.randomBytes(8).toString("hex");
    this.parentSpanId = options.parentSpanId || null;
    this.startTime = null;
    this.endTime = null;
    this.durationMs = null;
    this.attributes = {};
    this.events = [];
    this.status = "ok";
  }

  setAttribute(key, value) {
    this.attributes[key] = value;
  }

  addEvent(name, attributes = {}) {
    this.events.push({
      name,
      timestamp: new Date().toISOString(),
      attributes,
    });
  }

  finish() {
    this.endTime = Date.now();
    this.durationMs = Math.round((this.endTime - this.startTime) * 100) / 100;
  }
}

// =============================================================================
// TRACE
// =============================================================================

class Trace {
  constructor(name = "trace", metadata = {}) {
    this.traceId = crypto.randomBytes(8).toString("hex");
    this.name = name;
    this.metadata = metadata;
    this.spans = [];
    this.rootSpan = null;
  }

  createRootSpan(name) {
    const span = new Span(name, this.traceId);
    span.startTime = Date.now();
    this.rootSpan = span;
    this.spans.push(span);
    return span;
  }

  createChildSpan(name, parent) {
    const span = new Span(name, this.traceId, { parentSpanId: parent.spanId });
    span.startTime = Date.now();
    this.spans.push(span);
    return span;
  }

  getDurationMs() {
    return this.rootSpan ? this.rootSpan.durationMs : null;
  }

  getChildSpans(parent) {
    return this.spans.filter((s) => s.parentSpanId === parent.spanId);
  }
}

// =============================================================================
// SPAN CONTEXT (callback-based for JS)
// =============================================================================

async function withSpan(trace, name, parent, callback) {
  const span =
    parent === null
      ? trace.createRootSpan(name)
      : trace.createChildSpan(name, parent);

  try {
    const result = await callback(span);
    return result;
  } catch (err) {
    span.status = "error";
    span.addEvent("exception", {
      type: err.constructor.name,
      message: err.message,
    });
    throw err;
  } finally {
    span.finish();
  }
}

// =============================================================================
// SELF-TEST
// =============================================================================

async function selfTest() {
  console.log("=".repeat(60));
  console.log("M19 Trace Model \u2014 Self-Test");
  console.log("=".repeat(60));

  const trace = new Trace("ucc_research_agent", {
    query: "Find filings for Acme Corp",
  });

  await withSpan(trace, "agent_request", null, async (root) => {
    root.setAttribute("query", "Find filings for Acme Corp");

    await withSpan(trace, "llm_call", root, async (llmSpan) => {
      llmSpan.setAttribute("model", "claude-sonnet-4-6");
      llmSpan.setAttribute("input_tokens", 350);
      llmSpan.setAttribute("output_tokens", 120);
      await new Promise((r) => setTimeout(r, 50));
    });

    await withSpan(trace, "tool_execution", root, async (toolSpan) => {
      toolSpan.setAttribute("tool_name", "search_filings");
      toolSpan.setAttribute("input", { debtor_name: "Acme Corp" });
      await new Promise((r) => setTimeout(r, 20));
      toolSpan.setAttribute("output_records", 3);
    });

    await withSpan(trace, "llm_call", root, async (llmSpan2) => {
      llmSpan2.setAttribute("model", "claude-sonnet-4-6");
      llmSpan2.setAttribute("input_tokens", 800);
      llmSpan2.setAttribute("output_tokens", 200);
      await new Promise((r) => setTimeout(r, 30));
    });
  });

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
  console.assert(
    trace.spans.length === 4,
    `Expected 4 spans, got ${trace.spans.length}`
  );
  console.assert(
    children.length === 3,
    `Expected 3 children, got ${children.length}`
  );
  console.assert(trace.rootSpan.status === "ok", "Root span should be ok");
  console.log("\nAll assertions passed!");
}

export { Span, Trace, withSpan };

const isMain =
  process.argv[1] && process.argv[1].endsWith("trace_model.js");
if (isMain) {
  selfTest().catch(console.error);
}
