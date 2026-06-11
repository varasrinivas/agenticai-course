/**
 * M01 Lab - Step 2: System Prompt Experiment — SOLUTION
 * ======================================================
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

for (const systemPrompt of SYSTEM_PROMPTS) {
  try {
    const response = await client.chat.completions.create({
      model: "mistral",
      messages: [
        { role: "system", content: systemPrompt }, // the experiment variable
        { role: "user", content: USER_QUESTION },
      ],
    });
    console.log(`System: ${systemPrompt}`);
    console.log(`Response: ${response.choices[0].message.content}\n`);
  } catch (error) {
    console.error(`Error: ${error.message}`);
  }
}
