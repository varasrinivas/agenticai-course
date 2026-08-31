/**
 * B2B Ecommerce Order Status Bot — Agent (SOLUTION, Node.js)
 * =============================================================
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

const ORDER_RECORDS = {
  "PO-2024-8847": {
    po_number: "PO-2024-8847",
    status: "shipped",
    customer_name: "Apex Manufacturing Co.",
    order_date: "2024-10-28",
    ship_date: "2024-11-02",
    estimated_delivery: "2024-11-06",
    carrier: "FedEx Freight",
    tracking_number: "7489-3920-4817",
    shipping_method: "LTL Freight",
    warehouse: "Chicago Distribution Center (ORD-DC3)",
    line_items: [
      { sku: "IND-VALVE-3200", description: "3-inch Industrial Ball Valve, SS316", quantity: 50, unit_price: 87.5, status: "shipped" },
      { sku: "GASKET-FLG-3IN", description: "3-inch Flange Gasket, PTFE", quantity: 100, unit_price: 12.3, status: "shipped" },
    ],
    total: 5890.0,
    payment_terms: "Net 30",
    payment_status: "invoiced",
    notes: "All items shipped in single shipment. Signature required on delivery.",
  },
  "PO-2024-9250": {
    po_number: "PO-2024-9250",
    status: "backordered",
    customer_name: "Summit HVAC Solutions",
    order_date: "2024-11-10",
    estimated_delivery: "2024-12-15",
    carrier: null,
    tracking_number: null,
    warehouse: "Atlanta Distribution Center (ATL-DC1)",
    line_items: [
      { sku: "COMPRESSOR-5TON", description: "Scroll Compressor, 5-Ton, R-410A", quantity: 10, unit_price: 1245.0, status: "backordered" },
      { sku: "COIL-EVAP-5TON", description: "Evaporator Coil, 5-Ton", quantity: 10, unit_price: 485.0, status: "backordered" },
    ],
    total: 17920.0,
    payment_terms: "Net 60",
    payment_status: "pending",
    notes: "Manufacturer supply chain disruption. Compressors expected from factory 2024-12-05. SLA credit of 2% applied.",
  },
  "PO-2024-8512": {
    po_number: "PO-2024-8512",
    status: "delivered",
    customer_name: "Pacific Coast Electronics",
    order_date: "2024-10-10",
    ship_date: "2024-10-14",
    estimated_delivery: "2024-10-18",
    actual_delivery: "2024-10-17",
    carrier: "UPS Freight",
    tracking_number: "1Z999AA10123456784",
    warehouse: "Reno Distribution Center (RNO-DC2)",
    line_items: [
      { sku: "PCB-FR4-6L", description: "6-Layer FR-4 PCB Blank, 12x18 inch", quantity: 1000, unit_price: 3.45, status: "delivered" },
      { sku: "SMD-RES-KIT-0805", description: "SMD Resistor Kit, 0805, 170 values", quantity: 20, unit_price: 28.5, status: "delivered" },
    ],
    total: 4165.0,
    payment_terms: "Net 30",
    payment_status: "paid",
    notes: "Delivered one day early. Signed by J. Tanaka at receiving dock.",
  },
  "PO-2024-7891": {
    po_number: "PO-2024-7891",
    status: "cancelled",
    customer_name: "Redwood Agricultural Equipment",
    order_date: "2024-09-15",
    line_items: [
      { sku: "PUMP-CENT-15HP", description: "Centrifugal Irrigation Pump, 15HP", quantity: 3, unit_price: 4250.0, status: "cancelled" },
    ],
    total: 12750.0,
    payment_terms: "Net 30",
    payment_status: "refunded",
    notes: "Cancelled by customer on 2024-09-20. Reason: project funding withdrawn. Full refund processed 2024-09-25.",
  },
};

// ──────────────────────────────────────────────────────────────
// Tool Definition
// ──────────────────────────────────────────────────────────────

const tools = [
  {
    name: "get_order_status",
    description:
      "Look up the status of a B2B purchase order by PO number. Returns order status, line items, tracking info, and payment status.",
    input_schema: {
      type: "object",
      properties: {
        po_number: {
          type: "string",
          description: "The purchase order number, formatted as PO-YYYY-NNNN (e.g., PO-2024-8847)",
        },
      },
      required: ["po_number"],
    },
  },
];

// ──────────────────────────────────────────────────────────────
// Tool Implementation
// ──────────────────────────────────────────────────────────────

function getOrderStatus(poNumber) {
  const normalized = poNumber.trim().toUpperCase();
  const record = ORDER_RECORDS[normalized];

  if (!record) {
    return {
      error: `No order found for PO number '${normalized}'.`,
      suggestion: "Please verify the PO number format (PO-YYYY-NNNN) and try again.",
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
    "You are a B2B ecommerce order status assistant. " +
    "When a user provides a purchase order number (formatted like PO-YYYY-NNNN), " +
    "use the get_order_status tool to look up the order. Then explain the result " +
    "clearly, including current status, tracking info, and expected delivery. " +
    "If there are issues, explain and suggest next steps. " +
    "If the user asks a general question, respond without calling tools.";

  const messages = [];

  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout,
  });

  console.log("=".repeat(60));
  console.log("  B2B Order Status Bot (Node.js)");
  console.log("  Enter a PO number to check order status.");
  console.log("  Type 'quit' to exit.");
  console.log("=".repeat(60));
  console.log();

  const askQuestion = () => {
    // Bail out if stdin has already ended. askQuestion() recurses after each
    // turn, and when input is redirected (or Ctrl-D lands mid-request) readline
    // closes while the turn is still awaiting the API -- the recursive call
    // then throws ERR_USE_AFTER_CLOSE instead of exiting cleanly.
    if (rl.closed) return;

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

            if (toolUseBlock.name === "get_order_status") {
              toolResult = getOrderStatus(toolUseBlock.input.po_number);
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
