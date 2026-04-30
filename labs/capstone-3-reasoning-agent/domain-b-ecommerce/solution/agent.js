/**
 * B2B Ecommerce Order Exception Resolution Agent — ReAct Agent (Node.js Solution)
 *
 * Complete implementation using the Anthropic Node.js SDK.
 */

import Anthropic from "@anthropic-ai/sdk";

const MODEL = "claude-sonnet-4-6";
const MAX_ITERATIONS = 15;

const SYSTEM_PROMPT = `You are a B2B Ecommerce Order Exception Resolution Agent. Your job is to
investigate order exceptions, determine the root cause, propose resolutions,
and draft professional customer notifications.

You MUST follow this reasoning process:
1. FIRST, retrieve the order details to understand the exception type and affected items
2. THEN, investigate the root cause using the appropriate tools:
   - For delayed_shipment: track the shipment, check warehouse inventory
   - For partial_delivery: check warehouse inventory for the short-shipped SKU
   - For pricing_discrepancy: look up the contract pricing agreement
   - For quality_hold: check quality hold status for the affected SKU(s)
3. NEXT, gather any additional context needed (e.g., contract pricing for SLA penalties)
4. FINALLY, draft a customer notification with root cause, resolution, and timeline

Think step-by-step. Consider SLA penalties, alternative fulfillment, and customer impact.`;

// ---------------------------------------------------------------------------
// Tool Schemas
// ---------------------------------------------------------------------------
const TOOL_SCHEMAS = [
  {
    name: "get_order_details",
    description: "Retrieve full details for an order including line items, shipping info, exception type, customer data, and contract reference. Use this FIRST.",
    input_schema: {
      type: "object",
      properties: { order_id: { type: "string", description: "The order ID" } },
      required: ["order_id"],
    },
  },
  {
    name: "query_warehouse_inventory",
    description: "Query current inventory levels at a specific warehouse for a given SKU.",
    input_schema: {
      type: "object",
      properties: {
        warehouse_id: { type: "string", description: "The warehouse ID" },
        sku: { type: "string", description: "The product SKU to check" },
      },
      required: ["warehouse_id", "sku"],
    },
  },
  {
    name: "track_shipment",
    description: "Get real-time tracking information for a shipment.",
    input_schema: {
      type: "object",
      properties: { tracking_number: { type: "string", description: "The carrier tracking number" } },
      required: ["tracking_number"],
    },
  },
  {
    name: "get_contract_pricing",
    description: "Look up the contract pricing agreement for a customer.",
    input_schema: {
      type: "object",
      properties: { contract_id: { type: "string", description: "The contract ID" } },
      required: ["contract_id"],
    },
  },
  {
    name: "check_quality_hold_status",
    description: "Check if a SKU has any active quality holds.",
    input_schema: {
      type: "object",
      properties: { sku: { type: "string", description: "The product SKU" } },
      required: ["sku"],
    },
  },
  {
    name: "draft_customer_notification",
    description: "Draft a professional customer notification email about the order exception. Use as FINAL step.",
    input_schema: {
      type: "object",
      properties: {
        order_id: { type: "string" },
        customer_name: { type: "string" },
        contact_name: { type: "string" },
        contact_email: { type: "string" },
        exception_summary: { type: "string" },
        root_cause: { type: "string" },
        resolution: { type: "string" },
        sla_impact: { type: "string" },
      },
      required: ["order_id", "customer_name", "contact_name", "contact_email", "exception_summary", "root_cause", "resolution", "sla_impact"],
    },
  },
];

// ---------------------------------------------------------------------------
// Mock Data (condensed for JS — key order for the test scenario)
// ---------------------------------------------------------------------------
const ORDERS = {
  "ORD-2024-1847": {
    order_id: "ORD-2024-1847", po_number: "PO-88421", customer_id: "CUST-4420",
    customer_name: "Meridian Industrial Supply", order_date: "2024-11-15",
    promised_delivery: "2024-11-22", status: "exception",
    exception_type: "delayed_shipment",
    exception_details: "Carrier pickup missed — truck not dispatched due to routing error",
    priority: "high", total_value: 14750.0,
    lines: [
      { line: 1, sku: "HYD-PUMP-3200", description: "Hydraulic Pump Assembly 3200 PSI", qty_ordered: 5, qty_shipped: 0, unit_price: 1850.0, warehouse: "WH-EAST" },
      { line: 2, sku: "FLT-KIT-STD", description: "Standard Filter Replacement Kit", qty_ordered: 25, qty_shipped: 0, unit_price: 120.0, warehouse: "WH-EAST" },
      { line: 3, sku: "SEAL-VIT-050", description: "Viton O-Ring Seal Set 50mm", qty_ordered: 100, qty_shipped: 0, unit_price: 8.50, warehouse: "WH-EAST" },
    ],
    shipping: { carrier: "FastFreight Logistics", carrier_code: "FFL", service_level: "2-Day Priority", tracking_number: "FFL-9928374650", ship_from: "WH-EAST" },
    contract_id: "CTR-2024-0091", sla_penalty_clause: true, sla_penalty_rate: 0.02,
    contact_email: "procurement@meridian-industrial.com", contact_name: "Janet Kowalski",
  },
};

const WAREHOUSE_INVENTORY = {
  "WH-EAST": {
    warehouse_id: "WH-EAST", name: "Eastern Distribution Center", location: "Edison, NJ",
    inventory: {
      "HYD-PUMP-3200": { qty_available: 12, qty_reserved: 5, qty_on_hold: 20, reorder_point: 10, lead_time_days: 21 },
      "FLT-KIT-STD": { qty_available: 340, qty_reserved: 25, qty_on_hold: 0, reorder_point: 50, lead_time_days: 7 },
      "SEAL-VIT-050": { qty_available: 1200, qty_reserved: 100, qty_on_hold: 0, reorder_point: 200, lead_time_days: 5 },
    },
  },
};

const CARRIER_TRACKING = {
  "FFL-9928374650": {
    tracking_number: "FFL-9928374650", carrier: "FastFreight Logistics", status: "pickup_missed",
    status_detail: "Pickup scheduled for 2024-11-18 was not completed. Routing error — truck dispatched to wrong facility.",
    estimated_delivery: null, origin: "WH-EAST (Edison, NJ)", destination: "Meridian Industrial Supply, Cincinnati, OH",
    events: [
      { timestamp: "2024-11-15T14:30:00Z", event: "Shipment created", location: "Edison, NJ" },
      { timestamp: "2024-11-18T06:00:00Z", event: "Pickup scheduled", location: "Edison, NJ" },
      { timestamp: "2024-11-18T18:00:00Z", event: "Pickup missed — routing error", location: "Edison, NJ" },
    ],
    service_disruption: false,
  },
};

const CONTRACT_PRICING = {
  "CTR-2024-0091": {
    contract_id: "CTR-2024-0091", customer_name: "Meridian Industrial Supply",
    effective_date: "2024-01-01", expiration_date: "2024-12-31", status: "active",
    pricing_tiers: {
      "HYD-PUMP-3200": { contract_price: 1750.0, list_price: 1850.0, min_qty: 5, tier_discount: "5.4%" },
      "FLT-KIT-STD": { contract_price: 105.0, list_price: 120.0, min_qty: 20, tier_discount: "12.5%" },
      "SEAL-VIT-050": { contract_price: 7.25, list_price: 8.50, min_qty: 50, tier_discount: "14.7%" },
    },
    volume_rebate: { threshold: 100000, rebate_pct: 0.02, ytd_spend: 87500 },
  },
};

const QUALITY_HOLDS = {};

// ---------------------------------------------------------------------------
// Tool Handlers
// ---------------------------------------------------------------------------
function getOrderDetails({ order_id }) {
  return ORDERS[order_id] || { error: `Order ${order_id} not found` };
}

function queryWarehouseInventory({ warehouse_id, sku }) {
  const wh = WAREHOUSE_INVENTORY[warehouse_id];
  if (!wh) return { error: `Warehouse ${warehouse_id} not found` };
  const inv = wh.inventory[sku];
  if (!inv) return { error: `SKU ${sku} not found at ${warehouse_id}` };
  return { warehouse_id, warehouse_name: wh.name, location: wh.location, sku, ...inv };
}

function trackShipment({ tracking_number }) {
  return CARRIER_TRACKING[tracking_number] || { error: `Tracking ${tracking_number} not found` };
}

function getContractPricing({ contract_id }) {
  return CONTRACT_PRICING[contract_id] || { error: `Contract ${contract_id} not found` };
}

function checkQualityHoldStatus({ sku }) {
  const holds = Object.values(QUALITY_HOLDS).filter((h) => h.sku === sku);
  if (holds.length === 0) return { sku, holds: [], status: "no_active_holds" };
  return { sku, status: "holds_found", hold_count: holds.length, holds };
}

function draftCustomerNotification({ order_id, customer_name, contact_name, contact_email, exception_summary, root_cause, resolution, sla_impact }) {
  const body = `Dear ${contact_name},

We are writing to provide you with an update regarding your order ${order_id}.

ISSUE SUMMARY
${exception_summary}

ROOT CAUSE
${root_cause}

RESOLUTION & NEXT STEPS
${resolution}

SLA & CREDIT INFORMATION
${sla_impact}

We sincerely apologize for the inconvenience. Your account representative will follow up within 24 hours.

Best regards,
Order Management Team`;

  return { to: contact_email, subject: `Order Update: ${order_id} — Action Required`, body, status: "draft_ready" };
}

const TOOL_HANDLERS = {
  get_order_details: getOrderDetails,
  query_warehouse_inventory: queryWarehouseInventory,
  track_shipment: trackShipment,
  get_contract_pricing: getContractPricing,
  check_quality_hold_status: checkQualityHoldStatus,
  draft_customer_notification: draftCustomerNotification,
};

function executeTool(name, input) {
  const handler = TOOL_HANDLERS[name];
  if (!handler) return JSON.stringify({ error: `Unknown tool: ${name}` });
  try {
    return JSON.stringify(handler(input), null, 2);
  } catch (e) {
    return JSON.stringify({ error: `Tool execution failed: ${e.message}` });
  }
}

// ---------------------------------------------------------------------------
// ReAct Agent Loop
// ---------------------------------------------------------------------------
async function runAgent(userQuery) {
  const client = new Anthropic();
  const messages = [{ role: "user", content: userQuery }];

  console.log("\n" + "=".repeat(70));
  console.log("REASONING TRACE");
  console.log("=".repeat(70));

  for (let step = 1; step <= MAX_ITERATIONS; step++) {
    let response;
    try {
      response = await client.messages.create({
        model: MODEL,
        max_tokens: 4096,
        system: SYSTEM_PROMPT,
        tools: TOOL_SCHEMAS,
        messages,
      });
    } catch (e) {
      console.error(`\n[ERROR] API call failed: ${e.message}`);
      return `Agent error: ${e.message}`;
    }

    const toolUseBlocks = [];
    const textParts = [];

    for (const block of response.content) {
      if (block.type === "text") {
        textParts.push(block.text);
        console.log(`\n--- Step ${step} ---`);
        console.log(`[THINK] ${block.text}`);
      } else if (block.type === "tool_use") {
        toolUseBlocks.push(block);
        console.log(`\n--- Step ${step} ---`);
        console.log(`[ACT] Calling tool: ${block.name}`);
        console.log(`      Args: ${JSON.stringify(block.input, null, 2)}`);
      }
    }

    if (response.stop_reason === "end_turn") {
      const finalText = textParts.join("\n");
      console.log(`\n[ANSWER] ${finalText.substring(0, 500)}...`);
      return finalText;
    }

    if (response.stop_reason === "tool_use" && toolUseBlocks.length > 0) {
      messages.push({ role: "assistant", content: response.content });
      const toolResults = toolUseBlocks.map((block) => {
        const result = executeTool(block.name, block.input);
        console.log(`[OBSERVE] ${block.name} returned: ${result.substring(0, 300)}...`);
        return { type: "tool_result", tool_use_id: block.id, content: result };
      });
      messages.push({ role: "user", content: toolResults });
    }
  }

  return "Agent reached maximum iterations without completing.";
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------
const query = "Investigate the exception on order ORD-2024-1847 and resolve it.";

runAgent(query).then((result) => {
  console.log("\n" + "=".repeat(70));
  console.log("FINAL RESULT");
  console.log("=".repeat(70));
  console.log(result);
});
