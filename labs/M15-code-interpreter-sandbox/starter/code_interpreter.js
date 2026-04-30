/**
 * M15 Lab — Code Interpreter & Sandbox Execution (Starter)
 * ==========================================================
 * Agent that writes and executes Python code to analyze UCC data.
 *
 * NOTE: Even in the Node.js version, the agent writes PYTHON code
 * because Python is the standard for data analysis. The Node.js
 * agent orchestrates the loop; Python does the computation.
 *
 * Usage:
 *     node code_interpreter.js
 */

import Anthropic from "@anthropic-ai/sdk";
import { config } from "dotenv";
import { dirname, join } from "path";
import { fileURLToPath } from "url";
import { writeFileSync, unlinkSync, existsSync } from "fs";
import { execSync } from "child_process";
import { tmpdir } from "os";

config();
const __dirname = dirname(fileURLToPath(import.meta.url));
const { ALL_FILINGS, searchFilings } = await import(join(__dirname, "..", "..", "shared", "mock_ucc_data.js"));

const client = new Anthropic();
const MODEL = "claude-sonnet-4-6";

function observe(label, msg) { console.log(`\n${"=".repeat(60)}\n[${label}] ${msg}\n${"=".repeat(60)}`); }
function observeCode(code) { console.log(`\n${"─".repeat(60)}\n[CODE] Agent-generated Python:`); code.split("\n").forEach((l,i) => console.log(`  ${String(i+1).padStart(3)} | ${l}`)); console.log("─".repeat(60)); }
function observeExecution(stdout, stderr, success) { console.log(`\n${"─".repeat(60)}\n[EXECUTION: ${success?"SUCCESS":"ERROR"}]`); if(stdout) console.log(`[STDOUT]\n${stdout}`); if(stderr) console.log(`[STDERR]\n${stderr}`); console.log("─".repeat(60)); }

// Build data preamble (Python code that defines FILINGS variable)
const dataPreamble = `FILINGS = ${JSON.stringify(ALL_FILINGS.map(f => ({
  filing_number: f.filing_number, type: f.type, state: f.state,
  filing_date: f.filing_date, expiration_date: f.expiration_date, status: f.status,
  debtor_name: f.debtor.name, secured_party_name: f.secured_party.name,
  collateral_description: f.collateral_description,
})), null, 2)}\n\n`;

/**
 * Execute Python code in a subprocess.
 *
 * TODO 1: Implement this function
 *   - Prepend dataPreamble to the code
 *   - Write to a temp file
 *   - Execute with execSync or child_process
 *   - Return { success, stdout, stderr }
 *   - Handle timeout and errors
 */
function executePython(code, timeout = 10000) {
  // Your code here
  return { success: false, stdout: "", stderr: "Not implemented" };
}

const TOOLS = [
  { name: "run_python_code", description: "Execute Python code. FILINGS variable is pre-loaded. Use print() for output.",
    input_schema: { type: "object", properties: { code: { type: "string", description: "Python code" } }, required: ["code"] } },
  { name: "search_filings", description: "Search UCC filings.",
    input_schema: { type: "object", properties: { debtor_name: { type: "string" }, state: { type: "string" } }, required: [] } },
];

function executeTool(name, input) {
  try {
    if (name === "run_python_code") {
      observeCode(input.code);
      const result = executePython(input.code);
      observeExecution(result.stdout, result.stderr, result.success);
      return result.success ? (result.stdout || "(no output)") : JSON.stringify({ error: "Code failed", stderr: result.stderr });
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

/**
 * TODO 2: Implement the ReAct loop (same pattern as M12)
 */
async function runCodeAgent(query, maxTurns = 8) {
  observe("QUERY", query);
  // Your code here
  return "TODO: Implement ReAct loop";
}

console.log("=".repeat(60));
console.log("M15 Lab — Code Interpreter & Sandbox Execution");
console.log("=".repeat(60));

const r1 = await runCodeAgent("Count UCC filings by state and show the results");
console.log(`\nFINAL ANSWER:\n${r1}`);

const r2 = await runCodeAgent("Calculate the average number of days until expiration for all active filings");
console.log(`\nFINAL ANSWER:\n${r2}`);

const r3 = await runCodeAgent("What percentage of filings have blanket liens vs specific collateral?");
console.log(`\nFINAL ANSWER:\n${r3}`);
