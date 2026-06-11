/**
 * M01 Lab - Step 1: Your First Chat Completion
 * =============================================
 * Run: node first_call.js
 */

import OpenAI from "openai";

const client = new OpenAI({ baseURL: "http://localhost:11434/v1", apiKey: "ollama" });

console.log("--- First Local Model Call ---\n");

// TODO: Use client.chat.completions.create() to ask Mistral a question.
// - model: "mistral"
// - messages:
//     system: "You are a helpful assistant who explains things clearly."
//     user:   "What is a large language model? Explain in 2 sentences."
// Print the response text (response.choices[0].message.content) and the
// usage line: `Tokens used: ${usage.prompt_tokens} in, ${usage.completion_tokens} out`
// Wrap in try/catch — on failure, remind the user to run `ollama serve`.
