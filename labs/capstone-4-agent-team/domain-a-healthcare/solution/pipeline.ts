// pipeline.ts — Multi-Agent Pre-Auth Pipeline Orchestrator (Capstone 4-A)
//
// Mirrors pipeline.py. All four agents go through the same `runAgent`
// runner so the circuit breaker fires at every transition.

import Anthropic from "@anthropic-ai/sdk";
import * as readline from "readline";

import {
  validateAuthRequest, verifyMemberEligibility, verifyProvider,
  fetchClinicalPolicy, evaluateCriterion,
  computeDecisionConfidence, finalizeDetermination,
  draftDeterminationLetter, sendNotification, checkHipaaCompliance,
} from "./mock_tools";

const client = new Anthropic();
const MODEL = "claude-sonnet-4-6";

export interface PipelineState {
  request_id: string;
  stage: string;
  raw_request: any;
  intake_output?: any;
  criteria_output?: any;
  decision_output?: any;
  communication_output?: any;
  circuit_breaker: {
    consecutive_failures: number;
    threshold: number;
    status: string;
  };
}

export function createState(
  requestId: string, rawRequest: any = {}
): PipelineState {
  return {
    request_id: requestId, stage: "intake",
    raw_request: rawRequest,
    circuit_breaker: {
      consecutive_failures: 0, threshold: 3, status: "healthy",
    },
  };
}

export function checkCircuitBreaker(state: PipelineState): boolean {
  return state.circuit_breaker.status === "tripped";
}

export function recordFailure(state: PipelineState): void {
  state.circuit_breaker.consecutive_failures++;
  if (state.circuit_breaker.consecutive_failures >=
      state.circuit_breaker.threshold) {
    state.circuit_breaker.status = "tripped";
    console.log("[CIRCUIT BREAKER] TRIPPED!");
  }
}

export function recordSuccess(state: PipelineState): void {
  state.circuit_breaker.consecutive_failures = 0;
}

// ── Generic agent runner ─────────────────────────────────────────
async function runAgent(
  name: string, system: string, tools: any[],
  handlers: Record<string, (a: any) => any>,
  userMessage: string, state: PipelineState
): Promise<any> {
  if (checkCircuitBreaker(state)) {
    return { error: "CIRCUIT_BREAKER_TRIPPED" };
  }
  console.log(`\n[${name}] Starting...`);
  const history: any[] = [{ role: "user", content: userMessage }];
  try {
    while (true) {
      const resp = await client.messages.create({
        model: MODEL, max_tokens: 1500,
        system, tools, messages: history,
      } as any);
      if (resp.stop_reason === "tool_use") {
        history.push({ role: "assistant", content: resp.content });
        const results = (resp.content as any[])
          .filter(b => b.type === "tool_use")
          .map(b => ({
            type: "tool_result",
            tool_use_id: b.id,
            content: JSON.stringify(
              handlers[b.name]
                ? handlers[b.name](b.input)
                : { error: "UNKNOWN_TOOL" }),
          }));
        history.push({ role: "user", content: results });
        continue;
      }
      const text = (resp.content as any[])
        .filter(b => b.type === "text")
        .map(b => b.text).join("\n");
      console.log(`[${name}] Complete.`);
      recordSuccess(state);
      return { text };
    }
  } catch (e: any) {
    console.log(`[${name}] FAILED: ${e.message}`);
    recordFailure(state);
    return { error: e.message };
  }
}

// ── Pipeline orchestrator ────────────────────────────────────────
export async function runPipeline(rawRequest: any): Promise<PipelineState> {
  const state = createState(
    rawRequest.request_id ||
      `AR-${new Date().toISOString().replace(/\D/g, "").slice(0, 14)}`,
    rawRequest);

  // Agent 1: Intake — direct calls (deterministic) plus a runAgent
  // log entry so the circuit breaker is exercised.
  const validation = validateAuthRequest(rawRequest);
  const member = verifyMemberEligibility(rawRequest.member_id);
  state.intake_output = {
    validated: validation.validated,
    member_verified: !member.error,
    procedure_code: rawRequest.procedure_code,
    diagnosis_codes: rawRequest.diagnosis_codes,
    clinical_notes_summary: rawRequest.clinical_notes?.slice(0, 200),
  };
  state.stage = "clinical_criteria";

  // Agent 2: Clinical Criteria — direct evaluation
  const policy = fetchClinicalPolicy(state.intake_output.procedure_code);
  const criteriaEval = (policy.criteria || []).map((c: any) => {
    const ev = evaluateCriterion(c.id, rawRequest.clinical_notes || "");
    return {
      criterion: c.id, met: ev.met,
      confidence: ev.confidence, evidence: ev.evidence,
      required: c.required,
    };
  });
  state.criteria_output = {
    policy_id: policy.policy_id,
    criteria_evaluation: criteriaEval,
  };
  state.stage = "decision";

  // Agent 3: Decision — LLM-driven via runAgent
  const decisionScratch: any = {};
  const decisionTools = [
    {
      name: "compute_decision_confidence",
      description: "Compute overall confidence and a preliminary " +
        "recommendation.",
      input_schema: {
        type: "object",
        properties: {
          criteria_results: {
            type: "array", items: { type: "object" },
          },
          network_status: { type: "string" },
          benefit_summary: { type: "object" },
        },
        required: ["criteria_results", "network_status"],
      },
    },
  ];
  const decisionHandlers = {
    compute_decision_confidence: (a: any) => {
      const out = computeDecisionConfidence(
        a.criteria_results || [],
        a.network_status || "in-network",
        a.benefit_summary);
      Object.assign(decisionScratch, out);
      return out;
    },
  };
  const decisionResult = await runAgent(
    "DECISION",
    "You are the Decision Agent. Call compute_decision_confidence " +
      "with the criteria results, then reply with a JSON object: " +
      "{\"determination\": str, \"overall_confidence\": float, " +
      "\"human_review_required\": bool, \"rationale\": str}.",
    decisionTools, decisionHandlers,
    `Determine routing.\n` +
      `criteria_evaluation: ${JSON.stringify(criteriaEval)}\n` +
      `network_status: in-network`,
    state);
  if (decisionResult.error) { state.stage = "error"; return state; }
  state.decision_output = {
    ...decisionScratch,
    determination: decisionScratch.recommendation || "request_info",
  };

  const det = finalizeDetermination(
    state.request_id,
    state.decision_output.determination,
    state.decision_output.rationale || "");

  // Agent 4: Communication — LLM-driven with HIPAA guardrail
  const commScratch: any = {};
  const commTools = [
    {
      name: "draft_determination_letter",
      description: "Draft the determination letter.",
      input_schema: {
        type: "object",
        properties: {
          determination_id: { type: "string" },
          determination: {
            type: "string",
            enum: ["approve", "deny", "request_info"],
          },
        },
        required: ["determination_id", "determination"],
      },
    },
    {
      name: "check_hipaa_compliance",
      description: "Output guardrail. Call BEFORE send_notification.",
      input_schema: {
        type: "object",
        properties: {
          letter_text: { type: "string" },
          determination_type: { type: "string" },
        },
        required: ["letter_text", "determination_type"],
      },
    },
    {
      name: "send_notification",
      description: "Send only after the guardrail returns " +
        "compliant=true.",
      input_schema: {
        type: "object",
        properties: {
          letter_id: { type: "string" },
          channel: { type: "string" },
          recipient: { type: "string" },
        },
        required: ["letter_id", "channel"],
      },
    },
  ];
  const commHandlers = {
    draft_determination_letter: (a: any) => {
      const out = draftDeterminationLetter(
        a.determination_id, a.determination);
      commScratch.letter = out; return out;
    },
    check_hipaa_compliance: (a: any) => {
      const out = checkHipaaCompliance(
        a.letter_text, a.determination_type || "approve");
      commScratch.hipaa = out; return out;
    },
    send_notification: (a: any) =>
      sendNotification(a.letter_id, a.channel || "portal",
                       a.recipient || "provider@clinic.example"),
  };
  const commResult = await runAgent(
    "COMMUNICATION",
    "You are the Communication Agent. Draft -> check_hipaa_compliance " +
      "-> send_notification. Only send if compliant=true.",
    commTools, commHandlers,
    `Send notice for ${state.request_id}.\n` +
      `determination_id: ${det.determination_id}\n` +
      `determination: ${det.determination.toLowerCase()}`,
    state);
  if (commResult.error) { state.stage = "error"; return state; }

  // Belt-and-suspenders: orchestrator re-checks the guardrail.
  const letter = commScratch.letter ||
    draftDeterminationLetter(det.determination_id, det.determination);
  const hipaa = commScratch.hipaa ||
    checkHipaaCompliance(letter.draft_text, det.determination);
  if (!hipaa.compliant) {
    state.communication_output = {
      letter_id: letter.letter_id,
      hipaa_issues: hipaa.issues,
      blocked: true,
    };
    state.stage = "error";
    return state;
  }

  const notif = sendNotification(
    letter.letter_id, "portal", "provider@clinic.example");
  state.communication_output = {
    letter_id: letter.letter_id,
    letter_type: det.determination,
    sent_via: "portal",
    sent_at: notif.sent_at,
    hipaa_compliant: true,
  };
  state.stage = "complete";
  console.log(
    `\n[PIPELINE] Complete! Determination: ${det.determination}`);
  return state;
}

async function main(): Promise<void> {
  const sample = {
    request_id: "AR-2024-09821",
    member_id: "MBR-555-1234",
    provider_npi: "1234567890",
    procedure_code: "27447",
    diagnosis_codes: ["M17.11"],
    clinical_notes:
      "Severe right knee osteoarthritis (M17.11). KL Grade IV. " +
      "8 months PT. WOMAC 68. BMI 31.",
  };

  const rl = readline.createInterface({
    input: process.stdin, output: process.stdout,
  });
  rl.question("\nCommand (demo/quit): ", async (cmd: string) => {
    if (cmd.trim().toLowerCase() === "demo") {
      const state = await runPipeline(sample);
      console.log("\nFinal state:", JSON.stringify(state, null, 2));
    }
    rl.close();
  });
}

if (require.main === module) {
  main();
}
