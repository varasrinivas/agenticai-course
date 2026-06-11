/**
 * M01 Lab - Step 2: System Prompt Experiment
 * ===========================================
 * Same user question, three different system prompts. Watch the persona change.
 * Run: node system_prompts.js
 */

import OpenAI from "openai";

const client = new OpenAI({ baseURL: "http://localhost:11434/v1", apiKey: "ollama" });

const SYSTEM_PROMPTS = [
  "You are a pirate. Respond in pirate speak.",
  "You are a formal academic. Use precise, scholarly language.",
  "Respond only in haiku format (5-7-5 syllables).",
];

const USER_QUESTION = "What is the moon?";

// TODO: For each systemPrompt of SYSTEM_PROMPTS:
// - Call client.chat.completions.create({ model: "mistral", messages: [...] })
//   IMPORTANT: the messages array must contain BOTH
//     { role: "system", content: systemPrompt }   ← this is the experiment!
//     { role: "user",   content: USER_QUESTION }
// - Print the system prompt and the response, separated by a blank line
// - try/catch around each call so one failure doesn't kill the loop
