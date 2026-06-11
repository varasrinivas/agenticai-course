/**
 * M14 Lab: Multi-Agent Content Pipeline
 * ======================================
 * Researcher → Writer → Editor → Reviewer, orchestrated by a supervisor.
 * Run: node content_pipeline.js
 */

import OpenAI from "openai";
import { randomUUID } from "node:crypto";

const client = new OpenAI({ baseURL: "http://localhost:11434/v1", apiKey: "ollama" });

// ── Handoff Message Structure (COMPLETE) ─────────────────────
export function createHandoff(sender, receiver, taskId, msgType, payload, goal, instructions = "") {
  return {
    id: `msg_${randomUUID().slice(0, 8)}`,
    sender,
    receiver,
    task_id: taskId,
    type: msgType,
    payload,
    original_goal: goal, // travels with EVERY message — prevents pipeline drift
    instructions,
    timestamp: Date.now(),
  };
}

// ── Specialized Agents (COMPLETE) ────────────────────────────
const AGENT_PROMPTS = {
  researcher:
    "You are a research specialist. Given a topic, produce a concise " +
    "research brief with 3-5 key findings, each with a source reference. " +
    "Focus on facts and data points. Output structured markdown.",
  writer:
    "You are a professional writer. Given research findings, write a " +
    "well-structured article of 200-300 words. Use clear language, " +
    "include an introduction and conclusion. Incorporate the research " +
    "findings naturally with citations.",
  editor:
    "You are an experienced editor. Review the article for clarity, " +
    "grammar, flow, and factual consistency. Make direct edits (don't " +
    "just suggest changes). Return the improved article.",
  reviewer:
    "You are a quality reviewer. Score the article 0-100 on:\n" +
    "- Accuracy (0-25)\n- Clarity (0-25)\n- Completeness (0-25)\n- Engagement (0-25)\n\n" +
    'Respond with JSON: {"score": N, "feedback": "...", "approved": true/false}\n' +
    "Approve only if total score >= 75.",
};

/** (COMPLETE) Run a single specialized agent. */
async function runAgent(agentName, content) {
  const response = await client.chat.completions.create({
    model: "mistral",
    messages: [
      { role: "system", content: AGENT_PROMPTS[agentName] },
      { role: "user", content },
    ],
  });
  return response.choices[0].message.content;
}

// ── Supervisor (YOUR JOB) ────────────────────────────────────
/**
 * Orchestrate the 4-agent content pipeline with retry on rejection.
 *
 * TODO:
 * const taskId = `task_${randomUUID().slice(0, 8)}`;
 * const goal = `Write a high-quality article about: ${topic}`;
 * const messageLog = [];
 *
 * Stage 1 — RESEARCH:
 *   const research = await runAgent("researcher", `Research this topic: ${topic}`);
 *   messageLog.push(createHandoff("researcher", "writer", taskId,
 *     "research_complete", research, goal, "Use these findings to write an article."));
 *
 * Stage 2 — WRITE (pass the GOAL and the research, not the whole log):
 *   const article = await runAgent("writer",
 *     `Original goal: ${goal}\n\nResearch findings:\n${research}\n\n` +
 *     `Write a 200-300 word article based on these findings.`);
 *   log a writer→editor handoff
 *
 * Stage 3 — EDIT:
 *   let edited = await runAgent("editor", `Original goal: ${goal}\n\nArticle to edit:\n${article}`);
 *   log an editor→reviewer handoff
 *
 * Stage 4 — REVIEW with retry loop, attempt = 1..maxReviewAttempts:
 *   const reviewText = await runAgent("reviewer",
 *     `Original goal: ${goal}\n\nArticle to review:\n${edited}`);
 *   log a reviewer→supervisor handoff
 *   Parse DEFENSIVELY (strip ``` fences before JSON.parse):
 *     on failure: review = { score: 80, feedback: reviewText, approved: true }
 *     ← a malformed review fails OPEN here; a human reads the article anyway
 *   If review.approved: break
 *   If rejected and attempts remain: edited = await runAgent("editor",
 *     goal + current article + reviewer feedback + "revise to address this")
 *     and log the revision handoff
 *
 * If verbose: log each stage, then the message timeline
 *   `[HH:MM:SS] sender -> receiver: type / payload.slice(0, 60)`
 *
 * Return { topic, article: edited, review, message_log: messageLog,
 *          stages_completed: new Set(messageLog.map((m) => m.sender)).size };
 */
async function runPipeline(topic, maxReviewAttempts = 2, verbose = true) {
  // TODO: implement
}

// ── Tests (COMPLETE) ─────────────────────────────────────────
console.log("\n> TEST 1: Full content pipeline (4-6 model calls, be patient on CPU)");
const result = await runPipeline("The benefits of walking 30 minutes daily");
console.log(`\n  Final article (${result.article.split(/\s+/).length} words):`);
console.log(`  ${result.article.slice(0, 200)}...`);
console.log(`  Review score: ${result.review.score ?? "?"}/100`);
console.log(`  Total handoffs: ${result.message_log.length}`);

console.log(`\n${"=".repeat(55)}`);
console.log("> TEST 2: Individual agent test (Researcher only)");
const research = await runAgent("researcher", "Research: impact of AI on healthcare");
console.log(`  Research output: ${research.slice(0, 200)}...`);
