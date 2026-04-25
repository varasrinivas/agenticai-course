/**
 * M16: Schema Validator — Starter (Node.js)
 * Validates that user inputs match expected UCC data formats.
 */

// ── Validation Rules ─────────────────────────────────────────

// Valid US state codes
const VALID_STATES = new Set([
  "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
  "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
  "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
  "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
  "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY",
  "DC",
]);

// UCC filing number format: UCC-YYYY-SS-NNNNNNN
const FILING_NUMBER_PATTERN = /^UCC-\d{4}-[A-Z]{2}-\d{7}$/;

/**
 * Validate a UCC filing number format.
 *
 * Expected format: UCC-YYYY-SS-NNNNNNN
 * - YYYY: 4-digit year (2000-2030)
 * - SS: 2-letter state code
 * - NNNNNNN: 7-digit sequence number
 *
 * @param {string} filingNumber
 * @returns {{ valid: boolean, errors: string[], parsed: object|null }}
 */
export function validateFilingNumber(filingNumber) {
  const errors = [];
  let parsed = null;

  // TODO 1: Check basic format with regex
  // If doesn't match FILING_NUMBER_PATTERN, add error and return early

  // TODO 2: Extract and validate components
  // Split on "-" to get parts: ["UCC", "YYYY", "SS", "NNNNNNN"]
  // Validate year is between 2000-2030
  // Validate state code is in VALID_STATES
  // Build parsed object with year (number), state (string), sequence (string)

  return { valid: errors.length === 0, errors, parsed };
}

/**
 * Validate a UCC search query object.
 *
 * Expected fields:
 *   - debtor_name: string, 2-100 chars, no special injection chars
 *   - state: string, valid 2-letter state code (optional)
 *   - filing_type: string, one of "UCC-1", "UCC-3" (optional)
 *   - status: string, one of "Active", "Terminated", "Lapsed", "Amendment" (optional)
 *
 * @param {object} query
 * @returns {{ valid: boolean, errors: string[], sanitized: object }}
 */
export function validateSearchQuery(query) {
  const errors = [];
  const sanitized = {};

  // TODO 3: Validate debtor_name
  // - Must be present and non-empty
  // - Must be 2-100 characters
  // - Must not contain SQL injection chars: ;, --, ', ", DROP, DELETE, SELECT
  // - Strip leading/trailing whitespace

  // TODO 4: Validate state (if provided)
  // - Must be 2 uppercase letters
  // - Must be in VALID_STATES

  // TODO 5: Validate filing_type (if provided)
  // - Must be one of: "UCC-1", "UCC-3"

  // TODO 6: Validate status (if provided)
  // - Must be one of: "Active", "Terminated", "Lapsed", "Amendment"

  return { valid: errors.length === 0, errors, sanitized };
}

// ── Self-Test ────────────────────────────────────────────────
// Filing number tests
const filingTests = [
  "UCC-2024-NY-0012847",   // Valid
  "UCC-2024-ZZ-0012847",   // Invalid state
  "UCC-1999-NY-0012847",   // Invalid year
  "ucc-2024-ny-0012847",   // Wrong case
  "RANDOM-STRING",          // Wrong format
  "UCC-2024-NY-12847",     // Wrong sequence length
];

console.log("=== Filing Number Validation ===");
for (const fn of filingTests) {
  const result = validateFilingNumber(fn);
  const status = result.valid ? "VALID" : "INVALID";
  console.log(`${status} ${fn}`);
  if (!result.valid) {
    for (const err of result.errors) {
      console.log(`   -> ${err}`);
    }
  }
}

// Search query tests
const queryTests = [
  { debtor_name: "Acme Corporation", state: "NY" },  // Valid
  { debtor_name: "A" },  // Too short
  { debtor_name: "'; DROP TABLE filings; --" },  // SQL injection
  { debtor_name: "Test Corp", state: "ZZ" },  // Invalid state
  { debtor_name: "Test Corp", filing_type: "UCC-5" },  // Invalid type
  {},  // Missing required field
];

console.log("\n=== Search Query Validation ===");
for (const query of queryTests) {
  const result = validateSearchQuery(query);
  const status = result.valid ? "VALID" : "INVALID";
  console.log(`${status} ${JSON.stringify(query)}`);
  if (!result.valid) {
    for (const err of result.errors) {
      console.log(`   -> ${err}`);
    }
  }
}
