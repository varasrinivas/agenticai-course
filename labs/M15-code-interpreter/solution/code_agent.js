/**
 * M15 Lab — Code Interpreter Agent (Solution — Node.js)
 * =======================================================
 * Agent that writes and executes Python code in a sandbox
 * to analyze UCC filing data.
 *
 * NOTE: The sandbox still executes Python via child_process.
 * The agent orchestration is in Node.js; the generated analysis
 * code is Python (because MOCK_FILINGS is a Python data structure).
 *
 * Usage:
 *     node code_agent.js
 */

import Anthropic from "@anthropic-ai/sdk";
import { config } from "dotenv";
import { dirname, join } from "path";
import { fileURLToPath } from "url";
import { writeFileSync, unlinkSync, existsSync } from "fs";
import { execFileSync } from "child_process";
import { tmpdir } from "os";

config();

const __dirname = dirname(fileURLToPath(import.meta.url));

// ---------------------------------------------------------------------------
// Load mock data from shared module and build a Python data preamble
// ---------------------------------------------------------------------------

const { ALL_FILINGS } = await import(
  join(__dirname, "..", "..", "shared", "mock_ucc_data.js")
);

const SERIALIZED_FILINGS = ALL_FILINGS.map((f) => ({
  filing_number: f.filing_number,
  type: f.type,
  state: f.state,
  filing_date: f.filing_date,
  expiration_date: f.expiration_date,
  status: f.status,
  debtor_name: f.debtor.name,
  debtor_address: f.debtor.address,
  debtor_org_type: f.debtor.org_type,
  debtor_jurisdiction: f.debtor.jurisdiction,
  secured_party_name: f.secured_party.name,
  secured_party_address: f.secured_party.address,
  collateral_description: f.collateral_description,
}));

const DATA_PREAMBLE = `MOCK_FILINGS = ${JSON.stringify(SERIALIZED_FILINGS, null, 2)}\n\n`;

// ---------------------------------------------------------------------------
// Observation helpers
// ---------------------------------------------------------------------------

function observe(label, msg) {
  console.log(`\n${"=".repeat(60)}\n[${label}] ${msg}\n${"=".repeat(60)}`);
}

function observeCode(code) {
  console.log(`\n${"─".repeat(60)}`);
  console.log("[CODE] Agent-generated Python:");
  code.split("\n").forEach((line, i) => {
    console.log(`  ${String(i + 1).padStart(3)} | ${line}`);
  });
  console.log("─".repeat(60));
}

function observeExecution(stdout, stderr, success) {
  console.log(`\n${"─".repeat(60)}`);
  console.log(`[EXECUTION: ${success ? "SUCCESS" : "ERROR"}]`);
  if (stdout) console.log(`[STDOUT]\n${stdout}`);
  if (stderr) console.log(`[STDERR]\n${stderr}`);
  console.log("─".repeat(60));
}

function observeThinking(text) {
  console.log(`\n${"─".repeat(60)}`);
  const truncated = text.length > 300 ? text.slice(0, 300) + "..." : text;
  console.log(`[THINK] ${truncated}`);
  console.log("─".repeat(60));
}

// ---------------------------------------------------------------------------
// Sandbox — execute Python code via child_process
// ---------------------------------------------------------------------------

function runInSandbox(code, timeoutMs = 10000) {
  const fullCode = DATA_PREAMBLE + code;
  const tmpPath = join(tmpdir(), `m15_sandbox_${Date.now()}.py`);

  try {
    writeFileSync(tmpPath, fullCode, "utf8");

    const stdout = execFileSync("python", [tmpPath], {
      timeout: timeoutMs,
      encoding: "utf8",
      stdio: ["pipe", "pipe", "pipe"],
      env: {
        PATH: process.env.PATH || "",
        PYTHONIOENCODING: "utf-8",
        SYSTEMROOT: process.env.SYSTEMROOT || "",
      },
    });

    return { stdout, stderr: "", returncode: 0 };
  } catch (err) {
    if (err.killed) {
      return {
        stdout: "",
        stderr: `SANDBOX ERROR: Execution timed out after ${timeoutMs}ms.`,
        returncode: -1,
      };
    }
    return {
      stdout: err.stdout || "",
      stderr: err.stderr || err.message,
      returncode: err.status || 1,
    };
  } finally {
    if (existsSync(tmpPath)) {
      try { unlinkSync(tmpPath); } catch { /* ignore */ }
    }
  }
}

// ---------------------------------------------------------------------------
// Tool definitions and execution
// ---------------------------------------------------------------------------

const TOOL_DEFINITIONS = [
  {
    name: "execute_python",
    description:
      "Write and execute Python code to analyze UCC filing data. " +
      "A variable called MOCK_FILINGS is pre-loaded — a list of dicts with keys: " +
      "filing_number, type, state, filing_date, expiration_date, status, " +
      "debtor_name, debtor_address, debtor_org_type, debtor_jurisdiction, " +
      "secured_party_name, secured_party_address, collateral_description. " +
      "Use print() to produce output. Standard library only.",
    input_schema: {
      type: "object",
      properties: {
        code: {
          type: "string",
          description:
            "Python code to execute. MOCK_FILINGS is pre-loaded. Use print() for output.",
        },
      },
      required: ["code"],
    },
  },
];

function executeTool(toolName, toolInput) {
  if (toolName !== "execute_python") {
    return JSON.stringify({ error: `Unknown tool: ${toolName}` });
  }

  const code = toolInput.code || "";
  if (!code.trim()) {
    return JSON.stringify({ error: "Empty code string provided." });
  }

  observeCode(code);

  const result = runInSandbox(code);
  observeExecution(result.stdout, result.stderr, result.returncode === 0);

  if (result.returncode === 0) {
    return result.stdout || "(no output — did you forget to print()?)";
  }
  return JSON.stringify({
    error: "Code execution failed",
    stderr: result.stderr,
    hint: "Read the error message, fix the code, and try again.",
  });
}

// ---------------------------------------------------------------------------
// System prompt
// ---------------------------------------------------------------------------

const SYSTEM_PROMPT = `You are a UCC filing data analyst agent. You analyze UCC (Uniform Commercial Code)
filing data by writing and executing Python code.

## Your Tool
You have one tool: execute_python. It runs Python code in a sandbox with a
pre-loaded variable called MOCK_FILINGS — a list of dicts with 11 UCC filings.

Each filing dict has these keys:
  filing_number, type, state, filing_date, expiration_date, status,
  debtor_name, debtor_address, debtor_org_type, debtor_jurisdiction,
  secured_party_name, secured_party_address, collateral_description

## How to Work
1. Write Python code that analyzes MOCK_FILINGS using the standard library
2. Always use print() to output results — that is the only way you can see them
3. If your code errors, read the error message and write corrected code
4. After getting results, incorporate the exact numbers into your final answer
5. Use collections.Counter, datetime, etc. from the standard library as needed

## Important Rules
- NEVER guess or make up numbers — always compute them with code
- Handle edge cases: some expiration_date values are None (null)
- Some debtor_name values may be empty strings
- Cite specific numbers from your code output in your final answer`;

// ---------------------------------------------------------------------------
// ReAct agent loop
// ---------------------------------------------------------------------------

const client = new Anthropic();
const MODEL = "claude-sonnet-4-6";

async function runCodeAgent(query, maxTurns = 5) {
  observe("QUERY", query);

  const messages = [{ role: "user", content: query }];

  for (let turn = 0; turn < maxTurns; turn++) {
    const response = await client.messages.create({
      model: MODEL,
      max_tokens: 4096,
      system: SYSTEM_PROMPT,
      tools: TOOL_DEFINITIONS,
      messages,
    });

    // STOP: Claude has a final answer
    if (response.stop_reason !== "tool_use") {
      const text = response.content
        .filter((b) => b.type === "text")
        .map((b) => b.text)
        .join("");
      observe(
        "RESPONSE",
        text.slice(0, 200) + (text.length > 200 ? "..." : "")
      );
      return text;
    }

    // CONTINUE: Claude wants to execute code
    const toolResults = [];
    for (const block of response.content) {
      if (block.type === "tool_use") {
        const resultStr = executeTool(block.name, block.input);
        toolResults.push({
          type: "tool_result",
          tool_use_id: block.id,
          content: resultStr,
        });
      } else if (block.type === "text" && block.text.trim()) {
        observeThinking(block.text);
      }
    }

    messages.push({ role: "assistant", content: response.content });
    messages.push({ role: "user", content: toolResults });
  }

  return "Agent did not produce a final response within the allowed turns.";
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------

console.log("=".repeat(60));
console.log("M15 Lab — Code Interpreter & Sandbox Execution (SOLUTION — JS)");
console.log("=".repeat(60));

console.log("\n\n>>> Query 1: Count filings by state");
const r1 = await runCodeAgent(
  "Count UCC filings by state and display the results as a table"
);
console.log(`\nFINAL ANSWER:\n${r1}`);

console.log("\n\n>>> Query 2: Blanket lien percentage");
const r2 = await runCodeAgent(
  "What percentage of filings are blanket liens " +
    "(collateral description contains 'all assets' or 'all accounts')?"
);
console.log(`\nFINAL ANSWER:\n${r2}`);

console.log("\n\n>>> Query 3: Debtor with most filings");
const r3 = await runCodeAgent(
  "Which debtor has the most filings? Show the debtor name and count."
);
console.log(`\nFINAL ANSWER:\n${r3}`);

console.log("\n\n>>> Query 4: Average filings per state");
const r4 = await runCodeAgent(
  "Calculate the average number of filings per state"
);
console.log(`\nFINAL ANSWER:\n${r4}`);
