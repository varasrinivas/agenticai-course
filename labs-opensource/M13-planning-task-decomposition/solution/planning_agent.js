/**
 * M13 Lab: Planning Agent — SOLUTION
 * ===================================
 * Run: node planning_agent.js
 */

import OpenAI from "openai";

const client = new OpenAI({ baseURL: "http://localhost:11434/v1", apiKey: "ollama" });

function parseJson(raw) {
  return JSON.parse((raw ?? "").replace(/```json|```/g, "").trim());
}

// ── Part 1: Intent Classifier ────────────────────────────────
const CLASSIFY_SYSTEM =
  "Classify the user request. Respond with JSON only:\n" +
  '{"intent": "direct|research|multi_step", ' +
  '"complexity": "simple|moderate|complex", ' +
  '"needs_planning": true/false, ' +
  '"reason": "one sentence why"}';

async function classifyIntent(request) {
  try {
    const response = await client.chat.completions.create({
      model: "mistral",
      max_tokens: 256,
      messages: [
        { role: "system", content: CLASSIFY_SYSTEM },
        { role: "user", content: request },
      ],
    });
    return parseJson(response.choices[0].message.content);
  } catch {
    // Broken classifier degrades to "just answer it" — never crashes
    return { intent: "direct", complexity: "simple", needs_planning: false,
             reason: "Parse error, defaulting to direct" };
  }
}

// ── Task Decomposer ──────────────────────────────────────────
const DECOMPOSE_SYSTEM =
  "Decompose this goal into 3-7 sub-tasks. Respond with JSON only:\n" +
  '[{"id": "task_1", "description": "...", "depends_on": [], "tools_needed": ["search"]}, ...]' +
  "\n\nRules:\n- Each task achievable in 1-2 tool calls\n" +
  "- depends_on lists task IDs that must complete first\n" +
  "- Independent tasks: empty depends_on (they run in parallel)\n- NO circular dependencies";

async function decomposeTask(goal) {
  try {
    const response = await client.chat.completions.create({
      model: "mistral",
      max_tokens: 1024,
      messages: [
        { role: "system", content: DECOMPOSE_SYSTEM },
        { role: "user", content: `Goal: ${goal}` },
      ],
    });
    const tasks = parseJson(response.choices[0].message.content);
    if (!validateDag(tasks)) {
      console.log("  WARNING: cycle detected in task DAG — falling back to single task");
      return [{ id: "task_1", description: goal, depends_on: [], tools_needed: [] }];
    }
    return tasks;
  } catch {
    return [{ id: "task_1", description: goal, depends_on: [], tools_needed: [] }];
  }
}

// ── Part 2: DAG Validation (Kahn's topological sort) ─────────
function validateDag(tasks) {
  const inDegree = Object.fromEntries(tasks.map((t) => [t.id, (t.depends_on ?? []).length]));
  const deps = Object.fromEntries(tasks.map((t) => [t.id, new Set(t.depends_on ?? [])]));
  const queue = Object.entries(inDegree).filter(([, d]) => d === 0).map(([id]) => id);
  let visited = 0;
  while (queue.length) {
    const tid = queue.shift();
    visited++;
    for (const [otherId, otherDeps] of Object.entries(deps)) {
      if (otherDeps.has(tid)) {
        inDegree[otherId]--;
        if (inDegree[otherId] === 0) queue.push(otherId);
      }
    }
  }
  return visited === tasks.length; // fewer visited => a cycle exists
}

// ── Task Executor (simulated) ────────────────────────────────
async function executeTask(task) {
  await new Promise((r) => setTimeout(r, 500));
  return { task_id: task.id, status: "completed", result: `Completed: ${task.description.slice(0, 60)}` };
}

// ── Part 3: DAG Executor ─────────────────────────────────────
async function executeDag(tasks, verbose = true) {
  const completed = {};
  const failed = new Set();
  const results = [];
  const remaining = new Map(tasks.map((t) => [t.id, t]));
  let wave = 0;

  while (remaining.size) {
    wave++;
    const ready = [...remaining.values()].filter(
      (t) =>
        (t.depends_on ?? []).every((d) => d in completed) &&
        !(t.depends_on ?? []).some((d) => failed.has(d))
    );

    if (!ready.length) {
      // Deadlock guard: everything left is blocked by failures
      for (const tid of remaining.keys()) {
        results.push({ task_id: tid, status: "blocked", result: "Blocked by failed dependency" });
      }
      break;
    }

    if (verbose) {
      const mode = ready.length > 1 ? "PARALLEL" : "SEQUENTIAL";
      console.log(`    Wave ${wave} [${mode}]: ${JSON.stringify(ready.map((t) => t.id))}`);
    }

    const waveResults = await Promise.allSettled(ready.map(executeTask));

    ready.forEach((task, i) => {
      const settled = waveResults[i];
      if (settled.status === "rejected") {
        failed.add(task.id);
        results.push({ task_id: task.id, status: "failed", result: String(settled.reason) });
      } else {
        completed[task.id] = settled.value;
        results.push(settled.value);
      }
      remaining.delete(task.id);
    });
  }

  return results;
}

// ── Visualization + Pipeline ─────────────────────────────────
function printPlan(tasks, results = null) {
  const statusMap = Object.fromEntries((results ?? []).map((r) => [r.task_id, r.status]));
  console.log("\n  Execution Plan:");
  for (const t of tasks) {
    const status = statusMap[t.id] ?? "pending";
    const icon = { completed: "[done]", failed: "[FAIL]", blocked: "[blocked]" }[status] ?? "[ .. ]";
    const deps = t.depends_on?.length ? ` (after: ${t.depends_on.join(", ")})` : " (no deps)";
    console.log(`    ${icon} ${t.id}: ${t.description.slice(0, 50)}${deps}`);
  }
}

async function planningPipeline(request, verbose = true) {
  if (verbose) console.log(`\n${"=".repeat(55)}\n  Request: ${request}\n${"=".repeat(55)}`);

  const classification = await classifyIntent(request);
  if (verbose) {
    console.log(`\n  Classification: ${classification.intent} (${classification.complexity})`);
    console.log(`     Needs planning: ${classification.needs_planning} — ${classification.reason}`);
  }

  if (!classification.needs_planning) {
    if (verbose) console.log("  -> Routing to direct answer (no planning overhead)");
    const response = await client.chat.completions.create({
      model: "mistral", max_tokens: 1024,
      messages: [{ role: "user", content: request }],
    });
    return response.choices[0].message.content;
  }

  if (verbose) console.log("\n  Decomposing into sub-tasks...");
  const tasks = await decomposeTask(request);
  if (verbose) {
    printPlan(tasks);
    console.log(`\n  Executing ${tasks.length} tasks...`);
  }

  const start = Date.now();
  const results = await executeDag(tasks, verbose);
  const elapsed = (Date.now() - start) / 1000;

  if (verbose) {
    printPlan(tasks, results);
    const done = results.filter((r) => r.status === "completed").length;
    console.log(`\n  Completed ${done}/${tasks.length} tasks in ${elapsed.toFixed(1)}s`);
  }

  const resultText = results.map((r) => `- ${r.task_id}: ${r.result}`).join("\n");
  const response = await client.chat.completions.create({
    model: "mistral", max_tokens: 1024,
    messages: [{ role: "user", content:
      `Original request: ${request}\n\nSub-task results:\n${resultText}\n\nSynthesize a final answer from these results.` }],
  });
  return response.choices[0].message.content;
}

// ── Tests ────────────────────────────────────────────────────
console.log("\n> TEST 1: Simple task (should skip planning)");
const r1 = await planningPipeline("What is 2 + 2?");
console.log(`\n  Answer: ${r1.slice(0, 120)}`);

console.log("\n> TEST 2: Complex task (planning + execution)");
const r2 = await planningPipeline(
  "Research the top 3 AI agent frameworks, compare their features, and draft a recommendation for a startup team."
);
console.log(`\n  Answer: ${r2.slice(0, 200)}...`);

console.log("\n> TEST 3: DAG validation (pure algorithm)");
console.log(`  Valid DAG (expect true):    ${validateDag([
  { id: "a", depends_on: [] }, { id: "b", depends_on: ["a"] },
  { id: "c", depends_on: ["a"] }, { id: "d", depends_on: ["b", "c"] },
])}`);
console.log(`  Cyclic DAG (expect false):  ${validateDag([
  { id: "a", depends_on: ["c"] }, { id: "b", depends_on: ["a"] }, { id: "c", depends_on: ["b"] },
])}`);
