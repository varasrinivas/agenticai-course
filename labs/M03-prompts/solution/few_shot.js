/**
 * M03 Lab — Few-Shot Prompting (Node.js Solution)
 * ==================================================
 * Classify UCC collateral descriptions into categories
 * using few-shot examples embedded in the prompt.
 */

import Anthropic from "@anthropic-ai/sdk";
import "dotenv/config";

const client = new Anthropic();
const MODEL = "claude-sonnet-4-6";

// ─── Few-Shot Examples ──────────────────────────────────────────────────────

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
  // Build few-shot examples into the prompt
  let examplesText = "";
  for (const ex of EXAMPLES) {
    examplesText += `Description: ${ex.description}\nCategory: ${ex.category}\n\n`;
  }

  const userMessage =
    "Classify the following UCC collateral descriptions into categories. " +
    "Here are some examples:\n\n" +
    examplesText +
    "Now classify this description:\n" +
    `Description: ${description}\n` +
    "Category: ";

  const systemPrompt =
    "You are a UCC filing classification expert. Given a collateral " +
    "description from a UCC filing, classify it into the most appropriate " +
    "category. Respond with ONLY the category name, nothing else.";

  const response = await client.messages.create({
    model: MODEL,
    max_tokens: 100,
    system: systemPrompt,
    messages: [{ role: "user", content: userMessage }],
  });

  return response.content[0].text.trim();
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
    const match =
      testCase.expected.toLowerCase().includes(result.toLowerCase()) ||
      result.toLowerCase().includes(testCase.expected.toLowerCase())
        ? "MATCH"
        : "CHECK";
    console.log(`Status:      [${match}]`);
  } catch (e) {
    console.log(`[ERROR] ${e.message}`);
  }
}
