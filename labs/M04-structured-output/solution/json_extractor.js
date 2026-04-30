/**
 * M04 Lab -- Step 1: JSON Extraction with Prompting (SOLUTION)
 * =============================================================
 * Extract structured data from freetext UCC filing descriptions
 * using prompt engineering to get Claude to return valid JSON.
 */

import Anthropic from "@anthropic-ai/sdk";
import "dotenv/config";

const client = new Anthropic();
const MODEL = "claude-sonnet-4-6";

// ─── Sample freetext filing descriptions ──────────────────────────────────────

const FREETEXT_FILINGS = [
  "On March 15, 2024, Greenfield Logistics LLC (a New York LLC located at 450 West 33rd Street, " +
    "Suite 800, New York, NY 10001) filed a UCC-1 financing statement with the NY Department of State. " +
    "Atlantic Capital Partners (1 Chase Manhattan Plaza, Floor 45, New York, NY 10005) is listed as the " +
    "secured party. The collateral covers all accounts receivable, inventory, equipment, and general " +
    "intangibles now owned or hereafter acquired by the Debtor.",

  "A UCC-1 was recorded on September 10, 2023 in Texas. The debtor is Lone Star Energy Solutions LP, " +
    "a Texas limited partnership headquartered at 1200 Smith Street, Suite 3000, Houston, TX 77002. " +
    "Wells Fargo Equipment Finance holds the security interest in specific equipment: three Caterpillar " +
    "349F L hydraulic excavators (serial numbers CAT349F-8821, CAT349F-8822, CAT349F-8823) and one " +
    "Liebherr LTM 1300-6.2 mobile crane (serial number LTM-DE-90124).",

  "Sunshine Medical Group PA (a Florida professional association at 4500 Biscayne Boulevard, Miami, " +
    "FL 33137) filed an amendment (UCC-3) on June 1, 2024 with the FL Secured Transaction Registry. " +
    "This amends the original filing UCC-2022-FL-0031456. TD Bank N.A. is the secured party. The " +
    "amendment adds medical equipment including two Siemens MAGNETOM Vida 3T MRI systems and one GE " +
    "Revolution CT scanner to the existing collateral.",
];

const SYSTEM_PROMPT = `You are a UCC filing data extraction specialist. Your job is to extract structured data from freetext UCC filing descriptions.

Given a freetext description of a UCC filing, extract the following fields and return ONLY valid JSON. Do not include any explanation, markdown code fences, or additional text -- just the raw JSON object.

Required fields:
- filing_type: The type of UCC filing ("UCC-1" for original filings, "UCC-3" for amendments/continuations)
- filing_date: The date the filing was made, in YYYY-MM-DD format
- debtor_name: The full legal name of the debtor (the entity that owes the obligation)
- debtor_type: The type of business organization (e.g., "LLC", "Corporation", "Limited Partnership", "Professional Association", "Cooperative", "Other")
- debtor_state: The state where the filing was made
- secured_party: The name of the secured party (the lender or creditor)
- collateral_type: Classify the collateral into one of these categories: "Blanket Lien" (covers all assets), "Equipment" (specific machinery/vehicles), "Medical Equipment", "Accounts Receivable", "Inventory", "Intellectual Property", "Real Property", "Agricultural", or "Other"
- collateral_description: A brief summary of what collateral is covered

Return ONLY the JSON object. No markdown, no code fences, no explanation.`;

/**
 * Extract structured filing data from freetext using prompt-based JSON extraction.
 *
 * @param {string} text - Freetext UCC filing description
 * @returns {Promise<object>} Extracted filing data
 */
async function extractFilingJson(text) {
  const response = await client.messages.create({
    model: MODEL,
    max_tokens: 1024,
    system: SYSTEM_PROMPT,
    messages: [{ role: "user", content: text }],
  });

  let rawText = response.content[0].text.trim();

  // Strip any accidental markdown fences Claude might add
  if (rawText.startsWith("```")) {
    rawText = rawText.includes("\n")
      ? rawText.split("\n").slice(1).join("\n")
      : rawText.slice(3);
  }
  if (rawText.endsWith("```")) {
    rawText = rawText.slice(0, -3);
  }
  rawText = rawText.trim();

  return JSON.parse(rawText);
}

// ─── Main ─────────────────────────────────────────────────────────────────────

async function main() {
  console.log("=".repeat(70));
  console.log("M04 Lab -- Step 1: JSON Extraction with Prompting");
  console.log("=".repeat(70));

  for (let i = 0; i < FREETEXT_FILINGS.length; i++) {
    const text = FREETEXT_FILINGS[i];
    console.log(`\n${"─".repeat(70)}`);
    console.log(`Filing ${i + 1}:`);
    console.log("─".repeat(70));
    console.log(`Input (first 100 chars): ${text.slice(0, 100)}...`);
    console.log();

    try {
      const result = await extractFilingJson(text);
      console.log("Extracted JSON:");
      console.log(JSON.stringify(result, null, 2));
    } catch (e) {
      console.log(`[ERROR] ${e.message}`);
    }
  }

  console.log(`\n${"=".repeat(70)}`);
  console.log("Step 1 complete! Next: tool_extractor.js (Step 2)");
  console.log("=".repeat(70));
}

main();
