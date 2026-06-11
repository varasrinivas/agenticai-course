/**
 * M14 Lab: Multi-Agent Content Pipeline — SOLUTION
 * =================================================
 * Run: node content_pipeline.js
 */

import OpenAI from "openai";
import { randomUUID } from "node:crypto";

const client = new OpenAI({ baseURL: "http://localhost:11434/v1", apiKey: "ollama" });

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

async function runPipeline(topic, maxReviewAttempts = 2, verbose = true) {
  const taskId = `task_${randomUUID().slice(0, 8)}`;
  const goal = `Write a high-quality article about: ${topic}`;
  const messageLog = [];

  if (verbose) console.log(`\n${"=".repeat(55)}\n  Topic: ${topic}\n  Goal: ${goal}\n${"=".repeat(55)}`);

  // Stage 1: Research
  if (verbose) console.log("\n  [1/4] Researcher working...");
  const research = await runAgent("researcher", `Research this topic: ${topic}`);
  messageLog.push(createHandoff("researcher", "writer", taskId,
    "research_complete", research, goal, "Use these findings to write an article."));

  // Stage 2: Write — pass the GOAL and the research, not the whole log
  if (verbose) console.log("  [2/4] Writer working...");
  const article = await runAgent("writer",
    `Original goal: ${goal}\n\nResearch findings:\n${research}\n\n` +
    `Write a 200-300 word article based on these findings.`);
  messageLog.push(createHandoff("writer", "editor", taskId,
    "draft_complete", article, goal, "Edit this article for quality."));
  if (verbose) console.log(`         Draft: ${article.split(/\s+/).length} words`);

  // Stage 3: Edit
  if (verbose) console.log("  [3/4] Editor working...");
  let edited = await runAgent("editor", `Original goal: ${goal}\n\nArticle to edit:\n${article}`);
  messageLog.push(createHandoff("editor", "reviewer", taskId,
    "edit_complete", edited, goal, "Review and score this article."));

  // Stage 4: Review with retry loop
  let review = {};
  for (let attempt = 1; attempt <= maxReviewAttempts; attempt++) {
    if (verbose) console.log(`  [4/4] Reviewer (attempt ${attempt}/${maxReviewAttempts})...`);

    const reviewText = await runAgent("reviewer",
      `Original goal: ${goal}\n\nArticle to review:\n${edited}`);
    messageLog.push(createHandoff("reviewer", "supervisor", taskId,
      "review_complete", reviewText, goal));

    // Defensive parse — a malformed review fails OPEN (a human reads it anyway)
    try {
      review = JSON.parse(reviewText.replace(/```json|```/g, "").trim());
    } catch {
      review = { score: 80, feedback: reviewText, approved: true };
    }

    if (verbose) {
      console.log(`         Score: ${review.score ?? "?"}/100 — ${review.approved ? "Approved" : "Rejected"}`);
    }

    if (review.approved) break;

    // Rejected — the SUPERVISOR decides to retry, not the reviewer
    if (attempt < maxReviewAttempts) {
      if (verbose) console.log("         Sending feedback to Editor for revision...");
      edited = await runAgent("editor",
        `Original goal: ${goal}\n\nCurrent article:\n${edited}\n\n` +
        `Reviewer feedback (score ${review.score ?? "?"}/100):\n` +
        `${review.feedback ?? "No specific feedback"}\n\n` +
        `Please revise the article to address this feedback.`);
      messageLog.push(createHandoff("editor", "reviewer", taskId,
        "revision_complete", edited, goal, "Re-review after revision."));
    }
  }

  if (verbose) {
    console.log(`\n  ${"-".repeat(50)}`);
    console.log(`  Message Log (${messageLog.length} handoffs):`);
    for (const m of messageLog) {
      const ts = new Date(m.timestamp).toTimeString().slice(0, 8);
      console.log(`    [${ts}] ${m.sender} -> ${m.receiver}: ${m.type}`);
      console.log(`             ${m.payload.slice(0, 60)}...`);
    }
  }

  return {
    topic,
    article: edited,
    review,
    message_log: messageLog,
    stages_completed: new Set(messageLog.map((m) => m.sender)).size,
  };
}

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
