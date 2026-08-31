/**
 * M15 Lab — Code Interpreter & Sandbox Execution (Solution)
 * ===========================================================
 *
 * Usage:
 *     node code_interpreter.js
 */

import Anthropic from "@anthropic-ai/sdk";
import { config } from "dotenv";
import { dirname, join } from "path";
import { fileURLToPath, pathToFileURL } from "url";
import { writeFileSync, unlinkSync, existsSync } from "fs";
import { execFileSync } from "child_process";
import { tmpdir } from "os";

config();
const __dirname = dirname(fileURLToPath(import.meta.url));
// pathToFileURL: ESM import() needs a file:// URL, not a filesystem path.
// A bare Windows path (D:\...) is read as protocol 'd:' and rejected with
// ERR_UNSUPPORTED_ESM_URL_SCHEME. Posix paths happen to work, which is why
// this only breaks on Windows.
const { ALL_FILINGS, searchFilings } = await import(pathToFileURL(join(__dirname, "..", "..", "shared", "mock_ucc_data.js")).href);

const client = new Anthropic();
const MODEL = "claude-sonnet-4-6";

function observe(label, msg) { console.log(`\n${"=".repeat(60)}\n[${label}] ${msg}\n${"=".repeat(60)}`); }
function observeCode(code) { console.log(`\n${"─".repeat(60)}\n[CODE] Agent-generated Python:`); code.split("\n").forEach((l,i) => console.log(`  ${String(i+1).padStart(3)} | ${l}`)); console.log("─".repeat(60)); }
function observeExecution(stdout, stderr, success) { console.log(`\n${"─".repeat(60)}\n[EXECUTION: ${success?"SUCCESS":"ERROR"}]`); if(stdout) console.log(`[STDOUT]\n${stdout}`); if(stderr) console.log(`[STDERR]\n${stderr}`); console.log("─".repeat(60)); }

const dataPreamble = `FILINGS = ${JSON.stringify(ALL_FILINGS.map(f => ({
  filing_number: f.filing_number, type: f.type, state: f.state,
  filing_date: f.filing_date, expiration_date: f.expiration_date, status: f.status,
  debtor_name: f.debtor.name, secured_party_name: f.secured_party.name,
  collateral_description: f.collateral_description,
})), null, 2)}\n\n`;

function executePython(code, timeout = 10000) {
  const fullCode = dataPreamble + code;
  const tmpPath = join(tmpdir(), `m15_exec_${Date.now()}.py`);
  try {
    writeFileSync(tmpPath, fullCode, "utf8");
    const stdout = execFileSync("python", [tmpPath], { timeout, encoding: "utf8", stdio: ["pipe", "pipe", "pipe"] });
    return { success: true, stdout, stderr: "" };
  } catch (e) {
    if (e.killed) return { success: false, stdout: "", stderr: `Timeout after ${timeout}ms` };
    return { success: false, stdout: e.stdout || "", stderr: e.stderr || e.message };
  } finally {
    if (existsSync(tmpPath)) unlinkSync(tmpPath);
  }
}

const TOOLS = [
  { name: "run_python_code", description: "Execute Python code. FILINGS pre-loaded. Use print().",
    input_schema: { type: "object", properties: { code: { type: "string" } }, required: ["code"] } },
  { name: "search_filings", description: "Search UCC filings.",
    input_schema: { type: "object", properties: { debtor_name: { type: "string" }, state: { type: "string" } }, required: [] } },
];

function executeTool(name, input) {
  try {
    if (name === "run_python_code") {
      observeCode(input.code);
      const r = executePython(input.code);
      observeExecution(r.stdout, r.stderr, r.success);
      return r.success ? (r.stdout || "(no output)") : JSON.stringify({ error: "Code failed", stderr: r.stderr });
    } else if (name === "search_filings") {
      const r = searchFilings({ debtorName: input.debtor_name, state: input.state });
      return JSON.stringify(r.map(f => ({ filing_number: f.filing_number, debtor: f.debtor.name, state: f.state, status: f.status })), null, 2);
    }
    return JSON.stringify({ error: `Unknown: ${name}` });
  } catch (e) { return JSON.stringify({ error: e.message }); }
}

const SYSTEM = `You are a UCC filing data analyst. Write Python code to analyze FILINGS (pre-loaded list of dicts).
Keys: filing_number, type, state, filing_date, expiration_date, status, debtor_name, secured_party_name, collateral_description.
Always print() results. Use standard library only. Fix errors if they occur.`;

async function runCodeAgent(query, maxTurns = 8) {
  observe("QUERY", query);
  const messages = [{ role: "user", content: query }];

  for (let t = 0; t < maxTurns; t++) {
    const resp = await client.messages.create({ model: MODEL, max_tokens: 4096, system: SYSTEM, tools: TOOLS, messages });
    if (resp.stop_reason !== "tool_use") {
      const text = resp.content.filter(b => b.type === "text").map(b => b.text).join("");
      observe("RESPONSE", text.slice(0, 200) + (text.length > 200 ? "..." : ""));
      return text;
    }
    const results = [];
    for (const b of resp.content) { if (b.type === "tool_use") results.push({ type: "tool_result", tool_use_id: b.id, content: executeTool(b.name, b.input) }); }
    messages.push({ role: "assistant", content: resp.content });
    messages.push({ role: "user", content: results });
  }
  return "Agent did not complete.";
}

console.log("=".repeat(60));
console.log("M15 Lab — Code Interpreter & Sandbox Execution (SOLUTION)");
console.log("=".repeat(60));

const r1 = await runCodeAgent("Count UCC filings by state and show the results");
console.log(`\nFINAL ANSWER:\n${r1}`);

const r2 = await runCodeAgent("Calculate the average number of days until expiration for all active filings");
console.log(`\nFINAL ANSWER:\n${r2}`);

const r3 = await runCodeAgent("What percentage of filings have blanket liens vs specific collateral?");
console.log(`\nFINAL ANSWER:\n${r3}`);
