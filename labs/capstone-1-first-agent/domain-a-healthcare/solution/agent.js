/**
 * Healthcare Pre-Auth Status Checker — Agent (SOLUTION, Node.js)
 * ================================================================
 * Complete implementation of the conversational agent loop in Node.js.
 *
 * Prerequisites:
 *   npm install @anthropic-ai/sdk readline
 *
 * Run:
 *   node agent.js
 */

import Anthropic from "@anthropic-ai/sdk";
import * as readline from "readline";

// ──────────────────────────────────────────────────────────────
// Mock Data (inline for Node.js — same records as mock_data.py)
// ──────────────────────────────────────────────────────────────

const PREAUTH_RECORDS = {
  "PA-2024-00142": {
    reference_id: "PA-2024-00142",
    status: "approved",
    patient_name: "Maria Gonzalez",
    provider_name: "Dr. Sarah Chen, MD — Orthopedic Surgery",
    payer: "BlueCross BlueShield of Illinois",
    cpt_code: "27447",
    cpt_description: "Total knee replacement (arthroplasty)",
    icd10_codes: ["M17.11"],
    determination_date: "2024-10-08",
    expiration_date: "2025-01-08",
    reviewer_notes:
      "Meets InterQual criteria for TKA. Conservative treatment documented over 6-month period with insufficient relief. Approved for inpatient stay up to 3 days.",
    urgency: "elective",
  },
  "PA-2024-00278": {
    reference_id: "PA-2024-00278",
    status: "pending",
    patient_name: "Robert Williams",
    provider_name: "Dr. Anita Patel, MD — Cardiology",
    payer: "Aetna",
    cpt_code: "33533",
    cpt_description: "Coronary artery bypass graft (CABG), single arterial graft",
    icd10_codes: ["I25.10", "I11.9"],
    determination_date: null,
    reviewer_notes:
      "Pending peer-to-peer review. Cardiac catheterization report requested. Awaiting documentation of ejection fraction and stress test results.",
    urgency: "urgent",
  },
  "PA-2024-00398": {
    reference_id: "PA-2024-00398",
    status: "denied",
    patient_name: "James O'Brien",
    provider_name: "Dr. Michael Torres, MD — Pain Management",
    payer: "UnitedHealthcare",
    cpt_code: "63030",
    cpt_description: "Lumbar laminotomy (hemilaminectomy) with decompression",
    icd10_codes: ["M51.16", "M54.5"],
    determination_date: "2024-10-02",
    reviewer_notes:
      "Denied — does not meet medical necessity criteria. Only 4 weeks of conservative treatment documented. Plan requires minimum 6 weeks of PT and at least one epidural steroid injection before surgical intervention.",
    urgency: "elective",
  },
  "PA-2024-00415": {
    reference_id: "PA-2024-00415",
    status: "info-requested",
    patient_name: "Diane Kowalski",
    provider_name: "Dr. Emily Zhang, MD — Oncology",
    payer: "Cigna",
    cpt_code: "77386",
    cpt_description: "Intensity-modulated radiation therapy (IMRT), complex",
    icd10_codes: ["C50.911"],
    determination_date: null,
    reviewer_notes:
      "Additional information requested: (1) Pathology report with tumor staging, (2) HER2/ER/PR receptor status, (3) Oncotype DX score, (4) Tumor board recommendation. Respond within 14 days.",
    urgency: "urgent",
  },
};

// ──────────────────────────────────────────────────────────────
// Tool Definition
// ──────────────────────────────────────────────────────────────

const tools = [
  {
    name: "get_preauth_status",
    description:
      "Look up the status of a healthcare prior authorization request. Returns the authorization status, patient info, CPT/ICD codes, and clinical reviewer notes.",
    input_schema: {
      type: "object",
      properties: {
        reference_id: {
          type: "string",
          description:
            "The prior authorization reference ID, formatted as PA-YYYY-NNNNN (e.g., PA-2024-00142)",
        },
      },
      required: ["reference_id"],
    },
  },
];

// ──────────────────────────────────────────────────────────────
// Tool Implementation
// ──────────────────────────────────────────────────────────────

function getPreAuthStatus(referenceId) {
  const normalized = referenceId.trim().toUpperCase();
  const record = PREAUTH_RECORDS[normalized];

  if (!record) {
    return {
      error: `No pre-authorization found for reference ID '${normalized}'.`,
      suggestion:
        "Please verify the reference ID format (PA-YYYY-NNNNN) and try again.",
    };
  }

  return record;
}

// ──────────────────────────────────────────────────────────────
// Agent Loop
// ──────────────────────────────────────────────────────────────

async function runAgent() {
  const client = new Anthropic();

  const systemPrompt =
    "You are a healthcare pre-authorization status assistant. " +
    "When a user provides a prior authorization reference number " +
    "(formatted like PA-YYYY-NNNNN), use the get_preauth_status tool " +
    "to look up the status. Then explain the result in clear, " +
    "non-technical language and suggest next steps. " +
    "If the user asks a general question, respond helpfully without " +
    "calling any tools. Always be professional and empathetic.";

  const messages = [];

  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout,
  });

  console.log("=".repeat(60));
  console.log("  Healthcare Pre-Auth Status Checker (Node.js)");
  console.log("  Type a PA reference number to check status.");
  console.log("  Type 'quit' to exit.");
  console.log("=".repeat(60));
  console.log();

  const askQuestion = () => {
    rl.question("You: ", async (userInput) => {
      userInput = userInput.trim();

      if (!userInput) {
        askQuestion();
        return;
      }

      if (["quit", "exit", "q"].includes(userInput.toLowerCase())) {
        console.log("Goodbye!");
        rl.close();
        return;
      }

      messages.push({ role: "user", content: userInput });

      try {
        // Step 1: Send message to Claude
        let response = await client.messages.create({
          model: "claude-sonnet-4-6",
          max_tokens: 1024,
          system: systemPrompt,
          tools: tools,
          messages: messages,
        });

        // Step 2: Handle tool use
        if (response.stop_reason === "tool_use") {
          const toolUseBlock = response.content.find(
            (block) => block.type === "tool_use"
          );

          if (toolUseBlock) {
            let toolResult;

            if (toolUseBlock.name === "get_preauth_status") {
              toolResult = getPreAuthStatus(toolUseBlock.input.reference_id);
            } else {
              toolResult = { error: `Unknown tool: ${toolUseBlock.name}` };
            }

            // Add assistant response and tool result to messages
            messages.push({ role: "assistant", content: response.content });
            messages.push({
              role: "user",
              content: [
                {
                  type: "tool_result",
                  tool_use_id: toolUseBlock.id,
                  content: JSON.stringify(toolResult),
                },
              ],
            });

            // Get Claude's final response
            response = await client.messages.create({
              model: "claude-sonnet-4-6",
              max_tokens: 1024,
              system: systemPrompt,
              tools: tools,
              messages: messages,
            });
          }
        }

        // Step 3: Print response
        const assistantText = response.content[0].text;
        console.log(`\nAgent: ${assistantText}\n`);
        messages.push({ role: "assistant", content: response.content });
      } catch (error) {
        if (error instanceof Anthropic.AuthenticationError) {
          console.log(
            "\nError: Invalid API key. Set the ANTHROPIC_API_KEY environment variable.\n"
          );
        } else if (error instanceof Anthropic.RateLimitError) {
          console.log("\nError: Rate limit exceeded. Please wait and try again.\n");
        } else {
          console.log(`\nError: ${error.message}\n`);
        }
        messages.pop(); // Remove failed message
      }

      askQuestion();
    });
  };

  askQuestion();
}

runAgent();
