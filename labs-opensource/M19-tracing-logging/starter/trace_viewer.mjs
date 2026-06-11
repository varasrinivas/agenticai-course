#!/usr/bin/env node
/**
 * M19 Lab: Trace Viewer (COMPLETE — Node.js)
 * ===========================================
 * Usage: node trace_viewer.mjs traces/trace_a3f7b2.jsonl [--slow-threshold 2000]
 * Reads the same JSONL schema the Python tracer writes.
 */

import fs from "node:fs";

const RED = "\x1b[91m", YELLOW = "\x1b[93m", GREEN = "\x1b[92m";
const CYAN = "\x1b[96m", DIM = "\x1b[2m", RESET = "\x1b[0m", BOLD = "\x1b[1m";

function loadEvents(filepath) {
  return fs.readFileSync(filepath, "utf-8").split("\n").filter(Boolean)
    .map((l) => { try { return JSON.parse(l); } catch { return null; } })
    .filter(Boolean);
}

function printCallTree(events, slowMs = 2000) {
  console.log("\n" + BOLD + "-".repeat(60) + RESET);
  console.log(BOLD + `TRACE: ${events[0]?.run_id ?? "unknown"}` + RESET);
  console.log("-".repeat(60));
  for (const ev of events) {
    const latency = ev.latency_ms ?? 0;
    const slow = latency > slowMs ? ` ${RED}SLOW${RESET}` : "";
    if (ev.category === "llm_turn") {
      console.log(`  ${YELLOW}LLM [${ev.model ?? "?"}]${RESET}  ` +
        `${DIM}${ev.prompt_tokens ?? "?"}->${ev.completion_tokens ?? "?"} tok  ${ev.finish_reason ?? "?"}${RESET}  ` +
        `${YELLOW}${latency.toFixed(0)}ms${RESET}${slow}`);
    } else if (ev.category === "tool_call") {
      const status = ev.tool_ok ? `${GREEN}ok${RESET}` : `${RED}ERR ${String(ev.tool_error ?? "").slice(0, 40)}${RESET}`;
      console.log(`    ${GREEN}TOOL ${ev.tool_name ?? "?"}${RESET}  ${status}  ${YELLOW}${latency.toFixed(0)}ms${RESET}${slow}`);
    } else if (ev.category === "loop_iter") {
      console.log(`  ${CYAN}-- iter ${ev.iteration ?? "?"} [${ev.exit_reason ?? "?"}] ` +
        `tools=${JSON.stringify(ev.tools_invoked ?? [])} ${YELLOW}${latency.toFixed(0)}ms${RESET}${slow}`);
    } else if (ev.category === "error") {
      console.log(`  ${RED}ERROR ${ev.exc_type ?? "?"}: ${String(ev.exc_msg ?? "").slice(0, 80)}${RESET}`);
    }
  }
  console.log("-".repeat(60));
}

function printSummary(events, slowMs) {
  const byCat = {};
  for (const ev of events) {
    (byCat[ev.category ?? "?"] ??= []).push(ev.latency_ms ?? 0);
  }
  console.log(`\n${BOLD}Category breakdown:${RESET}`);
  console.log(`${"category".padEnd(12)} ${"count".padStart(5)} ${"avg_latency_ms".padStart(15)}`);
  for (const [cat, lats] of Object.entries(byCat).sort()) {
    const avg = lats.reduce((a, b) => a + b, 0) / (lats.length || 1);
    console.log(`${cat.padEnd(12)} ${String(lats.length).padStart(5)} ${avg.toFixed(1).padStart(15)}`);
  }
  const slow = events.filter((e) => (e.latency_ms ?? 0) > slowMs);
  if (slow.length) {
    console.log(`\n${RED}Slow steps (>${slowMs}ms):${RESET}`);
    for (const e of slow) {
      console.log(`  ${e.category}: ${e.tool_name ?? e.model ?? ""}  ${(e.latency_ms ?? 0).toFixed(0)}ms`);
    }
  }
}

const [, , tracefile, ...flags] = process.argv;
if (!tracefile) {
  console.error("Usage: node trace_viewer.mjs <tracefile.jsonl> [--slow-threshold N]");
  process.exit(1);
}
const slowIdx = flags.indexOf("--slow-threshold");
const slowThreshold = slowIdx >= 0 ? parseFloat(flags[slowIdx + 1] ?? "2000") : 2000;
if (!fs.existsSync(tracefile)) {
  console.error(`File not found: ${tracefile}`);
  process.exit(1);
}
const events = loadEvents(tracefile);
if (!events.length) {
  console.error("Trace file is empty.");
  process.exit(1);
}
printCallTree(events, slowThreshold);
printSummary(events, slowThreshold);
