/**
 * M03 Lab — Few-Shot Prompting (Node.js)
 * ========================================
 * Classify UCC collateral descriptions into categories
 * using few-shot examples embedded in the prompt.
 */

import Anthropic from "@anthropic-ai/sdk";
import "dotenv/config";

const client = new Anthropic();
const MODEL = "claude-sonnet-4-6";

// ─── Few-Shot Examples ──────────────────────────────────────────────────────
// Each example maps a collateral description to its category.
// These examples teach Claude the classification pattern.

const EXAMPLES = [
  {
    description: "All accounts receivable and inventory",
    category: "Blanket Lien",
  },
  {
    description: "Specific equipment: (2) Caterpillar 320 excavators",
    category: "Equipment",
  },
  {
    description: "All crops, livestock, and farm products",
    category: "Agricultural",
  },
];

/**
 * Classify a UCC collateral description into a category
 * using few-shot prompting.
 *
 * @param {string} description - The collateral description from a UCC filing.
 * @returns {Promise<string>} The predicted category.
 */
async function classifyCollateral(description) {
  // TODO: Build a prompt that includes the EXAMPLES above as few-shot
  // demonstrations, then asks Claude to classify the new description.
  //
  // Suggested prompt structure:
  //   - System prompt explaining the task
  //   - User message containing:
  //       1. The few-shot examples (description -> category)
  //       2. The new description to classify
  //       3. An instruction to respond with ONLY the category name
  //
  // Call client.messages.create and return the category string.
  return "";
}

// ─── Main ───────────────────────────────────────────────────────────────────

const testCases = [
  {
    description: "All intellectual property, patents, and trademarks",
    expected: "Intellectual Property / General Intangibles",
  },
  {
    description: "2021 Peterbilt 579 truck, VIN 1XPBD49X1MD123456",
    expected: "Specific Equipment / Vehicle",
  },
  {
    description:
      "All assets of the Debtor, whether now owned or hereafter acquired",
    expected: "Blanket Lien",
  },
];

console.log("=".repeat(60));
console.log("Few-Shot Collateral Classification");
console.log("=".repeat(60));

for (let i = 0; i < testCases.length; i++) {
  const testCase = testCases[i];
  console.log(`\n--- Test ${i + 1} ---`);
  console.log(`Description: ${testCase.description}`);
  console.log(`Expected:    ${testCase.expected}`);
  try {
    const result = await classifyCollateral(testCase.description);
    console.log(`Predicted:   ${result}`);
    const match = testCase.expected.toLowerCase().includes(result.toLowerCase()) ||
                  result.toLowerCase().includes(testCase.expected.toLowerCase())
      ? "MATCH"
      : "CHECK";
    console.log(`Status:      [${match}]`);
  } catch (e) {
    console.log(`[ERROR] ${e.message}`);
  }
}
