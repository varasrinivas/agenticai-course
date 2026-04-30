/**
 * M04 Lab -- Step 1: JSON Extraction with Prompting
 * ===================================================
 * Extract structured data from freetext UCC filing descriptions
 * using prompt engineering to get Claude to return valid JSON.
 */

import Anthropic from "@anthropic-ai/sdk";
import "dotenv/config";

const client = new Anthropic();
const MODEL = "claude-sonnet-4-6";

// ─── Sample freetext filing descriptions ──────────────────────────────────────

const FREETEXT_FILINGS = [
  // Based on mock filing UCC-2024-NY-0012847
  "On March 15, 2024, Greenfield Logistics LLC (a New York LLC located at 450 West 33rd Street, " +
    "Suite 800, New York, NY 10001) filed a UCC-1 financing statement with the NY Department of State. " +
    "Atlantic Capital Partners (1 Chase Manhattan Plaza, Floor 45, New York, NY 10005) is listed as the " +
    "secured party. The collateral covers all accounts receivable, inventory, equipment, and general " +
    "intangibles now owned or hereafter acquired by the Debtor.",

  // Based on mock filing UCC-2023-TX-0187634
  "A UCC-1 was recorded on September 10, 2023 in Texas. The debtor is Lone Star Energy Solutions LP, " +
    "a Texas limited partnership headquartered at 1200 Smith Street, Suite 3000, Houston, TX 77002. " +
    "Wells Fargo Equipment Finance holds the security interest in specific equipment: three Caterpillar " +
    "349F L hydraulic excavators (serial numbers CAT349F-8821, CAT349F-8822, CAT349F-8823) and one " +
    "Liebherr LTM 1300-6.2 mobile crane (serial number LTM-DE-90124).",

  // Based on mock filing UCC-2024-FL-0054219
  "Sunshine Medical Group PA (a Florida professional association at 4500 Biscayne Boulevard, Miami, " +
    "FL 33137) filed an amendment (UCC-3) on June 1, 2024 with the FL Secured Transaction Registry. " +
    "This amends the original filing UCC-2022-FL-0031456. TD Bank N.A. is the secured party. The " +
    "amendment adds medical equipment including two Siemens MAGNETOM Vida 3T MRI systems and one GE " +
    "Revolution CT scanner to the existing collateral.",
];

/**
 * Extract structured filing data from freetext using prompt-based JSON extraction.
 *
 * @param {string} text - Freetext UCC filing description
 * @returns {Promise<object>} Extracted filing data
 */
async function extractFilingJson(text) {
  // TODO: Build a system prompt that instructs Claude to:
  //   1. Extract UCC filing information from the provided text
  //   2. Return ONLY valid JSON (no markdown code fences, no explanation)
  //   3. Use exactly these field names:
  //      - filing_type: "UCC-1" or "UCC-3"
  //      - filing_date: date in YYYY-MM-DD format
  //      - debtor_name: full legal name of the debtor
  //      - debtor_type: organization type (LLC, Corporation, LP, etc.)
  //      - debtor_state: state where filed
  //      - secured_party: name of the secured party
  //      - collateral_type: one of "Blanket Lien", "Equipment", "Medical Equipment",
  //        "Accounts Receivable", "Inventory", "Intellectual Property", "Agricultural", "Other"
  //      - collateral_description: brief summary of collateral
  //
  // Then call client.messages.create with:
  //   - model: MODEL
  //   - max_tokens: 1024
  //   - system: <your system prompt>
  //   - messages: a single user message containing the freetext
  //
  // Parse the response text with JSON.parse() and return the object.
  // Hint: response.content[0].text gives you the raw text.
  return null;
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
      if (result === null) {
        console.log("[INCOMPLETE] Function returned null -- complete the TODO");
      } else {
        console.log("Extracted JSON:");
        console.log(JSON.stringify(result, null, 2));
      }
    } catch (e) {
      console.log(`[ERROR] ${e.message}`);
    }
  }

  console.log(`\n${"=".repeat(70)}`);
  console.log("Step 1 complete! Next: tool_extractor.js (Step 2)");
  console.log("=".repeat(70));
}

main();
