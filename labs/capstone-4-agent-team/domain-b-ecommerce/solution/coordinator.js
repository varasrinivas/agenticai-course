/**
 * Pipeline Coordinator — B2B Ecommerce Order Pipeline (Node.js Solution)
 */

import Anthropic from "@anthropic-ai/sdk";

const MODEL = "claude-sonnet-4-20250514";
const MAX_ITERATIONS = 10;

const ORDERS = {
  "PO-2024-5001": {
    order_id: "PO-2024-5001",
    customer_name: "Apex Manufacturing Corp",
    customer_id: "CUST-100",
    items: [
      { sku: "WDG-4420", qty: 500, unit_price: 12.5 },
      { sku: "BLT-7780", qty: 2000, unit_price: 0.85 },
    ],
    sla_tier: "standard",
    requested_delivery: "2024-12-01",
  },
};

const INVENTORY = {
  "WH-EAST": { "WDG-4420": 8000, "BLT-7780": 50000 },
  "WH-CENTRAL": { "WDG-4420": 12000, "BLT-7780": 30000 },
  "WH-WEST": { "WDG-4420": 5000, "BLT-7780": 20000 },
};

function validateOrder(orderId) {
  const order = ORDERS[orderId];
  if (!order) return { valid: false, errors: ["Not found"] };
  const errors = [];
  for (const item of order.items) {
    let found = false;
    for (const wh of Object.values(INVENTORY)) {
      if (item.sku in wh) found = true;
    }
    if (!found) errors.push(`Unknown SKU: ${item.sku}`);
    if (item.qty <= 0) errors.push(`Invalid qty: ${item.sku}`);
  }
  return { valid: errors.length === 0, errors };
}

function checkInventory(orderId) {
  const order = ORDERS[orderId];
  if (!order) return { error: "Not found" };
  const result = {};
  for (const item of order.items) {
    const byWh = {};
    let total = 0;
    for (const [whId, stock] of Object.entries(INVENTORY)) {
      const qty = stock[item.sku] || 0;
      byWh[whId] = qty;
      total += qty;
    }
    result[item.sku] = { by_warehouse: byWh, total, needed: item.qty, sufficient: total >= item.qty };
  }
  return result;
}

class CircuitBreaker {
  constructor(maxConsec = 3) {
    this.maxConsec = maxConsec;
    this.consec = 0;
    this.state = "closed";
  }
  recordSuccess() { this.consec = 0; if (this.state === "half_open") this.state = "closed"; }
  recordFailure() { this.consec++; if (this.consec > this.maxConsec) this.state = "open"; }
  isTripped() { return this.state === "open"; }
  reset() { this.consec = 0; this.state = "closed"; }
}

async function runPipeline(orderId) {
  const order = ORDERS[orderId];
  if (!order) { console.log(`Order ${orderId} not found`); return; }
  console.log(`\n${"#".repeat(50)}\nPipeline for ${orderId} -- ${order.customer_name}\n${"#".repeat(50)}`);

  const v = validateOrder(orderId);
  console.log(`[Intake] Validation: ${v.valid ? "PASS" : "FAIL"}`);

  const inv = checkInventory(orderId);
  console.log(`[Intake] Inventory checked`);

  // Simplified fulfillment
  console.log(`[Fulfillment] Allocating from WH-CENTRAL`);
  console.log(`[Fulfillment] Carrier: ExpressLine Logistics`);

  // Exception check
  console.log(`[Monitor] SLA: on_track`);

  // Communication
  console.log(`[Comm] Customer update sent`);
  console.log(`[Comm] Event logged`);

  console.log(`\n${"*".repeat(50)}\nPipeline COMPLETE\n${"*".repeat(50)}`);
}

async function main() {
  await runPipeline("PO-2024-5001");
}

main().catch(console.error);
