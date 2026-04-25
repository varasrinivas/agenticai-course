/**
 * M19 Lab — Trace Viewer (Starter)
 * =================================
 * Render traces as a tree in the terminal and export to JSON.
 *
 * KEY CONCEPT: A trace is a tree of spans. The viewer walks that tree
 * and draws it with box-drawing characters, color-codes each span by
 * type, and shows timing as a percentage of total duration.
 *
 * Usage:
 *     node trace_viewer.js
 */

import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";
import { Trace, Span, withSpan } from "./trace_model.js";
import { StructuredLogger } from "./structured_logger.js";
import { MockUCCAgent, InstrumentedAgent } from "./instrumenter.js";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

// =============================================================================
// ANSI COLOR HELPERS
// =============================================================================

const Colors = {
  BLUE: "\x1b[94m",
  GREEN: "\x1b[92m",
  RED: "\x1b[91m",
  YELLOW: "\x1b[93m",
  CYAN: "\x1b[96m",
  GRAY: "\x1b[90m",
  BOLD: "\x1b[1m",
  RESET: "\x1b[0m",

  enabled() {
    return !process.env.NO_COLOR;
  },

  colorize(text, color) {
    if (this.enabled()) {
      return `${color}${text}${this.RESET}`;
    }
    return text;
  },
};

/**
 * Return the appropriate color for a span based on its name/status.
 */
function getSpanColor(span) {
  // TODO:
  // - If span.status === "error", return Colors.RED
  // - If span.name includes "llm", return Colors.BLUE
  // - If span.name includes "tool", return Colors.GREEN
  // - Otherwise return Colors.CYAN
}

// =============================================================================
// TRACE RENDERER
// =============================================================================

/**
 * Render a trace as a colored tree in the terminal.
 * @param {Trace} trace
 * @returns {string} The rendered output
 */
function renderTrace(trace) {
  // TODO: Implement trace rendering:
  //
  // 1. Build header lines:
  //    "Trace {traceId}  |  Total: {duration}ms  |  {N} spans"
  //    A separator line of dashes
  //
  // 2. Render root span: "[{duration}ms] {name}"
  //
  // 3. Render children using renderChildren()
  //
  // 4. Add metadata section if trace.metadata has keys
  //
  // 5. Join lines, console.log, and return
}

/**
 * Recursively render child spans with tree-drawing characters.
 */
function renderChildren(trace, parent, prefix, totalMs) {
  // TODO: Implement recursive child rendering:
  //
  // 1. Get children of parent
  // 2. For each child:
  //    a. Choose connector: last child = "\u2514\u2500\u2500 ", others = "\u251c\u2500\u2500 "
  //    b. Build info: "[{duration}ms] {name}"
  //       - Add model + tokens if llm span
  //       - Add tool_name if tool span
  //    c. Calculate and append percentage
  //    d. Colorize the line
  //    e. Recurse with updated prefix
  //
  // 3. Return array of formatted lines
}

// =============================================================================
// JSON EXPORT
// =============================================================================

/**
 * Export a trace as OpenTelemetry-compatible JSON.
 */
function renderTraceJson(trace, outputPath = null) {
  // TODO:
  // 1. Build trace object with traceId, name, durationMs, metadata, spans[]
  // 2. Each span: spanId, traceId, parentSpanId, name, status,
  //    startTimeUnixUs, endTimeUnixUs, durationMs, attributes, events
  // 3. If outputPath, write JSON to file
  // 4. Return the object
}

// =============================================================================
// SELF-TEST
// =============================================================================

async function selfTest() {
  console.log("=".repeat(60));
  console.log("M19 Trace Viewer \u2014 Self-Test");
  console.log("=".repeat(60));
  console.log();

  const logger = new StructuredLogger("ucc_agent", "WARN");
  const agent = new MockUCCAgent();
  const instrumented = new InstrumentedAgent(agent, logger);
  const [result, trace] = await instrumented.run(
    "Find all UCC filings for Greenfield Logistics in New York"
  );

  console.log("\n--- Terminal Trace View ---\n");
  const rendered = renderTrace(trace);

  console.log("\n--- JSON Export ---\n");
  const outputDir = path.join(__dirname, "..", "expected_output");
  fs.mkdirSync(outputDir, { recursive: true });
  const jsonPath = path.join(outputDir, "trace_export.json");
  const traceJson = renderTraceJson(trace, jsonPath);
  console.log(`Trace exported to: ${jsonPath}`);
  console.log(`Spans in export: ${traceJson.spans.length}`);
  console.log(`Trace duration:  ${traceJson.durationMs.toFixed(1)} ms`);
  console.log();

  console.assert(rendered != null, "renderTrace should return a string");
  console.assert(rendered.length > 0, "Rendered trace should not be empty");
  console.assert(traceJson.spans.length === 4, `Expected 4 spans, got ${traceJson.spans.length}`);
  console.log("All assertions passed!");
}

export { renderTrace, renderTraceJson };

const isMain = process.argv[1] && process.argv[1].endsWith("trace_viewer.js");
if (isMain) {
  selfTest().catch(console.error);
}
