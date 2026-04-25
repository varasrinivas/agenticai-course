/**
 * M16: PII Detector — Starter (Node.js)
 * Detects and redacts personally identifiable information from user inputs.
 */

// ── PII Patterns ─────────────────────────────────────────────
// Each pattern: { name, regex, replacement }
const PII_PATTERNS = [
  // TODO 1: Add regex pattern for SSN (XXX-XX-XXXX format)
  // Hint: /\d{3}-\d{2}-\d{4}/g
  // { name: "ssn", regex: /.../, replacement: "[SSN REDACTED]" },

  // TODO 2: Add regex pattern for credit card numbers (XXXX-XXXX-XXXX-XXXX or 16 digits)
  // Hint: /\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}/g
  // { name: "credit_card", regex: /.../, replacement: "[CREDIT CARD REDACTED]" },

  // TODO 3: Add regex pattern for email addresses
  // { name: "email", regex: /.../, replacement: "[EMAIL REDACTED]" },

  // TODO 4: Add regex pattern for phone numbers (XXX-XXX-XXXX, (XXX) XXX-XXXX, etc.)
  // { name: "phone", regex: /.../, replacement: "[PHONE REDACTED]" },

  // TODO 5: Add regex pattern for dates of birth (MM/DD/YYYY, YYYY-MM-DD)
  // { name: "dob", regex: /.../, replacement: "[DOB REDACTED]" },
];

/**
 * Scan text for PII patterns.
 *
 * @param {string} text - The text to scan
 * @returns {{ has_pii: boolean, detections: Array, redacted_text: string }}
 */
export function detectPii(text) {
  const detections = [];
  let redacted = text;

  // TODO 6: Loop through PII_PATTERNS
  // For each pattern, use regex.exec() or matchAll() to find all matches
  // Append each match to detections array with type, match text, and position
  // Replace matches in redacted text with the replacement string

  return {
    has_pii: detections.length > 0,
    detections,
    redacted_text: redacted,
  };
}

// ── Self-Test ────────────────────────────────────────────────
const testInputs = [
  "Look up filings for John Smith, SSN 123-45-6789",
  "Contact me at john@example.com or 555-123-4567",
  "Credit card 4111-1111-1111-1111 for payment",
  "Born on 03/15/1990, needs UCC search",
  "Search filings for Acme Corporation in New York", // Clean — no PII
];

for (const text of testInputs) {
  const result = detectPii(text);
  const status = result.has_pii ? "PII FOUND" : "Clean";
  console.log(`\n${status}: ${text}`);
  if (result.has_pii) {
    for (const d of result.detections) {
      console.log(`   -> ${d.type}: ${d.match}`);
    }
    console.log(`   Redacted: ${result.redacted_text}`);
  }
}
