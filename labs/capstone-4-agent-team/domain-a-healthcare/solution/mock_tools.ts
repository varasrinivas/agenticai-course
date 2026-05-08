// mock_tools.ts — All agent tools for Capstone 4-A pipeline.
//
// Mirrors mock_tools.py. Used by pipeline.ts. No LLM calls in here —
// the tools are deterministic so the test suite stays fast and offline.

// ===================================================================
// INTAKE AGENT TOOLS
// ===================================================================

const MEMBER_DB: Record<string, any> = {
  "MBR-555-1234": {
    eligible: true, plan: "Gold PPO",
    effective: "2024-01-01", termination: null,
  },
};

const PROVIDER_DB: Record<string, any> = {
  "1234567890": {
    verified: true, name: "Dr. Sarah Johnson, MD",
    specialty: "Orthopedic Surgery", network: "in-network",
  },
};

export function validateAuthRequest(rawRequest: any): any {
  const required = ["member_id", "provider_npi", "procedure_code",
                    "diagnosis_codes", "clinical_notes"];
  const missing = required.filter(f => !rawRequest[f]);
  if (missing.length) {
    return {
      validated: false, missing_fields: missing,
      normalized_request: null,
    };
  }
  return {
    validated: true, missing_fields: [],
    normalized_request: {
      procedure_code: rawRequest.procedure_code,
      diagnosis_codes: rawRequest.diagnosis_codes,
      clinical_notes_summary: rawRequest.clinical_notes.slice(0, 200),
      urgency: rawRequest.urgency || "standard",
    },
  };
}

export function verifyMemberEligibility(
  memberId: string, _serviceDate?: string
): any {
  const member = MEMBER_DB[memberId];
  if (!member) {
    return {
      error: "MEMBER_NOT_FOUND",
      message: `Member ${memberId} not found.`,
    };
  }
  return { ...member, member_id: memberId };
}

export function verifyProvider(providerNpi: string): any {
  const provider = PROVIDER_DB[providerNpi];
  if (!provider) {
    return {
      error: "PROVIDER_NOT_FOUND",
      message: `NPI ${providerNpi} not found.`,
    };
  }
  return { ...provider, provider_npi: providerNpi };
}

// ===================================================================
// CLINICAL CRITERIA AGENT TOOLS
// ===================================================================

const POLICY_DB: Record<string, any> = {
  "27447": {
    policy_id: "POLICY-ORTHO-TKA-2024",
    criteria: [
      { id: "C1",
        description: "Severe OA (M17.11/M17.12) KL Grade III+",
        required: true },
      { id: "C2", description: "6+ months conservative treatment",
        required: true },
      { id: "C3", description: "WOMAC score > 50", required: true },
      { id: "C4", description: "BMI < 40", required: false },
    ],
    effective_date: "2024-01-01",
  },
};

export function fetchClinicalPolicy(procedureCode: string): any {
  const policy = POLICY_DB[procedureCode];
  if (!policy) {
    return {
      error: "NO_POLICY_FOUND",
      message: `No policy for CPT ${procedureCode}.`,
    };
  }
  return policy;
}

const CRITERIA_EVIDENCE_MAP: Record<
  string, { keywords: string[]; confidence_base: number }
> = {
  C1: {
    keywords: ["M17.11", "M17.12", "KL Grade III", "KL Grade IV",
               "osteoarthritis", "severe"],
    confidence_base: 0.90,
  },
  C2: {
    keywords: ["PT", "physical therapy", "NSAIDs", "injection",
               "conservative", "6 month", "8 month"],
    confidence_base: 0.85,
  },
  C3: { keywords: ["WOMAC", "score"], confidence_base: 0.90 },
  C4: { keywords: ["BMI"], confidence_base: 0.95 },
};

export function evaluateCriterion(
  criterionId: string, clinicalNotes: string
): any {
  const mapping = CRITERIA_EVIDENCE_MAP[criterionId];
  if (!mapping) {
    return {
      error: "CRITERION_NOT_FOUND",
      message: `Unknown criterion: ${criterionId}`,
    };
  }
  const lower = clinicalNotes.toLowerCase();
  const matches = mapping.keywords.filter(
    k => lower.includes(k.toLowerCase()));
  let confidence = mapping.confidence_base *
    (matches.length / Math.max(mapping.keywords.length * 0.5, 1));
  confidence = Math.min(confidence, 1.0);
  const met = confidence > 0.5;
  const gaps = met ? [] : [`Insufficient evidence for ${criterionId}`];
  const evidence = matches.length
    ? `Found: ${matches.join(", ")}`
    : "No matching evidence";
  return {
    criterion_id: criterionId, met,
    confidence: +confidence.toFixed(2), evidence, gaps,
  };
}

// ===================================================================
// DECISION AGENT TOOLS
// ===================================================================

export function computeDecisionConfidence(
  criteriaResults: any[],
  networkStatus: string,
  _benefitSummary?: any
): any {
  if (!criteriaResults.length) {
    return {
      error: "INCOMPLETE_INPUT", message: "No criteria results.",
    };
  }
  const avg = criteriaResults.reduce(
    (s, c) => s + (c.confidence || 0), 0) / criteriaResults.length;
  const allMet = criteriaResults
    .filter(c => c.required !== false)
    .every(c => c.met);

  let rec = "request_info";
  let humanReview = true;
  if (allMet && avg > 0.90) { rec = "approve"; humanReview = false; }
  else if (allMet && avg >= 0.70) { rec = "approve"; humanReview = true; }
  else if (!allMet && avg < 0.70) { rec = "deny"; humanReview = false; }
  else if (!allMet) { rec = "request_info"; humanReview = true; }

  return {
    overall_confidence: +avg.toFixed(2),
    recommendation: rec,
    rationale: `Avg confidence ${(avg * 100).toFixed(0)}%. ` +
      `Network: ${networkStatus}.`,
    human_review_required: humanReview,
  };
}

export function finalizeDetermination(
  requestId: string, determination: string,
  rationale: string, override?: any
): any {
  const now = new Date();
  const appeal = new Date(now.getTime() + 60 * 24 * 60 * 60 * 1000);
  return {
    determination_id: `DET-${requestId}`,
    determination: determination.toUpperCase(),
    effective_date: now.toISOString(),
    appeal_deadline: appeal.toISOString().split("T")[0],
    rationale,
    reviewer_override: override || null,
  };
}

// ===================================================================
// COMMUNICATION AGENT TOOLS
// ===================================================================

const LETTER_TEMPLATES: Record<string, string> = {
  approve: "Dear Provider,\n\nAuthorization has been approved. " +
    "Please schedule the procedure at your convenience.\n\n" +
    "Sincerely,\nClinical Authorization Team",
  deny: "Dear Provider,\n\nAuthorization has been denied. " +
    "You may appeal this decision within 60 days.\n\n" +
    "Sincerely,\nClinical Authorization Team",
  request_info: "Dear Provider,\n\nAdditional information is required. " +
    "Please submit the missing documentation within 14 days.\n\n" +
    "Sincerely,\nClinical Authorization Team",
};

export function draftDeterminationLetter(
  determinationId: string, determination = "approve"
): any {
  const template = LETTER_TEMPLATES[determination.toLowerCase()] ||
    LETTER_TEMPLATES["request_info"];
  return {
    letter_id: `LTR-${determinationId}`,
    draft_text: template,
    required_disclosures: ["Appeal rights", "Member cost share",
                           "Effective date"],
  };
}

export function sendNotification(
  letterId: string, channel: string, _recipient: string
): any {
  return {
    notification_id: `NOT-${letterId}`,
    sent_at: new Date().toISOString(),
    delivery_status: "delivered",
    channel,
  };
}

// ── Output guardrail used by Agent 4 (Communication) ───────────────
const SSN_RE = /\b\d{3}-\d{2}-\d{4}\b/g;
const DOB_RE =
  /\b(0?[1-9]|1[0-2])[/-](0?[1-9]|[12]\d|3[01])[/-]((19|20)\d{2})\b/g;

export function checkHipaaCompliance(
  letterText: string, determinationType: string
): any {
  const issues: string[] = [];
  let redacted = letterText || "";

  if (SSN_RE.test(redacted)) {
    issues.push("PII_LEAK: SSN pattern detected in letter body");
    redacted = redacted.replace(SSN_RE, "[redacted-ssn]");
  }
  if (DOB_RE.test(redacted)) {
    issues.push("PII_LEAK: full date-of-birth detected (use [redacted])");
    redacted = redacted.replace(DOB_RE, "[redacted-dob]");
  }

  const body = redacted.toLowerCase();
  const dtype = (determinationType || "").toLowerCase();
  if (["approve", "approval", "approved"].includes(dtype) &&
      !body.includes("approved")) {
    issues.push("MISSING_KEYWORD: approval letter must say 'approved'");
  } else if (["deny", "denial", "denied"].includes(dtype) &&
             !body.includes("appeal")) {
    issues.push("MISSING_KEYWORD: denial letter must include " +
                "appeal instructions");
  } else if (["request_info", "info_request"].includes(dtype) &&
             !["additional information", "missing", "submit"]
               .some(k => body.includes(k))) {
    issues.push("MISSING_KEYWORD: info-request letter must list " +
                "missing items");
  }

  if (!redacted.trim().toLowerCase().startsWith("dear")) {
    issues.push("FORMAT: missing salutation ('Dear ...')");
  }
  if (!body.includes("sincerely") && !body.includes("regards")) {
    issues.push("FORMAT: missing sign-off ('Sincerely' or 'Regards')");
  }

  return {
    compliant: issues.length === 0,
    issues,
    redacted_text: redacted,
  };
}
