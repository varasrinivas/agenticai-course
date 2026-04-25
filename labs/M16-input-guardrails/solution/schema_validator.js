/**
 * M16: Schema Validator — Solution (Node.js)
 * Validates that user inputs match expected UCC data formats.
 */

// ── Validation Rules ─────────────────────────────────────────

const VALID_STATES = new Set([
  "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
  "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
  "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
  "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
  "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY",
  "DC",
]);

const FILING_NUMBER_PATTERN = /^UCC-\d{4}-[A-Z]{2}-\d{7}$/;

/**
 * Validate a UCC filing number format.
 *
 * @param {string} filingNumber
 * @returns {{ valid: boolean, errors: string[], parsed: object|null }}
 */
export function validateFilingNumber(filingNumber) {
  const errors = [];
  let parsed = null;

  // Check basic format
  if (!FILING_NUMBER_PATTERN.test(filingNumber)) {
    errors.push(
      `Filing number '${filingNumber}' does not match expected format UCC-YYYY-SS-NNNNNNN`
    );
    return { valid: false, errors, parsed: null };
  }

  // Extract and validate components
  const parts = filingNumber.split("-");
  const year = parseInt(parts[1], 10);
  const state = parts[2];
  const sequence = parts[3];

  if (year < 2000 || year > 2030) {
    errors.push(`Year ${year} is out of valid range (2000-2030)`);
  }

  if (!VALID_STATES.has(state)) {
    errors.push(`Invalid state code '${state}'`);
  }

  if (errors.length === 0) {
    parsed = { year, state, sequence };
  }

  return { valid: errors.length === 0, errors, parsed };
}

/**
 * Validate a UCC search query object.
 *
 * @param {object} query
 * @returns {{ valid: boolean, errors: string[], sanitized: object }}
 */
export function validateSearchQuery(query) {
  const errors = [];
  const sanitized = {};

  // Validate debtor_name (required)
  const debtorName = query.debtor_name;
  if (!debtorName || typeof debtorName !== "string" || debtorName.trim() === "") {
    errors.push("debtor_name is required and must be a non-empty string");
  } else {
    const trimmed = debtorName.trim();
    if (trimmed.length < 2 || trimmed.length > 100) {
      errors.push("debtor_name must be 2-100 characters");
    }
    // Check for SQL injection characters
    const injectionPatterns = [";", "--", "'", '"', "DROP", "DELETE", "SELECT"];
    for (const pattern of injectionPatterns) {
      if (trimmed.toLowerCase().includes(pattern.toLowerCase())) {
        errors.push("debtor_name contains prohibited characters");
        break;
      }
    }
    sanitized.debtor_name = trimmed;
  }

  // Validate state (optional)
  if (query.state !== undefined) {
    const state = query.state;
    if (typeof state !== "string" || !/^[A-Z]{2}$/.test(state)) {
      errors.push(`State must be a 2-letter uppercase code, got '${state}'`);
    } else if (!VALID_STATES.has(state)) {
      errors.push(`Invalid state code '${state}'`);
    } else {
      sanitized.state = state;
    }
  }

  // Validate filing_type (optional)
  if (query.filing_type !== undefined) {
    const validTypes = new Set(["UCC-1", "UCC-3"]);
    if (!validTypes.has(query.filing_type)) {
      errors.push(
        `filing_type must be one of UCC-1, UCC-3, got '${query.filing_type}'`
      );
    } else {
      sanitized.filing_type = query.filing_type;
    }
  }

  // Validate status (optional)
  if (query.status !== undefined) {
    const validStatuses = new Set(["Active", "Terminated", "Lapsed", "Amendment"]);
    if (!validStatuses.has(query.status)) {
      errors.push(
        `status must be one of Active, Terminated, Lapsed, Amendment, got '${query.status}'`
      );
    } else {
      sanitized.status = query.status;
    }
  }

  return { valid: errors.length === 0, errors, sanitized };
}

// ── Self-Test ────────────────────────────────────────────────
const filingTests = [
  "UCC-2024-NY-0012847",
  "UCC-2024-ZZ-0012847",
  "UCC-1999-NY-0012847",
  "ucc-2024-ny-0012847",
  "RANDOM-STRING",
  "UCC-2024-NY-12847",
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

const queryTests = [
  { debtor_name: "Acme Corporation", state: "NY" },
  { debtor_name: "A" },
  { debtor_name: "'; DROP TABLE filings; --" },
  { debtor_name: "Test Corp", state: "ZZ" },
  { debtor_name: "Test Corp", filing_type: "UCC-5" },
  {},
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
