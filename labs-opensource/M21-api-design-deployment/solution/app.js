/**
 * M21 Lab: Express Mirror — REFERENCE (Node.js)
 * ==============================================
 * Same structure as the FastAPI service: CORS, Bearer auth, health probe,
 * validated agent route, global error envelope.
 *
 * Setup: npm install express express-async-errors cors zod uuid openai
 * Run:   API_KEY=dev-secret-123 node app.js
 */

import "express-async-errors"; // patches async route handlers — import FIRST
import express from "express";
import cors from "cors";
import { randomUUID } from "node:crypto";
import { z } from "zod";
import OpenAI from "openai";

const API_KEY = process.env.API_KEY;
if (!API_KEY) throw new Error("API_KEY environment variable must be set");

const OLLAMA_HOST = process.env.OLLAMA_HOST ?? "http://localhost:11434";

// ── Contracts (Zod) ──────────────────────────────────────────
const AgentRequestSchema = z.object({
  query: z.string().min(1).max(4096).transform((s) => s.trim())
    .refine((s) => s.length > 0, "query must not be empty"),
  session_id: z.string().uuid().nullable().default(null),
  max_iterations: z.number().int().min(1).max(20).default(8),
  stream: z.boolean().default(false),
});

// ── Minimal agent (the API is the lesson, not the agent) ─────
const client = new OpenAI({ baseURL: `${OLLAMA_HOST}/v1`, apiKey: "ollama" });

const TOOLS = [{
  type: "function",
  function: {
    name: "calculate",
    description: "Evaluate a math expression. Use for any computation.",
    parameters: { type: "object", properties: { expression: { type: "string" } }, required: ["expression"] },
  },
}];

function runTool(name, args) {
  if (name === "calculate") {
    const expr = args.expression ?? "";
    if (!/^[0-9+\-*/.()% ]+$/.test(expr)) return JSON.stringify({ error: "invalid characters" });
    try {
      return JSON.stringify({ result: Function(`"use strict"; return (${expr})`)() });
    } catch (e) {
      return JSON.stringify({ error: e.message });
    }
  }
  return JSON.stringify({ error: `unknown tool ${name}` });
}

async function runAgent({ query, sessionId, maxIterations }) {
  const messages = [{ role: "user", content: query }];
  const toolRecords = [];

  for (let iteration = 1; iteration <= maxIterations; iteration++) {
    const response = await client.chat.completions.create({ model: "mistral", tools: TOOLS, messages });
    const choice = response.choices[0];
    const toolCalls = choice.message.tool_calls ?? [];

    if (choice.finish_reason === "stop" || !toolCalls.length) {
      return {
        result: choice.message.content ?? "",
        session_id: sessionId ?? randomUUID(),
        iterations: iteration,
        tool_calls: toolRecords,
        model: "mistral",
      };
    }

    messages.push({ role: "assistant", content: choice.message.content, tool_calls: toolCalls });
    for (const tc of toolCalls) {
      const args = JSON.parse(tc.function.arguments);
      const t0 = Date.now();
      const result = runTool(tc.function.name, args);
      toolRecords.push({
        tool_name: tc.function.name,
        input_summary: JSON.stringify(args).slice(0, 120),
        output_summary: result.slice(0, 120),
        duration_ms: Date.now() - t0,
      });
      messages.push({ role: "tool", tool_call_id: tc.id, content: result });
    }
  }
  return {
    result: "Max iterations reached.",
    session_id: sessionId ?? randomUUID(),
    iterations: maxIterations,
    tool_calls: toolRecords,
    model: "mistral",
  };
}

// ── App ──────────────────────────────────────────────────────
export const app = express();

app.use(cors({ origin: "*", methods: ["GET", "POST", "OPTIONS"] }));
app.use(express.json({ limit: "1mb" }));

// API key auth — health probe exempt (LBs don't carry tokens)
app.use((req, res, next) => {
  if (req.path === "/health") return next();
  const auth = req.headers["authorization"] ?? "";
  if (!auth.startsWith("Bearer ")) return res.status(401).json({ error: "Missing Bearer token" });
  if (auth.slice(7).trim() !== API_KEY) return res.status(401).json({ error: "Invalid API key" });
  next();
});

app.get("/health", async (req, res) => {
  let ollamaOk = false;
  try {
    const r = await fetch(`${OLLAMA_HOST}/api/tags`, { signal: AbortSignal.timeout(3000) });
    ollamaOk = r.ok;
  } catch { /* degraded */ }
  res.json({ status: ollamaOk ? "ok" : "degraded", ollama: ollamaOk, version: "1.0.0" });
});

app.post("/agent/run", async (req, res) => {
  const parsed = AgentRequestSchema.safeParse(req.body);
  if (!parsed.success) {
    return res.status(422).json({ error: "validation_error", detail: JSON.stringify(parsed.error.issues) });
  }
  const { query, session_id, max_iterations } = parsed.data;
  const start = Date.now();
  const resultData = await runAgent({ query, sessionId: session_id, maxIterations: max_iterations });
  return res.json({ ...resultData, latency_ms: Date.now() - start });
});

// Global error envelope — never leak a stack trace
app.use((err, req, res, _next) => {
  const requestId = req.headers["x-request-id"] ?? randomUUID();
  console.error(`[${requestId}] Unhandled error:`, err);
  res.status(500).json({
    error: "internal_server_error",
    detail: process.env.DEBUG ? err.message : undefined,
    request_id: requestId,
  });
});

const port = process.env.PORT ?? 8080;
app.listen(port, () => console.log(`Agent API listening on :${port}`));
