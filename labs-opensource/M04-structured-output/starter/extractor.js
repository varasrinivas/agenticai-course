/**
 * M04 Lab - Step 2: Extract with Forced Tool Use + Validation
 * ============================================================
 * Force Mistral to call extract_contact, validate the args with Zod.
 * Run: node extractor.js
 */

import OpenAI from "openai";
import { z } from "zod";
import { ContactInfo, CONTACT_PARAMETERS, TEST_SIGNATURES } from "./schema_and_data.js";

const client = new OpenAI({ baseURL: "http://localhost:11434/v1", apiKey: "ollama" });

// Tool definition: the schema becomes the parameters (COMPLETE)
const EXTRACT_TOOL = {
  type: "function",
  function: {
    name: "extract_contact",
    description: "Extract structured contact information from an email signature.",
    parameters: CONTACT_PARAMETERS,
  },
};

/**
 * Extract contact info using forced tool use + Zod validation.
 *
 * TODO:
 * 1. Call client.chat.completions.create() with:
 *    - model: "mistral"
 *    - tools: [EXTRACT_TOOL]
 *    - tool_choice: { type: "function", function: { name: "extract_contact" } }
 *      ← this FORCES the model to call the tool
 *    - messages: [{ role: "user", content: `Extract contact info:\n\n${text}` }]
 * 2. const toolCalls = response.choices[0].message.tool_calls;
 *    If empty/undefined → throw new Error("Model did not call the tool")
 * 3. const args = JSON.parse(toolCalls[0].function.arguments);  // JSON STRING → object
 * 4. return ContactInfo.parse(args);  // throws ZodError if schema violated
 */
async function extractContact(text) {
  // TODO: implement
}

// ── Scoreboard over all 5 test signatures (COMPLETE) ──
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
