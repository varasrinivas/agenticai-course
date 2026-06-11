/**
 * M01 Lab - Step 5 (Stretch): CLI Chat with History
 * ==================================================
 * A terminal chat loop that resends the FULL conversation every turn.
 * Run: node chat_cli.js   (type 'quit' to exit)
 */

import OpenAI from "openai";
import * as readline from "node:readline/promises";

const client = new OpenAI({ baseURL: "http://localhost:11434/v1", apiKey: "ollama" });
const rl = readline.createInterface({ input: process.stdin, output: process.stdout });

const conversation = [];

console.log("Chat with Mistral! (type 'quit' to exit)\n");

// TODO: Build the chat loop:
// while (true):
//   1. const userInput = (await rl.question("You: ")).trim();
//   2. Exit on "quit"/"exit" (rl.close() then break); skip empty input
//   3. conversation.push({ role: "user", content: userInput });
//   4. Call the model with [system message, ...conversation]
//      (system: "You are a friendly, helpful assistant.")
//   5. Push the assistant reply onto conversation and print it
//   6. On API error: print the error AND conversation.pop() — remove the
//      failed user message so the history stays consistent
