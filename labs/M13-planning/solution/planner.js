/**
 * M13 Lab — Planning & Task Decomposition (Solution)
 * ====================================================
 * Node.js planning agent that decomposes a goal into sub-tasks,
 * executes them as a DAG, and synthesizes a structured report.
 *
 * Usage:
 *     node planner.js
 *     node planner.js "Generate a complete risk report for Acme Corporation"
 */

import Anthropic from "@anthropic-ai/sdk";
import { config } from "dotenv";
import { dirname, join } from "path";
import { fileURLToPath } from "url";

config();

const __dirname = dirname(fileURLToPath(import.meta.url));
const mockDataPath = join(__dirname, "..", "..", "shared", "mock_ucc_data.js");
const { searchFilings, getFilingByNumber } = await import(mockDataPath);

const client = new Anthropic();
const MODEL = "claude-sonnet-4-6";

// =============================================================================
// LOGGING HELPERS
// =============================================================================

function logPhase(phase, message) {
  console.log(`\n${"=".repeat(60)}`);
  console.log(`[${phase}] ${message}`);
  console.log("=".repeat(60));
}

function logTask(taskId, message) {
  console.log(`\n${"─".repeat(60)}`);
  console.log(`  [${taskId}] ${message}`);
  console.log("─".repeat(60));
}

function logDetail(message) {
  console.log(`    ${message}`);
}

// =============================================================================
// TOOL DEFINITIONS
// =============================================================================

const TOOL_DEFINITIONS = [
  {
    name: "search_filings",
    description:
      "Search UCC filings by debtor name and/or state. Returns matching filings with key details.",
    input_schema: {
      type: "object",
      properties: {
        debtor_name: {
          type: "string",
          description: "Full or partial debtor (company) name",
        },
        state: {
          type: "string",
          description: "US state to filter results",
        },
      },
      required: [],
    },
  },
  {
    name: "get_filing_details",
    description:
      "Get full details of a specific UCC filing by its filing number.",
    input_schema: {
      type: "object",
      properties: {
        filing_number: {
          type: "string",
          description: "The UCC filing number",
        },
      },
      required: ["filing_number"],
    },
  },
  {
    name: "calculate_risk",
    description:
      "Calculate a risk profile for a debtor based on their UCC filings.",
    input_schema: {
      type: "object",
      properties: {
        debtor_name: {
          type: "string",
          description: "The debtor name to assess risk for",
        },
      },
      required: ["debtor_name"],
    },
  },
];

// =============================================================================
// TOOL EXECUTION
// =============================================================================

function calculateRiskForDebtor(debtorName) {
  const filings = searchFilings({ debtorName });
  if (filings.length === 0) {
    return {
      debtor: debtorName,
      risk_score: 0,
      risk_level: "UNKNOWN",
      message: `No filings found for '${debtorName}'`,
    };
  }
  const active = filings.filter((f) => f.status === "Active");
  const blanket = filings.filter(
    (f) =>
      f.collateral_description.toLowerCase().includes("all assets") ||
      f.collateral_description.toLowerCase().includes("all accounts")
  );
  const amendments = filings.filter((f) => f.type === "UCC-3");
  const score = Math.min(
    1.0,
    active.length * 0.25 + blanket.length * 0.3 + amendments.length * 0.1
  );

  let level, rec;
  if (score >= 0.7) {
    level = "HIGH";
    rec =
      "Significant lien exposure. Detailed due diligence recommended before extending credit.";
  } else if (score >= 0.4) {
    level = "MEDIUM";
    rec =
      "Moderate lien activity. Review collateral descriptions and secured party priorities.";
  } else {
    level = "LOW";
    rec = "Limited lien exposure. Standard credit procedures should suffice.";
  }

  return {
    debtor: debtorName,
    risk_score: Math.round(score * 100) / 100,
    risk_level: level,
    total_filings: filings.length,
    active_filings: active.length,
    blanket_liens: blanket.length,
    amendments: amendments.length,
    recommendation: rec,
    factors: [
      `${active.length} active filing(s)`,
      `${blanket.length} blanket lien(s) covering all assets`,
      `${amendments.length} amendment(s) on file`,
    ],
  };
}

function executeTool(toolName, toolInput) {
  try {
    if (toolName === "search_filings") {
      const results = searchFilings({
        debtorName: toolInput.debtor_name,
        state: toolInput.state,
      });
      return JSON.stringify(
        results.map((f) => ({
          filing_number: f.filing_number,
          debtor: f.debtor.name,
          secured_party: f.secured_party.name,
          state: f.state,
          status: f.status,
          type: f.type,
          collateral: f.collateral_description.slice(0, 120) + "...",
        })),
        null,
        2
      );
    } else if (toolName === "get_filing_details") {
      const filing = getFilingByNumber(toolInput.filing_number);
      if (filing) return JSON.stringify(filing, null, 2);
      return JSON.stringify({ error: `Filing ${toolInput.filing_number} not found` });
    } else if (toolName === "calculate_risk") {
      return JSON.stringify(
        calculateRiskForDebtor(toolInput.debtor_name),
        null,
        2
      );
    }
    return JSON.stringify({ error: `Unknown tool: ${toolName}` });
  } catch (e) {
    return JSON.stringify({ error: `Tool execution failed: ${e.message}` });
  }
}

// =============================================================================
// PHASE 1: CREATE PLAN
// =============================================================================

const AVAILABLE_TOOLS_DESC = `
Available tools (each task must use exactly one):
1. search_filings(debtor_name?, state?) — Search UCC filings by debtor name and/or state
2. get_filing_details(filing_number) — Get full details of a specific UCC filing
3. calculate_risk(debtor_name) — Calculate risk profile for a debtor based on their filings
`;

async function createPlan(goal) {
  logPhase("PLAN", `Decomposing goal: ${goal}`);

  const planningPrompt = `You are a task planning agent. Your job is to decompose a research goal
into a series of sub-tasks that can be executed using available tools.

${AVAILABLE_TOOLS_DESC}

Rules:
- Each task must use exactly ONE of the available tools.
- Tasks can depend on other tasks (specify by task ID).
- A task will receive the results of its dependencies as context.
- Order tasks so dependencies come first.
- Keep the plan focused — typically 3-5 tasks for a research goal.
- Do NOT include a final "synthesize" or "write report" task — that is handled separately.

Output ONLY a valid JSON array of task objects. No explanation, no markdown fences.
Each task object must have these fields:
  "id": "task_1" (incrementing),
  "description": "what the task does",
  "tool": "tool_name",
  "depends_on": ["task_ids"]

Example for "Research filings for XYZ Corp":
[
  {"id": "task_1", "description": "Search for UCC filings for XYZ Corp", "tool": "search_filings", "depends_on": []},
  {"id": "task_2", "description": "Get detailed information for each filing found", "tool": "get_filing_details", "depends_on": ["task_1"]},
  {"id": "task_3", "description": "Calculate risk profile for XYZ Corp", "tool": "calculate_risk", "depends_on": ["task_1"]}
]`;

  try {
    const response = await client.messages.create({
      model: MODEL,
      max_tokens: 1024,
      system: planningPrompt,
      messages: [{ role: "user", content: goal }],
    });

    let text = response.content[0].text.trim();

    // Strip markdown code fences if present
    if (text.startsWith("```")) {
      text = text.split("\n").slice(1).join("\n").split("```")[0].trim();
    }

    const tasksData = JSON.parse(text);

    const tasks = tasksData.map((t) => ({
      id: t.id,
      description: t.description,
      tool: t.tool,
      dependsOn: t.depends_on || [],
      status: "pending",
      result: null,
    }));

    logDetail(`Created ${tasks.length} tasks:`);
    for (const t of tasks) {
      const deps = t.dependsOn.length
        ? ` (after ${t.dependsOn.join(", ")})`
        : " (no deps)";
      logDetail(`  ${t.id}: ${t.description} [tool=${t.tool}]${deps}`);
    }

    return tasks;
  } catch (e) {
    logDetail(`Planning failed: ${e.message}`);
    return [];
  }
}

// =============================================================================
// PHASE 2: EXECUTE PLAN
// =============================================================================

async function executeTask(task, context) {
  logTask(task.id, `Executing: ${task.description}`);

  // Build context from dependencies
  const contextParts = [];
  for (const depId of task.dependsOn) {
    if (context[depId]) {
      let depResult = context[depId];
      if (depResult.length > 2000) {
        depResult = depResult.slice(0, 2000) + "\n... (truncated)";
      }
      contextParts.push(`Results from ${depId}:\n${depResult}`);
    }
  }
  const contextStr =
    contextParts.length > 0 ? contextParts.join("\n\n") : "No prior context.";

  const userMessage =
    `Task: ${task.description}\n\n` +
    `Context from previous tasks:\n${contextStr}\n\n` +
    `Use the ${task.tool} tool to complete this task. ` +
    `If you need a specific parameter from the context (like a filing number), ` +
    `extract it from the context above. Return the raw tool results.`;

  const messages = [{ role: "user", content: userMessage }];

  // Mini ReAct loop for this task
  for (let turn = 0; turn < 5; turn++) {
    let response;
    try {
      response = await client.messages.create({
        model: MODEL,
        max_tokens: 2048,
        tools: TOOL_DEFINITIONS,
        messages,
      });
    } catch (e) {
      logDetail(`API call failed: ${e.message}`);
      return JSON.stringify({ error: `API call failed: ${e.message}` });
    }

    // If Claude is done, return text
    if (response.stop_reason !== "tool_use") {
      let finalText = "";
      for (const block of response.content) {
        if (block.type === "text") finalText += block.text;
      }
      logDetail(`Task produced text response (${finalText.length} chars)`);
      return finalText;
    }

    // Process tool calls
    const toolResults = [];
    for (const block of response.content) {
      if (block.type === "tool_use") {
        logDetail(`Tool call: ${block.name}(${JSON.stringify(block.input)})`);
        const result = executeTool(block.name, block.input);
        logDetail(
          `Tool result: ${result.slice(0, 200)}${result.length > 200 ? "..." : ""}`
        );
        toolResults.push({
          type: "tool_result",
          tool_use_id: block.id,
          content: result,
        });
      }
    }

    messages.push({ role: "assistant", content: response.content });
    messages.push({ role: "user", content: toolResults });
  }

  return JSON.stringify({ error: "Task did not complete within max turns" });
}

async function executePlan(tasks) {
  logPhase("EXECUTE", `Running ${tasks.length} tasks in dependency order`);

  const results = {};
  const completedIds = new Set();
  const failedIds = new Set();

  const maxIterations = tasks.length + 1;
  for (let iteration = 0; iteration < maxIterations; iteration++) {
    // Mark tasks with failed dependencies as failed
    const toFail = tasks.filter(
      (t) =>
        t.status === "pending" &&
        t.dependsOn.some((d) => failedIds.has(d))
    );
    for (const t of toFail) {
      t.status = "failed";
      failedIds.add(t.id);
      logTask(t.id, "SKIPPED — dependency failed");
    }

    // Find ready tasks
    const ready = tasks.filter(
      (t) =>
        t.status === "pending" &&
        t.dependsOn.every((d) => completedIds.has(d))
    );

    if (ready.length === 0) break;

    // Execute ready tasks sequentially
    for (const t of ready) {
      t.status = "running";
      try {
        const result = await executeTask(t, results);
        t.status = "completed";
        t.result = result;
        results[t.id] = result;
        completedIds.add(t.id);
        logTask(t.id, "COMPLETED");
      } catch (e) {
        t.status = "failed";
        failedIds.add(t.id);
        logTask(t.id, `FAILED: ${e.message}`);
      }
    }
  }

  logDetail(
    `Execution complete: ${completedIds.size} completed, ${failedIds.size} failed`
  );

  return results;
}

// =============================================================================
// PHASE 3: SYNTHESIZE REPORT
// =============================================================================

async function synthesizeReport(goal, tasks, results) {
  logPhase("REPORT", "Synthesizing final report");

  let resultsText = "";
  for (const task of tasks) {
    if (task.status === "completed" && task.result) {
      resultsText += `\n### ${task.description}\n${task.result}\n`;
    }
  }

  if (!resultsText.trim()) {
    return "No task results available to synthesize. All tasks may have failed.";
  }

  const userMessage =
    `Original research goal: ${goal}\n\n` +
    `Research results from completed tasks:\n${resultsText}\n\n` +
    `Write a structured risk report with these sections:\n` +
    `1. **Executive Summary** — One paragraph overview of findings\n` +
    `2. **Filing Details** — List each filing found with key details ` +
    `(filing number, parties, collateral, status, dates)\n` +
    `3. **Risk Assessment** — Risk score, risk level, and contributing factors\n` +
    `4. **Recommendation** — Clear next steps based on the findings\n\n` +
    `Use specific data from the research results. ` +
    `If some data was not found (e.g., no filings for the entity), note that clearly. ` +
    `Be concise and professional.`;

  try {
    const response = await client.messages.create({
      model: MODEL,
      max_tokens: 2048,
      messages: [{ role: "user", content: userMessage }],
    });

    let report = "";
    for (const block of response.content) {
      if (block.type === "text") report += block.text;
    }
    return report;
  } catch (e) {
    return `Report synthesis failed: ${e.message}`;
  }
}

// =============================================================================
// MAIN
// =============================================================================

async function runPlanningAgent(goal) {
  logPhase("START", "Planning agent initialized");
  logDetail(`Goal: ${goal}`);

  // Phase 1
  const tasks = await createPlan(goal);
  if (tasks.length === 0) {
    return "Failed to create a plan. Check API key and model availability.";
  }

  // Phase 2
  const results = await executePlan(tasks);

  // Phase 3
  const report = await synthesizeReport(goal, tasks, results);

  // Summary
  logPhase("DONE", "Planning agent complete");
  const completed = tasks.filter((t) => t.status === "completed").length;
  const failed = tasks.filter((t) => t.status === "failed").length;
  logDetail(`Tasks: ${completed} completed, ${failed} failed, ${tasks.length} total`);

  return report;
}

// Run
const goal =
  process.argv.slice(2).join(" ") ||
  "Generate a complete risk report for Acme Corporation";

console.log("=".repeat(60));
console.log("M13 Lab — Planning & Task Decomposition (SOLUTION)");
console.log("=".repeat(60));

const report = await runPlanningAgent(goal);

console.log(`\n${"=".repeat(60)}`);
console.log("FINAL REPORT");
console.log("=".repeat(60));
console.log(report);
