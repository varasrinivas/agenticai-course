/**
 * M16: PII Detector — Solution (Node.js)
 * Detects and redacts personally identifiable information from user inputs.
 */

// ── PII Patterns ─────────────────────────────────────────────
// Each pattern: { name, regex, replacement }
const PII_PATTERNS = [
  { name: "ssn", regex: /\b\d{3}-\d{2}-\d{4}\b/g, replacement: "[SSN REDACTED]" },
  { name: "credit_card", regex: /\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b/g, replacement: "[CREDIT CARD REDACTED]" },
  { name: "email", regex: /\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b/g, replacement: "[EMAIL REDACTED]" },
  { name: "phone", regex: /(?:\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})\b/g, replacement: "[PHONE REDACTED]" },
  { name: "dob", regex: /\b(?:\d{2}\/\d{2}\/\d{4}|\d{4}-\d{2}-\d{2})\b/g, replacement: "[DOB REDACTED]" },
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

  for (const { name, regex, replacement } of PII_PATTERNS) {
    // Reset regex lastIndex for each run
    const pattern = new RegExp(regex.source, regex.flags);
    let match;
    const matches = [];

    while ((match = pattern.exec(redacted)) !== null) {
      matches.push({
        type: name,
        match: match[0],
        position: [match.index, match.index + match[0].length],
      });
    }

    // Process from end to start to preserve positions during replacement
    for (let i = matches.length - 1; i >= 0; i--) {
      const m = matches[i];
      detections.push(m);
      redacted =
        redacted.slice(0, m.position[0]) +
        replacement +
        redacted.slice(m.position[1]);
    }
  }

  // Sort detections by position for consistent output
  detections.sort((a, b) => a.position[0] - b.position[0]);

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
