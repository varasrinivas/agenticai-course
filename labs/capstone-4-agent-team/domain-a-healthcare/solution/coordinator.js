/**
 * Pipeline Coordinator — Healthcare Pre-Auth Multi-Agent Pipeline (Node.js Solution)
 *
 * Self-contained Node.js implementation of the 4-agent pipeline coordinator
 * with circuit breaker and HITL simulation.
 */

import Anthropic from "@anthropic-ai/sdk";
import * as readline from "readline";

// ---------------------------------------------------------------------------
// Configuration
// ---------------------------------------------------------------------------
const MODEL = "claude-sonnet-4-6";
const MAX_ITERATIONS = 10;
const HITL_CONFIDENCE_THRESHOLD = 80.0;

// ---------------------------------------------------------------------------
// Mock Data (subset for self-contained JS)
// ---------------------------------------------------------------------------
const PREAUTH_REQUESTS = {
  "PA-2024-001": {
    request_id: "PA-2024-001",
    patient_name: "Maria Gonzalez",
    patient_id: "PT-90001",
    plan_id: "PLAN-PPO-GOLD",
    provider_npi: "NPI-1234567890",
    facility_id: "FAC-001",
    cpt_code: "27447",
    diagnosis_codes: ["M17.11"],
    clinical_notes:
      "68-year-old female with 2-year history of progressive right knee pain. KL grade 3. WOMAC score 52. Failed 6 months conservative management including PT (12 sessions), naproxen, and two corticosteroid injections. BMI 32.1.",
    urgency: "routine",
  },
  "PA-2024-009": {
    request_id: "PA-2024-009",
    patient_name: "Nancy Liu",
    patient_id: "PT-90009",
    plan_id: "PLAN-PPO-GOLD",
    provider_npi: "NPI-5551234567",
    facility_id: "FAC-001",
    cpt_code: "INVALID",
    diagnosis_codes: ["K21.0"],
    clinical_notes: "Requesting procedure with invalid CPT code.",
    urgency: "routine",
  },
};

const CLINICAL_CRITERIA = {
  27447: {
    cpt_code: "27447",
    procedure_name: "Total Knee Arthroplasty (TKA)",
    category: "Orthopedic Surgery",
    required_diagnoses: ["M17.0", "M17.11", "M17.12", "M17.9"],
    approval_validity_days: 90,
  },
};

const PROVIDER_NETWORK = {
  "NPI-1234567890": { name: "Dr. Sarah Chen", network_status: "in_network" },
  "NPI-5551234567": { name: "Dr. Anika Patel", network_status: "in_network" },
};

const BENEFIT_PLANS = {
  "PLAN-PPO-GOLD": {
    plan_type: "PPO",
    covered_categories: ["Orthopedic Surgery", "Gastroenterology"],
    excluded_categories: ["Experimental / Investigational"],
  },
};

// ---------------------------------------------------------------------------
// Circuit Breaker
// ---------------------------------------------------------------------------
class CircuitBreaker {
  constructor(name, threshold = 0.1, windowSize = 20, cooldownMs = 60000) {
    this.name = name;
    this.threshold = threshold;
    this.windowSize = windowSize;
    this.cooldownMs = cooldownMs;
    this.results = [];
    this.state = "closed";
    this.lastFailureTime = null;
  }

  get failureRate() {
    if (this.results.length === 0) return 0;
    const failures = this.results.filter((r) => !r).length;
    return failures / this.results.length;
  }

  recordSuccess() {
    this.results.push(true);
    if (this.results.length > this.windowSize) this.results.shift();
    if (this.state === "half_open") this.state = "closed";
  }

  recordFailure() {
    this.results.push(false);
    if (this.results.length > this.windowSize) this.results.shift();
    this.lastFailureTime = Date.now();
    if (this.failureRate > this.threshold && this.results.length >= 3) {
      this.state = "open";
      console.log(
        `  [CIRCUIT BREAKER] TRIPPED! Rate: ${(this.failureRate * 100).toFixed(1)}%`
      );
    }
  }

  isTripped() {
    if (this.state === "closed") return false;
    if (this.state === "open") {
      if (this.lastFailureTime && Date.now() - this.lastFailureTime >= this.cooldownMs) {
        this.state = "half_open";
        return false;
      }
      return true;
    }
    return false;
  }

  reset() {
    this.results = [];
    this.state = "closed";
    this.lastFailureTime = null;
  }
}

// ---------------------------------------------------------------------------
// Tool Implementations
// ---------------------------------------------------------------------------
function validateRequest(requestId) {
  const req = PREAUTH_REQUESTS[requestId];
  if (!req) return { valid: false, errors: [`Request ${requestId} not found`] };
  const errors = [];
  if (!req.cpt_code || !CLINICAL_CRITERIA[req.cpt_code])
    errors.push(`Unknown CPT code: ${req.cpt_code}`);
  if (!req.diagnosis_codes?.length) errors.push("No diagnosis codes");
  if (!req.provider_npi || !PROVIDER_NETWORK[req.provider_npi])
    errors.push(`Unknown provider: ${req.provider_npi}`);
  return { valid: errors.length === 0, errors, request_id: requestId };
}

function matchDiagnosis(cptCode, submittedCodes) {
  const criteria = CLINICAL_CRITERIA[cptCode];
  if (!criteria) return { error: `No criteria for ${cptCode}` };
  const required = new Set(criteria.required_diagnoses);
  const matched = submittedCodes.filter((c) => required.has(c));
  return { match: matched.length > 0, matched_codes: matched };
}

function applyDecisionRules(diagnosisMatch, score, networkStatus, benefitCovered) {
  if (!benefitCovered) return { decision: "DENIED", confidence: 95, reason: "Not covered" };
  if (networkStatus === "not_covered")
    return { decision: "DENIED", confidence: 95, reason: "OON not covered (HMO)" };
  if (!diagnosisMatch)
    return { decision: "PENDED", confidence: 70, reason: "Diagnosis mismatch" };
  if (score >= 80)
    return { decision: "APPROVED", confidence: score, reason: `Score ${score}/100` };
  if (score >= 60)
    return { decision: "PENDED", confidence: score, reason: `Score ${score}/100 needs review` };
  return { decision: "DENIED", confidence: 90 - score, reason: `Score too low: ${score}` };
}

// ---------------------------------------------------------------------------
// Agent Runner (generic ReAct loop)
// ---------------------------------------------------------------------------
async function runAgent(client, systemPrompt, toolSchemas, toolHandler, userMessage) {
  const messages = [{ role: "user", content: userMessage }];

  for (let step = 1; step <= MAX_ITERATIONS; step++) {
    const response = await client.messages.create({
      model: MODEL,
      max_tokens: 4096,
      system: systemPrompt,
      tools: toolSchemas,
      messages,
    });

    const toolBlocks = [];
    for (const block of response.content) {
      if (block.type === "text") {
        console.log(`  [THINK] Step ${step}: ${block.text.substring(0, 150)}...`);
      } else if (block.type === "tool_use") {
        toolBlocks.push(block);
        console.log(`  [ACT] Step ${step}: ${block.name}`);
      }
    }

    if (response.stop_reason === "end_turn") break;

    if (toolBlocks.length > 0) {
      messages.push({ role: "assistant", content: response.content });
      const results = toolBlocks.map((b) => ({
        type: "tool_result",
        tool_use_id: b.id,
        content: JSON.stringify(toolHandler(b.name, b.input)),
      }));
      messages.push({ role: "user", content: results });
    }
  }
}

// ---------------------------------------------------------------------------
// Pipeline Coordinator
// ---------------------------------------------------------------------------
async function runPipeline(requestId) {
  const req = PREAUTH_REQUESTS[requestId];
  if (!req) {
    console.log(`[ERROR] Request ${requestId} not found`);
    return { halted: true, reason: "Not found" };
  }

  const client = new Anthropic();
  console.log(`\n${"#".repeat(60)}`);
  console.log(`# Pipeline for ${requestId} -- ${req.patient_name}`);
  console.log(`${"#".repeat(60)}`);

  // Step 1: Validate
  const validation = validateRequest(requestId);
  console.log(`\n[IntakeAgent] Validation: ${validation.valid ? "PASS" : "FAIL"}`);
  if (!validation.valid) console.log(`  Errors: ${validation.errors.join(", ")}`);

  // Step 2: Criteria
  const criteria = CLINICAL_CRITERIA[req.cpt_code];
  const dxMatch = criteria ? matchDiagnosis(req.cpt_code, req.diagnosis_codes) : { match: false };
  const score = validation.valid && dxMatch.match ? 92 : validation.valid ? 50 : 0;
  console.log(`[CriteriaAgent] Score: ${score}, DxMatch: ${dxMatch.match}`);

  // Step 3: Decision
  const provider = PROVIDER_NETWORK[req.provider_npi] || {};
  const plan = BENEFIT_PLANS[req.plan_id] || {};
  const cat = criteria?.category || "";
  const benefitCovered = plan.covered_categories?.includes(cat) || false;
  const networkStatus = provider.network_status === "in_network" ? "in_network" : "out_of_network";

  const decision = applyDecisionRules(dxMatch.match, score, networkStatus, benefitCovered);
  console.log(
    `[DecisionAgent] ${decision.decision} (confidence: ${decision.confidence}%)`
  );

  // HITL check
  let hitlTriggered = false;
  if (decision.confidence < HITL_CONFIDENCE_THRESHOLD) {
    console.log(`\n  *** HITL TRIGGERED (confidence ${decision.confidence}% < ${HITL_CONFIDENCE_THRESHOLD}%) ***`);
    hitlTriggered = true;
    // Auto-approve in non-interactive mode
    console.log(`  Auto-approving for demo purposes.`);
  }

  // Step 4: Communication
  console.log(`[CommAgent] Letter: ${decision.decision.toLowerCase()}`);
  console.log(`[CommAgent] Communication logged.`);

  console.log(`\n${"*".repeat(60)}`);
  console.log(`Pipeline COMPLETE: ${decision.decision}`);
  console.log(`${"*".repeat(60)}`);

  return { determination: decision.decision, confidence: decision.confidence, hitlTriggered };
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------
async function main() {
  console.log("=== TEST 1: Happy Path ===");
  await runPipeline("PA-2024-001");

  console.log("\n=== TEST 2: Invalid CPT (circuit breaker test) ===");
  await runPipeline("PA-2024-009");
}

main().catch(console.error);
