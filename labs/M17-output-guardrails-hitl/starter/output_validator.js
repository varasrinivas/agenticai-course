/**
 * M17: Output Validator — Starter
 * Validates agent outputs for structure, hallucination markers, and PII leakage.
 */

// ── Hallucination Markers ───────────────────────────────────
// Phrases that signal the agent is guessing rather than answering from data
const HALLUCINATION_MARKERS = [
  // TODO 1: Add at least 6 low-confidence phrases that indicate hallucination.
  // Examples: "i think", "probably", "i'm not sure", "it seems like",
  //           "i believe", "might be", "not entirely certain"
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
 * @param {Object} output - Agent output object.
 * @param {string[]} requiredFields - List of required field names.
 * @returns {{ valid: boolean, missingFields: string[], extraFields: string[] }}
 */
export function checkJsonStructure(output, requiredFields) {
  // TODO 2: Check which requiredFields are missing from Object.keys(output).
  // Also identify any keys in output not in requiredFields.
  // Return valid=true only if no fields are missing.
  const missing = [];
  const extra = [];

  return {
    valid: missing.length === 0,
    missingFields: missing,
    extraFields: extra,
  };
}

/**
 * Scan text for low-confidence phrases indicating potential hallucination.
 * @param {string} text - Text to scan.
 * @returns {{ hasMarkers: boolean, markersFound: string[], confidencePenalty: number }}
 */
export function checkHallucinationMarkers(text) {
  // TODO 3: Check text (lowercased) for each marker in HALLUCINATION_MARKERS.
  // Collect all found markers.
  // Calculate confidencePenalty: 0.1 per marker, capped at 0.5.
  const markersFound = [];
  const penalty = 0.0;

  return {
    hasMarkers: markersFound.length > 0,
    markersFound,
    confidencePenalty: penalty,
  };
}

/**
 * Ensure agent outputs don't leak PII data.
 * @param {string} text - Text to scan.
 * @returns {{ hasPii: boolean, piiTypes: string[], redactedText: string }}
 */
export function checkPiiInOutput(text) {
  // TODO 4: Loop through PII_PATTERNS. Use pattern.test() to detect matches.
  // Collect the PII type names found.
  // Replace all PII matches in text with the replacement string.
  // IMPORTANT: Reset regex lastIndex before each test since /g flag is used.
  const piiTypes = [];
  let redacted = text;

  return {
    hasPii: piiTypes.length > 0,
    piiTypes,
    redactedText: redacted,
  };
}

/**
 * Run all output validation checks.
 * @param {Object} output - Agent output object.
 * @param {string[]} expectedFields - Expected field names.
 * @returns {{ valid: boolean, checks: Object, output: Object }}
 */
export function validateOutput(output, expectedFields) {
  // TODO 5: Run checkJsonStructure with output and expectedFields.
  // TODO 6: If output has a "response" key (string), run checkHallucinationMarkers
  //         and checkPiiInOutput on it. If PII found, replace the response with
  //         the redacted version in a copy of the output.
  // Combine all check results. valid=true only if structure is valid AND no PII found.

  const structureCheck = { valid: true, missingFields: [], extraFields: [] };
  const hallucinationCheck = { hasMarkers: false, markersFound: [], confidencePenalty: 0.0 };
  const piiCheck = { hasPii: false, piiTypes: [], redactedText: "" };

  const isValid = structureCheck.valid && !piiCheck.hasPii;

  return {
    valid: isValid,
    checks: {
      structure: structureCheck,
      hallucination: hallucinationCheck,
      pii: piiCheck,
    },
    output,
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

  // Test 1: Valid output
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

  // Test 2: Missing fields
  const badStructure = { entity: "Acme Corp" };
  result = validateOutput(badStructure, ["entity", "filing_number", "response", "confidence"]);
  console.log(`\nTest 2 — Missing fields: ${!result.valid ? "PASS" : "FAIL"}`);
  console.log(`  Missing: ${JSON.stringify(result.checks.structure.missingFields)}`);

  // Test 3: Hallucination markers
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

  // Test 4: PII in output
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
  console.log("Self-test complete. Fill in TODOs to make all tests pass.");
  console.log("=".repeat(60));
}
