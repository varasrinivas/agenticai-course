/**
 * M04 Lab - Step 3: Retry with Error Feedback
 * ============================================
 * When validation fails, tell the model WHAT failed and let it self-correct.
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

/**
 * Extract with automatic retry on validation failure.
 *
 * TODO:
 * let lastError = null;
 * For attempt = 1..maxRetries:
 *   1. let prompt = `Extract contact info:\n\n${text}`;
 *      If lastError: append
 *        `\n\nPrevious attempt failed with: ${lastError}\n` +
 *        `Fix the output to match the required schema exactly.`
 *   2. Call the API (same forced tool_choice pattern as Step 2),
 *      JSON.parse(toolCalls[0].function.arguments)
 *   3. return ContactInfo.parse(args) on success
 *   4. catch:
 *      - ZodError → lastError = issues joined as "path: message"
 *      - other errors → lastError = error.message
 *      print attempt status; await new Promise(r => setTimeout(r, 2 ** attempt * 1000));
 * After the loop: throw new Error(`Failed after ${maxRetries} attempts: ${lastError}`);
 */
async function extractWithRetry(text, maxRetries = 3) {
  // TODO: implement
}

// ── Test with a deliberately tricky signature (COMPLETE) ──
const tricky = "Contact: J. at some-company, email is j (at) co (dot) com, phone TBD";
console.log(`Input: ${tricky}\n`);
try {
  const result = await extractWithRetry(tricky);
  console.log(`\nExtracted: ${result.name} <${result.email}>`);
} catch (error) {
  console.log(`\nGave up: ${error.message}`);
  console.log("(That can legitimately happen — the input is designed to be hostile.)");
}
