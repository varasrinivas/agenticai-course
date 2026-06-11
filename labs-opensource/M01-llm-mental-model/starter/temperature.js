/**
 * M01 Lab - Step 3: Temperature Experiment
 * =========================================
 * Same prompt at temperature 0.0 and 1.0, three runs each.
 * Run: node temperature.js
 */

import OpenAI from "openai";

const client = new OpenAI({ baseURL: "http://localhost:11434/v1", apiKey: "ollama" });

const PROMPT = "Write a one-sentence description of the moon.";

// TODO: For temp of [0.0, 1.0]:
//   Print a header like "--- Temperature 0 ---"
//   For run i = 1..3:
//     - Call client.chat.completions.create({ model: "mistral", temperature: temp,
//         messages: [{ role: "user", content: PROMPT }] })
//     - Print `  Run ${i}: ${response text}`
//     - try/catch around each call
//
// What to observe: temp 0.0 → (nearly) identical runs; temp 1.0 → three different ones.
