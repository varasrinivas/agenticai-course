/**
 * M03 Lab - Step 1: Code Review System Prompt
 * ============================================
 * Write a structured system prompt and test it on code with a real vulnerability.
 * Run: node review_agent.js
 */

import OpenAI from "openai";

const client = new OpenAI({ baseURL: "http://localhost:11434/v1", apiKey: "ollama" });

// TODO: Write a system prompt with four labeled sections:
// <role>            — senior software engineer reviewing for correctness,
//                     performance, security, and style
// <review_criteria> — name concrete things to check: logic errors, injection
//                     risks, hardcoded secrets, naming, missing docstrings...
// <output_format>   — "## [Category]" headers, **Issue**/**Fix** bullets,
//                     omit categories with no findings
// <tone>            — constructive and specific; praise good patterns
const REVIEW_SYSTEM_PROMPT = `...`;

// Test code with a deliberate SQL injection vulnerability (COMPLETE)
const testCode = `def get_user(id):
    query = f"SELECT * FROM users WHERE id = {id}"
    return db.execute(query)`;

// TODO: Send the review request:
// - messages: [{ role: "system", content: REVIEW_SYSTEM_PROMPT },
//              { role: "user", content: `Review this code:\n\`\`\`python\n${testCode}\n\`\`\`` }]
// - Print the response and token usage (usage.prompt_tokens / usage.completion_tokens)
// - try/catch with a helpful error message
//
// Success check: the response must flag the f-string SQL injection.
// If it doesn't, make <review_criteria> more explicit and re-run.
