/**
 * M03 Lab - Step 2: Compare Prompt Patterns
 * ==========================================
 * Zero-shot vs few-shot vs chain-of-thought on the same buggy code.
 * Run: node pattern_compare.js
 */

import OpenAI from "openai";

const client = new OpenAI({ baseURL: "http://localhost:11434/v1", apiKey: "ollama" });

// Buggy code to review (COMPLETE) — contains: `!= None` instead of `is None`,
// unnecessary range(len(...)), no handling of non-string items
const CODE = `def process_items(items):
    result = []
    for i in range(len(items)):
        if items[i] != None:
            result.append(items[i].upper())
    return result`;

// TODO: Build an object `patterns` with three prompts:
// "zero-shot"        — `Review this Python code for issues:\n\`\`\`python\n${CODE}\n\`\`\``
// "few-shot"         — two example reviews first, e.g.:
//                        Code: `x = x + 1` → Style: Use `x += 1`.
//                        Code: `if x == None` → Bug: Use `is None`.
//                      ...then "Now review this code:" + CODE
// "chain-of-thought" — "Review this Python code step by step:" + CODE +
//                      numbered steps: 1. bugs 2. performance 3. style 4. summarize
const patterns = {};

// TODO: For each [name, prompt] of Object.entries(patterns):
// - Call client.chat.completions.create({ model: "mistral",
//     messages: [{ role: "user", content: prompt }] })
// - Print a separator, the pattern name, token usage
//   (usage.prompt_tokens / usage.completion_tokens), and the first ~300
//   characters of the response
// - try/catch per pattern
