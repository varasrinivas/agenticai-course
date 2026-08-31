/**
 * M01 Lab - Step 5 (Stretch): CLI Chat with History — SOLUTION
 * =============================================================
 * Run: node chat_cli.js   (type 'quit' to exit)
 */

import OpenAI from "openai";
import * as readline from "node:readline/promises";

const client = new OpenAI({ baseURL: "http://localhost:11434/v1", apiKey: "ollama" });
const rl = readline.createInterface({ input: process.stdin, output: process.stdout });

const conversation = [];

console.log("Chat with Mistral! (type 'quit' to exit)\n");

while (true) {
  // Stop if stdin has ended. Redirecting input (or Ctrl-D) closes readline, and
  // asking again then throws ERR_USE_AFTER_CLOSE instead of exiting cleanly --
  // you only see it when the chat is not driven by a person typing.
  if (rl.closed) break;

  let userInput;
  try {
    userInput = (await rl.question("You: ")).trim();
  } catch {
    break;                      // stream closed mid-prompt
  }

  if (["quit", "exit"].includes(userInput.toLowerCase())) {
    rl.close();
    break;
  }
  if (!userInput) continue;

  conversation.push({ role: "user", content: userInput });

  try {
    const response = await client.chat.completions.create({
      model: "mistral",
      messages: [
        { role: "system", content: "You are a friendly, helpful assistant." },
        ...conversation,
      ],
    });
    const assistantMsg = response.choices[0].message.content;
    conversation.push({ role: "assistant", content: assistantMsg });
    console.log(`\nMistral: ${assistantMsg}\n`);
  } catch (error) {
    console.error(`\nError: ${error.message}\n`);
    // Remove the failed user message so conversation stays consistent
    conversation.pop();
  }
}
