/**
 * UCC Filing Lookup Agent — Agent (SOLUTION, Node.js)
 * =====================================================
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
// Mock Data (inline for Node.js — subset of mock_data.py records)
// ──────────────────────────────────────────────────────────────

const UCC_FILINGS = {
  "2024-0194827": {
    filing_number: "2024-0194827",
    filing_type: "UCC-1",
    status: "active",
    filing_date: "2024-02-15",
    lapse_date: "2029-02-15",
    state: "DE",
    debtor: {
      name: "Meridian Logistics Holdings LLC",
      address: "1209 Orange Street, Wilmington, DE 19801",
      organization_type: "LLC",
      jurisdiction: "Delaware",
    },
    secured_party: {
      name: "JPMorgan Chase Bank, N.A.",
      address: "383 Madison Avenue, New York, NY 10179",
    },
    collateral_description:
      "All accounts, chattel paper, deposit accounts, equipment, general intangibles, instruments, inventory, investment property, letter-of-credit rights, and all proceeds and products thereof.",
    amendments: [],
  },
  "2023-0087145": {
    filing_number: "2023-0087145",
    filing_type: "UCC-1",
    status: "active",
    filing_date: "2023-06-20",
    lapse_date: "2028-06-20",
    state: "DE",
    debtor: {
      name: "Meridian Fleet Services Inc.",
      address: "2711 Centerville Road, Suite 400, Wilmington, DE 19808",
      organization_type: "Corporation",
      jurisdiction: "Delaware",
    },
    secured_party: {
      name: "Wells Fargo Equipment Finance, Inc.",
      address: "800 Walnut Street, Des Moines, IA 50309",
    },
    collateral_description:
      "All equipment and fixtures including 47 Freightliner Cascadia Class 8 tractors, 85 Wabash DuraPlate dry van trailers, and all telematics and GPS equipment installed therein.",
    amendments: [
      {
        amendment_number: "2024-0012883",
        amendment_date: "2024-01-10",
        amendment_type: "Collateral Amendment",
        description: "Added 12 additional tractors and 20 additional trailers.",
      },
    ],
  },
  "2019-0334521": {
    filing_number: "2019-0334521",
    filing_type: "UCC-1",
    status: "lapsed",
    filing_date: "2019-08-12",
    lapse_date: "2024-08-12",
    state: "NY",
    debtor: {
      name: "Brightstone Capital Partners LLC",
      address: "125 Park Avenue, 25th Floor, New York, NY 10017",
      organization_type: "LLC",
      jurisdiction: "Delaware",
    },
    secured_party: {
      name: "Bank of America, N.A.",
      address: "100 North Tryon Street, Charlotte, NC 28255",
    },
    collateral_description: "All assets of the Debtor including accounts, inventory, equipment, and general intangibles.",
    amendments: [],
  },
  "2022-0451208": {
    filing_number: "2022-0451208",
    filing_type: "UCC-1",
    status: "active",
    filing_date: "2022-03-28",
    lapse_date: "2027-03-28",
    state: "TX",
    debtor: {
      name: "Lone Star Fabrication & Welding Inc.",
      address: "4500 Industrial Blvd, Houston, TX 77015",
      organization_type: "Corporation",
      jurisdiction: "Texas",
    },
    secured_party: {
      name: "Caterpillar Financial Services Corp.",
      address: "2120 West End Avenue, Nashville, TN 37203",
    },
    collateral_description:
      "Specific equipment: Caterpillar 320 GC Hydraulic Excavator, Caterpillar D6 Dozer, Caterpillar 950 GC Wheel Loader, with all attachments and accessories.",
    amendments: [],
  },
  "2021-0298374": {
    filing_number: "2021-0298374",
    filing_type: "UCC-1",
    status: "terminated",
    filing_date: "2021-04-18",
    lapse_date: "2026-04-18",
    state: "IL",
    debtor: {
      name: "Great Lakes Brewing Collective Inc.",
      address: "811 W. Fulton Market, Chicago, IL 60607",
      organization_type: "Corporation",
      jurisdiction: "Illinois",
    },
    secured_party: {
      name: "BMO Harris Bank N.A.",
      address: "111 W. Monroe Street, Chicago, IL 60603",
    },
    collateral_description: "All equipment (brewing tanks, fermentation vessels, kegging/canning lines, cold storage, delivery vehicles) and inventory.",
    amendments: [
      {
        amendment_number: "2024-0009123",
        amendment_date: "2024-01-22",
        amendment_type: "Termination",
        description: "Loan paid in full. All security interests released.",
      },
    ],
  },
};

// ──────────────────────────────────────────────────────────────
// Tool Definition
// ──────────────────────────────────────────────────────────────

const tools = [
  {
    name: "search_ucc_filings",
    description:
      "Search for UCC financing statement filings by business name and state. Returns matching filings with status, debtor/secured party info, collateral, and amendments. Supports partial name matching.",
    input_schema: {
      type: "object",
      properties: {
        business_name: {
          type: "string",
          description: "The business (debtor) name to search for. Supports partial matching.",
        },
        state: {
          type: "string",
          description: "Two-letter state code (e.g., 'DE', 'NY', 'TX').",
        },
      },
      required: ["business_name", "state"],
    },
  },
];

// ──────────────────────────────────────────────────────────────
// Tool Implementation
// ──────────────────────────────────────────────────────────────

function searchUccFilings(businessName, state) {
  const nameLower = businessName.trim().toLowerCase();
  const stateUpper = state.trim().toUpperCase();

  const matches = Object.values(UCC_FILINGS).filter((record) => {
    const debtorName = record.debtor.name.toLowerCase();
    return debtorName.includes(nameLower) && record.state === stateUpper;
  });

  if (matches.length === 0) {
    return {
      results: [],
      total: 0,
      message: `No UCC filings found for '${businessName}' in state '${stateUpper}'.`,
    };
  }

  return {
    results: matches,
    total: matches.length,
  };
}

// ──────────────────────────────────────────────────────────────
// Agent Loop
// ──────────────────────────────────────────────────────────────

async function runAgent() {
  const client = new Anthropic();

  const systemPrompt =
    "You are a UCC filing research assistant. " +
    "When a user asks about UCC filings, liens, or security interests, " +
    "use the search_ucc_filings tool to look up filings. Explain results clearly, " +
    "including filing status, secured party, collateral, dates, and amendments. " +
    "Explain practical implications. If asked a general question, respond without tools.";

  const messages = [];

  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout,
  });

  console.log("=".repeat(60));
  console.log("  UCC Filing Lookup Agent (Node.js)");
  console.log("  Search for UCC filings by business name and state.");
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
        let response = await client.messages.create({
          model: "claude-sonnet-4-6",
          max_tokens: 1024,
          system: systemPrompt,
          tools: tools,
          messages: messages,
        });

        if (response.stop_reason === "tool_use") {
          const toolUseBlock = response.content.find(
            (block) => block.type === "tool_use"
          );

          if (toolUseBlock) {
            let toolResult;

            if (toolUseBlock.name === "search_ucc_filings") {
              toolResult = searchUccFilings(
                toolUseBlock.input.business_name,
                toolUseBlock.input.state
              );
            } else {
              toolResult = { error: `Unknown tool: ${toolUseBlock.name}` };
            }

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

            response = await client.messages.create({
              model: "claude-sonnet-4-6",
              max_tokens: 1024,
              system: systemPrompt,
              tools: tools,
              messages: messages,
            });
          }
        }

        const assistantText = response.content[0].text;
        console.log(`\nAgent: ${assistantText}\n`);
        messages.push({ role: "assistant", content: response.content });
      } catch (error) {
        if (error instanceof Anthropic.AuthenticationError) {
          console.log("\nError: Invalid API key. Set ANTHROPIC_API_KEY.\n");
        } else if (error instanceof Anthropic.RateLimitError) {
          console.log("\nError: Rate limit exceeded. Wait and retry.\n");
        } else {
          console.log(`\nError: ${error.message}\n`);
        }
        messages.pop();
      }

      askQuestion();
    });
  };

  askQuestion();
}

runAgent();
