/**
 * M15 Lab - Step 2: The Self-Debugging Code Agent (Node.js)
 * ==========================================================
 * Run: node code_agent.js
 */

import OpenAI from "openai";
import { SubprocessExecutor, toToolContent } from "./sandbox_executor.js";

const client = new OpenAI({ baseURL: "http://localhost:11434/v1", apiKey: "ollama" });

const EXECUTE_PYTHON_TOOL = {
  type: "function",
  function: {
    name: "execute_python",
    description:
      "Execute Python code in a sandbox and return stdout, stderr, and " +
      "exit_code. Use print() for any output you want to see.",
    parameters: {
      type: "object",
      properties: {
        code: { type: "string", description: "Complete, runnable Python code" },
        timeout_seconds: { type: "integer", description: "Max runtime (default 10)" },
      },
      required: ["code"],
    },
  },
};

const SYSTEM_PROMPT =
  "You are a data analysis assistant. When asked to compute something, " +
  "write complete Python code and call execute_python. Always import every " +
  "module you use. Print your final answer so it appears in stdout. If you " +
  "receive an error, read it carefully, fix the code, and call " +
  "execute_python again.";

class CodeExecutionAgent {
  constructor({ executor = null, model = "mistral", maxRetries = 3 } = {}) {
    // Executor is injected so a DockerExecutor can replace it without changes here
    this.executor = executor ?? new SubprocessExecutor();
    this.model = model;
    this.maxRetries = maxRetries;
  }

  /**
   * Run the agent, return the final answer string.
   *
   * TODO:
   * const messages = [{ role: "system", content: SYSTEM_PROMPT },
   *                   { role: "user", content: userRequest }];
   * let result = null;
   * For (attempt = 0; attempt <= this.maxRetries; attempt++):
   *   1. response = await client.chat.completions.create({ model: this.model,
   *        messages, tools: [EXECUTE_PYTHON_TOOL], tool_choice: "auto",
   *        temperature: 0.1 })   ← low temp = more deterministic code
   *      (try/catch → return `API error: ...`)
   *   2. const msg = response.choices[0].message;
   *   3. If (!msg.tool_calls?.length) return msg.content ?? "(no output)";
   *      ← some Ollama builds drop tool_choice silently; check tool_calls
   *   4. messages.push(msg);   ← assistant message FIRST, then results
   *   5. For each tc of msg.tool_calls:
   *      - const args = JSON.parse(tc.function.arguments);
   *      - result = await this.executor.run(args.code, args.timeout_seconds ?? 10);
   *      - log a short trace (first line of code + exitCode)
   *      - messages.push({ role: "tool", tool_call_id: tc.id,
   *                        content: toToolContent(result) });
   *   6. If (attempt === this.maxRetries && result && result.exitCode !== 0)
   *        return `Failed after ${this.maxRetries} attempts.\nLast error:\n${result.stderr}`;
   * After the loop: one final model call WITHOUT tools to summarize.
   */
  async run(userRequest) {
    // TODO: implement
  }
}

// ── Smoke test (COMPLETE) ──
const agent = new CodeExecutionAgent();

console.log("TEST 1: computation the model can't do in its head");
let answer = await agent.run("What is 3.7 to the power of 12? Show your work.");
console.log(`\nAgent answer: ${(answer ?? "").slice(0, 300)}`);

console.log("\nTEST 2: a task that usually needs a debug round");
answer = await agent.run(
  "Compute the 25th Fibonacci number and the sum of the first 25 Fibonacci numbers. Print both."
);
console.log(`\nAgent answer: ${(answer ?? "").slice(0, 300)}`);
