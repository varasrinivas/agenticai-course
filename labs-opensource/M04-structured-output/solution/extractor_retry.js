/**
 * M04 Lab - Step 3: Retry with Error Feedback — SOLUTION
 * =======================================================
 * Run: node extractor_retry.js
 */

import OpenAI from "openai";
import { z } from "zod";
import { ContactInfo, CONTACT_PARAMETERS } from "./schema_and_data.js";

const client = new OpenAI({ baseURL: "http://localhost:11434/v1", apiKey: "ollama" });

const EXTRACT_TOOL = {
  type: "function",
  function: {
    name: "extract_contact",
    description: "Extract contact info. ALL fields must be valid (email must be a real address format).",
    parameters: CONTACT_PARAMETERS,
  },
};

async function extractWithRetry(text, maxRetries = 3) {
  let lastError = null;

  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    let prompt = `Extract contact info:\n\n${text}`;
    if (lastError) {
      // Feed the model its own failure — this is what makes it self-correct
      prompt += `\n\nPrevious attempt failed with: ${lastError}`;
      prompt += `\nFix the output to match the required schema exactly.`;
    }

    try {
      const response = await client.chat.completions.create({
        model: "mistral",
        tools: [EXTRACT_TOOL],
        tool_choice: { type: "function", function: { name: "extract_contact" } },
        messages: [{ role: "user", content: prompt }],
      });
      const toolCalls = response.choices[0].message.tool_calls;
      if (!toolCalls || toolCalls.length === 0) {
        throw new Error("Model did not call the tool");
      }

      const args = JSON.parse(toolCalls[0].function.arguments);
      const contact = ContactInfo.parse(args);
      console.log(`  Attempt ${attempt}: Success!`);
      return contact;
    } catch (error) {
      lastError = error instanceof z.ZodError
        ? error.issues.map((iss) => `${iss.path}: ${iss.message}`).join(", ")
        : error.message;
      console.log(`  Attempt ${attempt}: ${lastError.slice(0, 80)} — retrying...`);
      await new Promise((r) => setTimeout(r, 2 ** attempt * 1000)); // exponential backoff
    }
  }

  throw new Error(`Failed after ${maxRetries} attempts: ${lastError}`);
}

const tricky = "Contact: J. at some-company, email is j (at) co (dot) com, phone TBD";
console.log(`Input: ${tricky}\n`);
try {
  const result = await extractWithRetry(tricky);
  console.log(`\nExtracted: ${result.name} <${result.email}>`);
} catch (error) {
  console.log(`\nGave up: ${error.message}`);
  console.log("(That can legitimately happen — the input is designed to be hostile.)");
}
