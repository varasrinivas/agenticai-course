/**
 * M00 Lab - Step 2: Your First Local Model Call
 * ==============================================
 * Complete the TODO below to send a message to Mistral-7B running in Ollama.
 * Run: node hello_mistral.js
 */

import OpenAI from "openai";

// Connect to Ollama running on localhost.
// apiKey: "ollama" is a placeholder — Ollama doesn't need a real key.
const client = new OpenAI({ baseURL: "http://localhost:11434/v1", apiKey: "ollama" });

console.log("Connecting to local Mistral-7B via Ollama...");
console.log("-".repeat(50));

// TODO: Use client.chat.completions.create() to send a message to Mistral
// - model: "mistral"
// - messages: a system message ("You are a helpful assistant. Be concise.")
//             and a user message ("In exactly one sentence, what is a large language model?")
// Then print:
//   1. The response text  — response.choices[0].message.content
//   2. The token usage    — response.usage.prompt_tokens and response.usage.completion_tokens
// Wrap the call in try/catch and print troubleshooting hints on failure
// (is Ollama running? is mistral pulled?).
