/**
 * M04 Lab - Step 2: Extract with Forced Tool Use + Validation — SOLUTION
 * =======================================================================
 * Run: node extractor.js
 */

import OpenAI from "openai";
import { z } from "zod";
import { ContactInfo, CONTACT_PARAMETERS, TEST_SIGNATURES } from "./schema_and_data.js";

const client = new OpenAI({ baseURL: "http://localhost:11434/v1", apiKey: "ollama" });

const EXTRACT_TOOL = {
  type: "function",
  function: {
    name: "extract_contact",
    description: "Extract structured contact information from an email signature.",
    parameters: CONTACT_PARAMETERS,
  },
};

async function extractContact(text) {
  const response = await client.chat.completions.create({
    model: "mistral",
    tools: [EXTRACT_TOOL],
    // Forcing the tool guarantees structured output instead of prose
    tool_choice: { type: "function", function: { name: "extract_contact" } },
    messages: [{ role: "user", content: `Extract contact info:\n\n${text}` }],
  });

  const toolCalls = response.choices[0].message.tool_calls;
  if (!toolCalls || toolCalls.length === 0) {
    throw new Error("Model did not call the tool");
  }

  // arguments is a JSON string — parse it, then validate with Zod
  const args = JSON.parse(toolCalls[0].function.arguments);
  return ContactInfo.parse(args);
}

let successes = 0;
for (let i = 0; i < TEST_SIGNATURES.length; i++) {
  try {
    const contact = await extractContact(TEST_SIGNATURES[i]);
    console.log(`[OK]   Sig ${i + 1}: ${contact.name} <${contact.email}> @ ${contact.company ?? "N/A"}`);
    successes++;
  } catch (error) {
    const msg = error instanceof z.ZodError
      ? error.issues.map((iss) => `${iss.path}: ${iss.message}`).join(", ")
      : error.message;
    console.log(`[FAIL] Sig ${i + 1}: ${msg.slice(0, 100)}`);
  }
}
console.log(`\nResults: ${successes}/${TEST_SIGNATURES.length} extracted successfully`);
