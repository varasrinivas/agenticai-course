/**
 * Healthcare Pre-Authorization Decision Support Agent — ReAct Agent (Node.js Solution)
 *
 * Complete implementation of the ReAct loop using the Anthropic Node.js SDK.
 */

import Anthropic from "@anthropic-ai/sdk";

// ---------------------------------------------------------------------------
// Configuration
// ---------------------------------------------------------------------------
const MODEL = "claude-sonnet-4-6";
const MAX_ITERATIONS = 15;

const SYSTEM_PROMPT = `You are a Healthcare Pre-Authorization Decision Support Agent. Your job is to
process pre-authorization requests by systematically gathering and analyzing information.

You MUST follow this reasoning process:
1. FIRST, look up the clinical criteria for the requested procedure (CPT code)
2. THEN, verify that the submitted diagnosis codes match the required diagnoses
3. NEXT, check the provider and facility network status for the patient's plan
4. THEN, retrieve the patient's benefit summary to confirm coverage
5. FINALLY, generate an authorization recommendation based on ALL gathered evidence

Think step-by-step. After each tool call, analyze the result before deciding your next action.
When you have gathered all necessary information, use the generate_auth_recommendation tool
to produce your final decision.

Always explain your reasoning clearly. If you find issues (e.g., out-of-network provider,
excluded procedure category), note them and factor them into your recommendation.

Do NOT skip steps. Even if the answer seems obvious, gather ALL evidence first.`;

// ---------------------------------------------------------------------------
// Tool Schemas
// ---------------------------------------------------------------------------
const TOOL_SCHEMAS = [
  {
    name: "lookup_clinical_criteria",
    description:
      "Look up the clinical criteria required for pre-authorization of a specific procedure. Returns the required diagnoses, clinical criteria checklist, required documentation, and approval validity period. Use this FIRST.",
    input_schema: {
      type: "object",
      properties: {
        cpt_code: {
          type: "string",
          description: "The CPT procedure code to look up",
        },
      },
      required: ["cpt_code"],
    },
  },
  {
    name: "verify_diagnosis_match",
    description:
      "Verify whether the submitted diagnosis code(s) match the required diagnoses for the requested procedure.",
    input_schema: {
      type: "object",
      properties: {
        cpt_code: { type: "string", description: "The CPT procedure code" },
        submitted_diagnosis_codes: {
          type: "array",
          items: { type: "string" },
          description: "List of ICD-10 diagnosis codes submitted with the request",
        },
      },
      required: ["cpt_code", "submitted_diagnosis_codes"],
    },
  },
  {
    name: "check_network_status",
    description:
      "Check whether a provider and facility are in-network for the patient's plan.",
    input_schema: {
      type: "object",
      properties: {
        provider_npi: { type: "string", description: "The provider's NPI number" },
        facility_id: { type: "string", description: "The facility ID" },
        plan_id: { type: "string", description: "The patient's benefit plan ID" },
      },
      required: ["provider_npi", "facility_id", "plan_id"],
    },
  },
  {
    name: "get_benefit_summary",
    description:
      "Retrieve the patient's benefit plan summary including deductible status, coinsurance rates, out-of-pocket maximum, and whether the procedure category is covered.",
    input_schema: {
      type: "object",
      properties: {
        plan_id: { type: "string", description: "The patient's benefit plan ID" },
        procedure_category: {
          type: "string",
          description: "The category of the procedure",
        },
      },
      required: ["plan_id", "procedure_category"],
    },
  },
  {
    name: "generate_auth_recommendation",
    description:
      "Generate a pre-authorization recommendation based on all gathered information. Use this as the FINAL step.",
    input_schema: {
      type: "object",
      properties: {
        cpt_code: { type: "string", description: "The CPT procedure code" },
        diagnosis_match: {
          type: "boolean",
          description: "Whether the diagnosis codes match",
        },
        network_status: {
          type: "string",
          enum: ["in_network", "out_of_network", "not_covered"],
          description: "The provider/facility network status",
        },
        benefit_covered: {
          type: "boolean",
          description: "Whether the procedure category is covered",
        },
        clinical_notes_summary: {
          type: "string",
          description: "Brief summary of clinical notes",
        },
      },
      required: [
        "cpt_code",
        "diagnosis_match",
        "network_status",
        "benefit_covered",
        "clinical_notes_summary",
      ],
    },
  },
];

// ---------------------------------------------------------------------------
// Mock Data (inline for self-contained JS solution)
// ---------------------------------------------------------------------------
const CLINICAL_CRITERIA = {
  27447: {
    cpt_code: "27447",
    procedure_name: "Total Knee Arthroplasty (TKA)",
    category: "Orthopedic Surgery",
    required_diagnoses: ["M17.0", "M17.11", "M17.12", "M17.9"],
    diagnosis_descriptions: {
      "M17.0": "Bilateral primary osteoarthritis of knee",
      "M17.11": "Primary osteoarthritis, right knee",
      "M17.12": "Primary osteoarthritis, left knee",
      "M17.9": "Osteoarthritis of knee, unspecified",
    },
    criteria: [
      "Documented failure of at least 3 months of conservative treatment",
      "Conservative treatments must include physical therapy, NSAIDs, and at least one corticosteroid injection",
      "Radiographic evidence of moderate to severe joint space narrowing (Kellgren-Lawrence grade 3 or 4)",
      "Functional impairment documented by validated outcome measure (e.g., WOMAC score >= 39)",
      "BMI < 40 or documentation of weight management programme enrollment",
    ],
    required_documentation: [
      "Office visit notes from the past 6 months",
      "Imaging reports (X-ray or MRI within 12 months)",
      "Physical therapy progress notes",
      "Conservative treatment log",
    ],
    approval_validity_days: 90,
    peer_review_threshold: "auto_approve_if_all_criteria_met",
  },
  99999: {
    cpt_code: "99999",
    procedure_name: "Experimental Regenerative Cartilage Implant",
    category: "Experimental / Investigational",
    required_diagnoses: ["M17.11", "M17.12"],
    criteria: [
      "EXPERIMENTAL — Not covered under standard benefit plans",
      "Requires medical director review",
    ],
    approval_validity_days: 0,
    peer_review_threshold: "medical_director_review_required",
  },
};

const PROVIDER_NETWORK = {
  "NPI-1234567890": {
    npi: "NPI-1234567890",
    name: "Dr. Sarah Chen",
    specialty: "Orthopedic Surgery",
    network_status: "in_network",
    network_tier: "preferred",
    board_certified: true,
    quality_score: 4.7,
  },
  "NPI-9876543210": {
    npi: "NPI-9876543210",
    name: "Dr. James Morton",
    specialty: "Orthopedic Surgery",
    network_status: "out_of_network",
    network_tier: null,
    board_certified: true,
    quality_score: 4.9,
  },
};

const FACILITIES = {
  "FAC-001": {
    id: "FAC-001",
    name: "Valley Medical Center",
    network_status: "in_network",
    type: "Hospital — Acute Care",
  },
  "FAC-005": {
    id: "FAC-005",
    name: "Summit Specialty Hospital",
    network_status: "out_of_network",
    type: "Specialty Hospital",
  },
};

const BENEFIT_PLANS = {
  "PLAN-PPO-GOLD": {
    plan_id: "PLAN-PPO-GOLD",
    plan_name: "PPO Gold Plus",
    plan_type: "PPO",
    in_network_deductible: 500,
    in_network_deductible_met: 500,
    in_network_coinsurance: 0.1,
    in_network_oop_max: 4000,
    out_of_network_deductible: 2000,
    out_of_network_deductible_met: 750,
    out_of_network_coinsurance: 0.4,
    out_of_network_oop_max: 12000,
    current_oop_spent: 1200,
    covered_categories: [
      "Orthopedic Surgery",
      "Gastroenterology",
      "Diagnostic Imaging",
      "Pain Management",
    ],
    excluded_categories: ["Experimental / Investigational", "Cosmetic Surgery"],
    notes: "Standard employer group plan with comprehensive surgical coverage.",
  },
  "PLAN-HMO-BASIC": {
    plan_id: "PLAN-HMO-BASIC",
    plan_name: "HMO Basic",
    plan_type: "HMO",
    in_network_deductible: 1500,
    in_network_deductible_met: 400,
    in_network_coinsurance: 0.2,
    in_network_oop_max: 7500,
    current_oop_spent: 800,
    covered_categories: [
      "Orthopedic Surgery",
      "Gastroenterology",
      "Diagnostic Imaging",
      "Pain Management",
    ],
    excluded_categories: ["Experimental / Investigational", "Cosmetic Surgery"],
    notes: "HMO plan — out-of-network services NOT covered except emergencies.",
  },
};

// ---------------------------------------------------------------------------
// Tool Handlers
// ---------------------------------------------------------------------------
function lookupClinicalCriteria({ cpt_code }) {
  const criteria = CLINICAL_CRITERIA[cpt_code];
  if (!criteria) return { error: `No criteria found for CPT code ${cpt_code}` };
  return criteria;
}

function verifyDiagnosisMatch({ cpt_code, submitted_diagnosis_codes }) {
  const criteria = CLINICAL_CRITERIA[cpt_code];
  if (!criteria) return { error: `No criteria found for CPT code ${cpt_code}` };

  const required = new Set(criteria.required_diagnoses);
  const matched = submitted_diagnosis_codes.filter((c) => required.has(c));
  const unmatched = submitted_diagnosis_codes.filter((c) => !required.has(c));
  const details = {};
  for (const code of matched) {
    details[code] = criteria.diagnosis_descriptions?.[code] || "Description not available";
  }

  return {
    match: matched.length > 0,
    matched_codes: matched,
    unmatched_codes: unmatched,
    required_codes: criteria.required_diagnoses,
    details,
    procedure_name: criteria.procedure_name,
  };
}

function checkNetworkStatus({ provider_npi, facility_id, plan_id }) {
  const provider = PROVIDER_NETWORK[provider_npi];
  if (!provider) return { error: `Provider ${provider_npi} not found` };
  const facility = FACILITIES[facility_id];
  if (!facility) return { error: `Facility ${facility_id} not found` };
  const plan = BENEFIT_PLANS[plan_id];
  if (!plan) return { error: `Plan ${plan_id} not found` };

  const providerIn = provider.network_status === "in_network";
  const facilityIn = facility.network_status === "in_network";

  let combined_status, status_detail;
  if (plan.plan_type === "HMO" && (!providerIn || !facilityIn)) {
    combined_status = "not_covered";
    status_detail = "HMO plan does not cover out-of-network services.";
  } else if (!providerIn || !facilityIn) {
    combined_status = "out_of_network";
    status_detail = "Provider or facility is out-of-network. Higher cost sharing applies.";
  } else {
    combined_status = "in_network";
    status_detail = "Both provider and facility are in-network.";
  }

  return { combined_status, status_detail, provider, facility, plan_type: plan.plan_type };
}

function getBenefitSummary({ plan_id, procedure_category }) {
  const plan = BENEFIT_PLANS[plan_id];
  if (!plan) return { error: `Plan ${plan_id} not found` };

  const isCovered = plan.covered_categories.includes(procedure_category);
  const isExcluded = plan.excluded_categories.includes(procedure_category);

  return {
    plan_name: plan.plan_name,
    plan_type: plan.plan_type,
    category_covered: isCovered,
    category_excluded: isExcluded,
    in_network: {
      deductible: plan.in_network_deductible,
      deductible_met: plan.in_network_deductible_met,
      remaining_deductible: Math.max(0, plan.in_network_deductible - plan.in_network_deductible_met),
      coinsurance: `${plan.in_network_coinsurance * 100}%`,
      oop_max: plan.in_network_oop_max,
      current_oop_spent: plan.current_oop_spent,
    },
    notes: plan.notes,
    ...(isExcluded && {
      exclusion_note: `'${procedure_category}' is explicitly excluded from this plan.`,
    }),
  };
}

function generateAuthRecommendation({
  cpt_code,
  diagnosis_match,
  network_status,
  benefit_covered,
  clinical_notes_summary,
}) {
  const criteria = CLINICAL_CRITERIA[cpt_code] || {};

  if (!benefit_covered) {
    return {
      recommendation: "DENIED",
      reason: "Procedure category excluded from benefit plan.",
      conditions: ["Patient may appeal", "May request Medical Director exception"],
      peer_review_required: false,
      approval_validity_days: 0,
    };
  }
  if (network_status === "not_covered") {
    return {
      recommendation: "DENIED",
      reason: "HMO plan does not cover out-of-network services.",
      conditions: ["Must select in-network provider"],
      peer_review_required: false,
      approval_validity_days: 0,
    };
  }
  if (!diagnosis_match) {
    return {
      recommendation: "PENDED",
      reason: "Diagnosis codes do not match required criteria. Pended for peer review.",
      conditions: ["Provider may submit corrected codes"],
      peer_review_required: true,
      approval_validity_days: 0,
    };
  }
  if (network_status === "out_of_network") {
    return {
      recommendation: "APPROVED",
      reason: "Criteria met. Approved at out-of-network benefit levels.",
      conditions: ["Higher cost sharing applies", "Balance billing may apply"],
      peer_review_required: false,
      approval_validity_days: criteria.approval_validity_days || 60,
    };
  }

  return {
    recommendation: "APPROVED",
    reason: `All criteria met. In-network. ${clinical_notes_summary}`,
    conditions: [
      `Authorization valid for ${criteria.approval_validity_days || 60} days`,
      "Pre-operative clearance required",
    ],
    peer_review_required: false,
    approval_validity_days: criteria.approval_validity_days || 60,
  };
}

const TOOL_HANDLERS = {
  lookup_clinical_criteria: lookupClinicalCriteria,
  verify_diagnosis_match: verifyDiagnosisMatch,
  check_network_status: checkNetworkStatus,
  get_benefit_summary: getBenefitSummary,
  generate_auth_recommendation: generateAuthRecommendation,
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
        console.log(
          `[OBSERVE] ${block.name} returned: ${result.substring(0, 300)}...`
        );
        return {
          type: "tool_result",
          tool_use_id: block.id,
          content: result,
        };
      });

      messages.push({ role: "user", content: toolResults });
    }
  }

  return "Agent reached maximum iterations without completing.";
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------
const query = `Process this pre-authorization request:

Patient: Maria Gonzalez (DOB: 1958-03-14)
Plan: PLAN-PPO-GOLD
Provider: NPI-1234567890
Facility: FAC-001
Procedure: CPT 27447 (Total Knee Arthroplasty)
Diagnosis: M17.11 (Primary osteoarthritis, right knee)

Clinical Notes: Patient is a 68-year-old female with 2-year history of progressive
right knee pain. Kellgren-Lawrence grade 3 on recent X-ray. WOMAC score 52.
Failed 6 months of conservative management including PT (12 sessions), naproxen
500mg BID, and two corticosteroid injections (most recent 3 months ago with
minimal relief). BMI 32.1. Requesting total knee arthroplasty.`;

runAgent(query).then((result) => {
  console.log("\n" + "=".repeat(70));
  console.log("FINAL RESULT");
  console.log("=".repeat(70));
  console.log(result);
});
