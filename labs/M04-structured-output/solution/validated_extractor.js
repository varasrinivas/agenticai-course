/**
 * M04 Lab -- Step 3: Validation with Zod (SOLUTION)
 * ===================================================
 * Add schema validation to ensure extracted data is not just valid JSON
 * but semantically correct (valid dates, valid enums, non-empty strings).
 */

import Anthropic from "@anthropic-ai/sdk";
import "dotenv/config";
import { z } from "zod";

const client = new Anthropic();
const MODEL = "claude-sonnet-4-6";

// ─── Sample freetext filing descriptions (same as Steps 1-2) ─────────────────

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

// Edge case -- deliberately ambiguous/malformed
const EDGE_CASE_TEXT =
  "filed sometime in 2024, maybe New York. Debtor could be Smith & Co or Smith and Company. " +
  "Collateral: everything? Also the filing number is unknown.";

// ─── Tool definition (reused from Step 2) ────────────────────────────────────

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

// ─── Zod validation schema ───────────────────────────────────────────────────

const uccFilingSchema = z.object({
  filing_type: z.enum(["UCC-1", "UCC-3"], {
    errorMap: () => ({ message: "filing_type must be 'UCC-1' or 'UCC-3'" }),
  }),

  filing_date: z
    .string()
    .regex(/^\d{4}-\d{2}-\d{2}$/, "filing_date must be in YYYY-MM-DD format")
    .refine(
      (val) => {
        const d = new Date(val + "T00:00:00Z");
        return !isNaN(d.getTime());
      },
      { message: "filing_date is not a valid calendar date" }
    ),

  debtor_name: z.string().min(2, "debtor_name must be at least 2 characters"),

  debtor_type: z.enum(
    [
      "LLC",
      "Corporation",
      "Limited Partnership",
      "Professional Association",
      "Cooperative",
      "Sole Proprietorship",
      "Other",
    ],
    {
      errorMap: () => ({
        message: "debtor_type is not a valid organization type",
      }),
    }
  ),

  debtor_state: z
    .string()
    .min(2, "debtor_state must be at least 2 characters"),

  secured_party: z
    .string()
    .min(2, "secured_party must be at least 2 characters"),

  collateral_type: z.enum(
    [
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
    { errorMap: () => ({ message: "collateral_type is not a valid category" }) }
  ),

  collateral_description: z
    .string()
    .min(5, "collateral_description must be at least 5 characters"),
});

// ─── Extraction + Validation ─────────────────────────────────────────────────

/**
 * Extract structured filing data using tool_use (from Step 2).
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

/**
 * Extract structured data and validate it with Zod.
 *
 * @param {string} text - Freetext UCC filing description
 * @returns {Promise<object>} Validated filing data
 * @throws {z.ZodError} If validation fails
 */
async function extractAndValidate(text) {
  const rawData = await extractWithToolUse(text);
  return uccFilingSchema.parse(rawData);
}

// ─── Main ─────────────────────────────────────────────────────────────────────

async function main() {
  console.log("=".repeat(70));
  console.log("M04 Lab -- Step 3: Validation with Zod");
  console.log("=".repeat(70));

  // --- Test valid filings ---
  for (let i = 0; i < FREETEXT_FILINGS.length; i++) {
    const text = FREETEXT_FILINGS[i];
    console.log(`\n${"─".repeat(70)}`);
    console.log(`Filing ${i + 1} (should PASS validation):`);
    console.log("─".repeat(70));
    console.log(`Input (first 100 chars): ${text.slice(0, 100)}...`);
    console.log();

    try {
      const filing = await extractAndValidate(text);
      console.log("[PASS] Validated successfully!");
      console.log(`  Filing type:  ${filing.filing_type}`);
      console.log(`  Filing date:  ${filing.filing_date}`);
      console.log(`  Debtor:       ${filing.debtor_name} (${filing.debtor_type})`);
      console.log(`  State:        ${filing.debtor_state}`);
      console.log(`  Secured:      ${filing.secured_party}`);
      console.log(`  Collateral:   ${filing.collateral_type}`);
      console.log(
        `  Description:  ${filing.collateral_description.slice(0, 80)}...`
      );
    } catch (e) {
      if (e instanceof z.ZodError) {
        console.log("[UNEXPECTED FAIL] Validation error on valid filing:");
        for (const issue of e.issues) {
          console.log(`  - ${issue.path[0]}: ${issue.message}`);
        }
      } else {
        console.log(`[ERROR] ${e.message}`);
      }
    }
  }

  // --- Test edge case (should fail validation) ---
  console.log(`\n${"─".repeat(70)}`);
  console.log("Edge Case (should FAIL validation):");
  console.log("─".repeat(70));
  console.log(`Input: ${EDGE_CASE_TEXT}`);
  console.log();

  try {
    const filing = await extractAndValidate(EDGE_CASE_TEXT);
    // Expect this branch from a capable model, and read it as the lesson rather
    // than as a surprise. The input says "sometime in 2024", "maybe New York"
    // and "the filing number is unknown" -- yet a schema-valid object comes
    // back with a precise filing_date and a definite state. Nothing was
    // validated away because nothing was malformed. It was invented.
    //
    // A schema checks SHAPE, not TRUTH. A confident fabrication satisfies every
    // type, enum and regex you can write, so "we use structured output,
    // therefore the data is reliable" does not follow. Structured output makes
    // data parseable; grounding it is a separate job. (As in the Python twin.)
    console.log("[VALIDATION PASSED] — and that is the point:");
    console.log(`  Got: ${JSON.stringify(filing, null, 2)}`);
    console.log();
    const vague = {
      filing_date: "the input said only 'sometime in 2024'",
      debtor_state: "the input said 'maybe New York'",
      debtor_name: "the input offered two spellings; one was chosen",
    };
    for (const [field, why] of Object.entries(vague)) {
      const value = filing?.[field];
      if (value !== undefined && value !== null && value !== "" && value !== "<UNKNOWN>") {
        console.log(`  invented  ${field} = ${JSON.stringify(value)}  (${why})`);
      }
    }
    console.log();
    console.log("  Defence: make uncertainty representable, then validate THAT —");
    console.log("  an optional field the model may leave null, or an explicit");
    console.log("  'unknown' sentinel, so a gap can be stated instead of guessed.");
  } catch (e) {
    if (e instanceof z.ZodError) {
      // More literal models do refuse here. That is the other half of the
      // lesson: whether invention happens is a property of the model, not of
      // the schema, so it is not something to build a guarantee on.
      console.log("[VALIDATION FAILED] This model declined to invent the missing fields:");
      for (const issue of e.issues) {
        console.log(`  - ${issue.path[0]}: ${issue.message}`);
      }
    } else {
      console.log(`[ERROR] ${e.message}`);
    }
  }

  console.log(`\n${"=".repeat(70)}`);
  console.log("Step 3 complete! All exercises done.");
  console.log("=".repeat(70));
}

main();
