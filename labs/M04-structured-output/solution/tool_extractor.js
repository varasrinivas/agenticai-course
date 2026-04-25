/**
 * M04 Lab -- Step 2: Tool Use for Guaranteed Structure (SOLUTION)
 * ================================================================
 * Use Claude's tool_use feature to guarantee structured JSON output.
 * Claude returns data by "calling" a tool with the extracted fields.
 */

import Anthropic from "@anthropic-ai/sdk";
import "dotenv/config";

const client = new Anthropic();
const MODEL = "claude-sonnet-4-20250514";

// ─── Sample freetext filing descriptions (same as Step 1) ────────────────────

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

// ─── Tool definition ─────────────────────────────────────────────────────────

const EXTRACT_TOOL = {
  name: "extract_filing_data",
  description:
    "Extract structured data from a UCC filing description. " +
    "Call this tool with the extracted fields from the provided text.",
  input_schema: {
    type: "object",
    properties: {
      filing_type: {
        type: "string",
        enum: ["UCC-1", "UCC-3"],
        description: "The type of UCC filing",
      },
      filing_date: {
        type: "string",
        description: "Filing date in YYYY-MM-DD format",
      },
      debtor_name: {
        type: "string",
        description: "Full legal name of the debtor organization",
      },
      debtor_type: {
        type: "string",
        enum: [
          "LLC",
          "Corporation",
          "Limited Partnership",
          "Professional Association",
          "Cooperative",
          "Sole Proprietorship",
          "Other",
        ],
        description: "Type of business organization",
      },
      debtor_state: {
        type: "string",
        description: "State where the filing was made",
      },
      secured_party: {
        type: "string",
        description: "Name of the secured party (lender/creditor)",
      },
      collateral_type: {
        type: "string",
        enum: [
          "Blanket Lien",
          "Equipment",
          "Accounts Receivable",
          "Inventory",
          "Intellectual Property",
          "Real Property",
          "Agricultural",
          "Medical Equipment",
          "Other",
        ],
        description: "Category of collateral",
      },
      collateral_description: {
        type: "string",
        description: "Brief summary of the collateral covered",
      },
    },
    required: [
      "filing_type",
      "filing_date",
      "debtor_name",
      "debtor_type",
      "debtor_state",
      "secured_party",
      "collateral_type",
      "collateral_description",
    ],
  },
};

/**
 * Extract structured filing data using Claude's tool_use feature.
 *
 * @param {string} text - Freetext UCC filing description
 * @returns {Promise<object>} Extracted filing data (guaranteed structure)
 */
async function extractWithToolUse(text) {
  const response = await client.messages.create({
    model: MODEL,
    max_tokens: 1024,
    tools: [EXTRACT_TOOL],
    tool_choice: { type: "tool", name: "extract_filing_data" },
    messages: [
      {
        role: "user",
        content: `Extract the structured filing data from this UCC filing description:\n\n${text}`,
      },
    ],
  });

  const toolBlock = response.content.find((block) => block.type === "tool_use");
  if (!toolBlock) {
    throw new Error(
      "No tool_use block found in response. " +
        "Ensure tool_choice is set to force tool use."
    );
  }

  return toolBlock.input;
}

// ─── Main ─────────────────────────────────────────────────────────────────────

async function main() {
  console.log("=".repeat(70));
  console.log("M04 Lab -- Step 2: Tool Use for Guaranteed Structure");
  console.log("=".repeat(70));

  for (let i = 0; i < FREETEXT_FILINGS.length; i++) {
    const text = FREETEXT_FILINGS[i];
    console.log(`\n${"─".repeat(70)}`);
    console.log(`Filing ${i + 1}:`);
    console.log("─".repeat(70));
    console.log(`Input (first 100 chars): ${text.slice(0, 100)}...`);
    console.log();

    try {
      const result = await extractWithToolUse(text);
      console.log("Extracted via tool_use:");
      console.log(JSON.stringify(result, null, 2));
      console.log(`\n  [OK] All ${Object.keys(result).length} fields present`);
    } catch (e) {
      console.log(`[ERROR] ${e.message}`);
    }
  }

  console.log(`\n${"=".repeat(70)}`);
  console.log("Step 2 complete! Next: validated_extractor.js (Step 3)");
  console.log("=".repeat(70));
}

main();
