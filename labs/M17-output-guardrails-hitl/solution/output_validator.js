/**
 * M17: Output Validator — Solution
 * Validates agent outputs for structure, hallucination markers, and PII leakage.
 */

// ── Hallucination Markers ───────────────────────────────────
const HALLUCINATION_MARKERS = [
  "i think",
  "probably",
  "i'm not sure",
  "it seems like",
  "i believe",
  "might be",
  "not entirely certain",
  "possibly",
  "i'm not confident",
  "it's unclear",
];

// ── PII Patterns for Output Scanning ───────────────────────
const PII_PATTERNS = [
  { name: "ssn", pattern: /\b\d{3}-\d{2}-\d{4}\b/g, replacement: "[SSN REDACTED]" },
  { name: "credit_card", pattern: /\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b/g, replacement: "[CC REDACTED]" },
  { name: "email", pattern: /\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b/g, replacement: "[EMAIL REDACTED]" },
  { name: "phone", pattern: /\b(?:\+1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b/g, replacement: "[PHONE REDACTED]" },
];

/**
 * Validate that the output object contains all required fields.
 */
export function checkJsonStructure(output, requiredFields) {
  const outputKeys = new Set(Object.keys(output));
  const requiredSet = new Set(requiredFields);

  const missing = requiredFields.filter((f) => !outputKeys.has(f)).sort();
  const extra = Object.keys(output).filter((f) => !requiredSet.has(f)).sort();

  return {
    valid: missing.length === 0,
    missingFields: missing,
    extraFields: extra,
  };
}

/**
 * Scan text for low-confidence phrases indicating potential hallucination.
 */
export function checkHallucinationMarkers(text) {
  const textLower = text.toLowerCase();
  const markersFound = HALLUCINATION_MARKERS.filter((marker) => textLower.includes(marker));
  const penalty = Math.min(markersFound.length * 0.1, 0.5);

  return {
    hasMarkers: markersFound.length > 0,
    markersFound,
    confidencePenalty: penalty,
  };
}

/**
 * Ensure agent outputs don't leak PII data.
 */
export function checkPiiInOutput(text) {
  const piiTypes = [];
  let redacted = text;

  for (const { name, pattern, replacement } of PII_PATTERNS) {
    // Reset regex lastIndex since /g flag is stateful
    pattern.lastIndex = 0;
    if (pattern.test(redacted)) {
      piiTypes.push(name);
      pattern.lastIndex = 0;
      redacted = redacted.replace(pattern, replacement);
    }
  }

  return {
    hasPii: piiTypes.length > 0,
    piiTypes,
    redactedText: redacted,
  };
}

/**
 * Run all output validation checks.
 */
export function validateOutput(output, expectedFields) {
  const structureCheck = checkJsonStructure(output, expectedFields);

  let hallucinationCheck = { hasMarkers: false, markersFound: [], confidencePenalty: 0.0 };
  let piiCheck = { hasPii: false, piiTypes: [], redactedText: "" };

  const resultOutput = { ...output };

  if (typeof output.response === "string") {
    hallucinationCheck = checkHallucinationMarkers(output.response);
    piiCheck = checkPiiInOutput(output.response);
    if (piiCheck.hasPii) {
      resultOutput.response = piiCheck.redactedText;
    }
  }

  const isValid = structureCheck.valid && !piiCheck.hasPii;

  return {
    valid: isValid,
    checks: {
      structure: structureCheck,
      hallucination: hallucinationCheck,
      pii: piiCheck,
    },
    output: resultOutput,
  };
}

// ── Self-Test ───────────────────────────────────────────────
const isMain = process.argv[1] && (
  process.argv[1].endsWith("output_validator.js") ||
  process.argv[1].endsWith("output_validator.mjs")
);

if (isMain) {
  console.log("=".repeat(60));
  console.log("M17 Output Validator — Self-Test");
  console.log("=".repeat(60));

  const goodOutput = {
    entity: "Acme Corp",
    filing_number: "UCC-2024-CA-0001234",
    response: "Acme Corp has 3 active UCC filings in California.",
    confidence: 0.95,
  };
  let result = validateOutput(goodOutput, ["entity", "filing_number", "response", "confidence"]);
  console.log(`\nTest 1 — Valid output: ${result.valid ? "PASS" : "FAIL"}`);
  console.log(`  Structure valid: ${result.checks.structure.valid}`);
  console.log(`  Hallucination markers: ${result.checks.hallucination.hasMarkers}`);
  console.log(`  PII detected: ${result.checks.pii.hasPii}`);

  const badStructure = { entity: "Acme Corp" };
  result = validateOutput(badStructure, ["entity", "filing_number", "response", "confidence"]);
  console.log(`\nTest 2 — Missing fields: ${!result.valid ? "PASS" : "FAIL"}`);
  console.log(`  Missing: ${JSON.stringify(result.checks.structure.missingFields)}`);

  const hedgingOutput = {
    entity: "Acme Corp",
    filing_number: "UCC-2024-CA-0001234",
    response: "I think Acme Corp probably has some filings, but I'm not sure about the details.",
    confidence: 0.75,
  };
  result = validateOutput(hedgingOutput, ["entity", "filing_number", "response", "confidence"]);
  console.log(`\nTest 3 — Hallucination markers:`);
  console.log(`  Markers found: ${JSON.stringify(result.checks.hallucination.markersFound)}`);
  console.log(`  Confidence penalty: ${result.checks.hallucination.confidencePenalty}`);

  const piiOutput = {
    entity: "John Smith",
    filing_number: "UCC-2024-NY-0005678",
    response: "Contact John Smith at 555-123-4567 or john@example.com. SSN: 123-45-6789.",
    confidence: 0.85,
  };
  result = validateOutput(piiOutput, ["entity", "filing_number", "response", "confidence"]);
  console.log(`\nTest 4 — PII in output: ${!result.valid ? "PASS" : "FAIL"}`);
  console.log(`  PII types: ${JSON.stringify(result.checks.pii.piiTypes)}`);
  console.log(`  Redacted: ${result.output.response || "N/A"}`);

  console.log("\n" + "=".repeat(60));
  console.log("All tests complete.");
  console.log("=".repeat(60));
}
