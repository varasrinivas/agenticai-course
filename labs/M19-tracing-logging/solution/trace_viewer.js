/**
 * M19 Lab — Trace Viewer (Solution)
 * ==================================
 * Complete terminal trace viewer and JSON exporter.
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
import assert from "node:assert/strict";

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

function getSpanColor(span) {
  if (span.status === "error") return Colors.RED;
  if (span.name.includes("llm")) return Colors.BLUE;
  if (span.name.includes("tool")) return Colors.GREEN;
  return Colors.CYAN;
}

// =============================================================================
// TRACE RENDERER
// =============================================================================

function renderTrace(trace) {
  const lines = [];

  const duration = trace.getDurationMs() || 0;
  const header = `Trace ${trace.traceId}  |  Total: ${duration.toFixed(1)}ms  |  ${trace.spans.length} spans`;
  lines.push(Colors.colorize(header, Colors.CYAN + Colors.BOLD));
  lines.push(Colors.colorize("-".repeat(header.length), Colors.GRAY));

  if (trace.rootSpan) {
    const rootText = `[${trace.rootSpan.durationMs.toFixed(1)}ms] ${trace.rootSpan.name}`;
    lines.push(Colors.colorize(rootText, getSpanColor(trace.rootSpan)));

    const childLines = renderChildren(trace, trace.rootSpan, "", duration);
    lines.push(...childLines);
  }

  if (trace.metadata && Object.keys(trace.metadata).length > 0) {
    lines.push("");
    lines.push(Colors.colorize("Metadata:", Colors.GRAY));
    for (const [k, v] of Object.entries(trace.metadata)) {
      lines.push(Colors.colorize(`  ${k}: ${v}`, Colors.GRAY));
    }
  }

  const result = lines.join("\n");
  console.log(result);
  return result;
}

function renderChildren(trace, parent, prefix, totalMs) {
  const children = trace.getChildSpans(parent);
  const lines = [];

  children.forEach((child, i) => {
    const isLast = i === children.length - 1;
    const connector = isLast ? "\u2514\u2500\u2500 " : "\u251c\u2500\u2500 ";

    let info = `[${child.durationMs.toFixed(1)}ms] ${child.name}`;

    if (child.attributes.model) {
      const totalTokens = child.attributes.total_tokens || "?";
      info += ` (${child.attributes.model}, ${totalTokens} tokens)`;
    } else if (child.attributes.tool_name) {
      info += ` (${child.attributes.tool_name})`;
    }

    const pct =
      totalMs > 0 ? ((child.durationMs / totalMs) * 100).toFixed(1) : "0.0";
    const pctStr = `  ${pct}%`;

    const color = getSpanColor(child);
    const coloredInfo = Colors.colorize(
      `${prefix}${connector}${info}`,
      color
    );
    const coloredPct = Colors.colorize(pctStr, Colors.GRAY);

    lines.push(`${coloredInfo}${coloredPct}`);

    const childPrefix = prefix + (isLast ? "    " : "\u2502   ");
    lines.push(...renderChildren(trace, child, childPrefix, totalMs));
  });

  return lines;
}

// =============================================================================
// JSON EXPORT
// =============================================================================

function renderTraceJson(trace, outputPath = null) {
  const traceDict = {
    traceId: trace.traceId,
    name: trace.name,
    durationMs: trace.getDurationMs(),
    metadata: trace.metadata,
    spans: trace.spans.map((span) => ({
      spanId: span.spanId,
      traceId: span.traceId,
      parentSpanId: span.parentSpanId,
      name: span.name,
      status: span.status,
      startTimeUnixUs: span.startTime ? span.startTime * 1000 : null,
      endTimeUnixUs: span.endTime ? span.endTime * 1000 : null,
      durationMs: span.durationMs,
      attributes: span.attributes,
      events: span.events,
    })),
  };

  if (outputPath) {
    fs.mkdirSync(path.dirname(outputPath), { recursive: true });
    fs.writeFileSync(outputPath, JSON.stringify(traceDict, null, 2));
  }

  return traceDict;
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

  assert.ok(rendered != null, "renderTrace should return a string");
  assert.ok(rendered.length > 0, "Rendered trace should not be empty");
  assert.ok(
    traceJson.spans.length === 4,
    `Expected 4 spans, got ${traceJson.spans.length}`
  );
  console.log("All assertions passed!");
}

export { renderTrace, renderTraceJson };

const isMain =
  process.argv[1] && process.argv[1].endsWith("trace_viewer.js");
if (isMain) {
  selfTest().catch(console.error);
}
