/**
 * M19 Lab — Structured Logger (Starter)
 * ======================================
 * Build a JSON structured logger with PII scrubbing.
 *
 * KEY CONCEPT: JSON log lines are machine-parseable. You can pipe
 * them through jq, ship them to Datadog, or query them with SQL.
 *
 * Usage:
 *     node structured_logger.js
 */

// =============================================================================
// PII SCRUBBER
// =============================================================================

// WHAT: Functions to detect and redact PII (SSNs, emails, phones).
// WHY:  Regulations like HIPAA/GDPR require PII stay out of logs.
// GOTCHA: Regex-based scrubbing catches common formats but not all edge cases.

const PII_PATTERNS = {
  ssn: /\b\d{3}-?\d{2}-?\d{4}\b/g,
  email: /\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b/g,
  phone: /(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b/g,
};

const REDACTED = "[REDACTED]";

/**
 * Recursively scrub PII from strings, objects, and arrays.
 */
function scrubPii(data) {
  // TODO: Implement recursive PII scrubbing:
  //
  // 1. If data is a string:
  //    - For each pattern in PII_PATTERNS, use .replace() with REDACTED
  //    - Return the scrubbed string
  //
  // 2. If data is an array:
  //    - Return a new array with scrubPii() applied to each element
  //
  // 3. If data is a non-null object:
  //    - Return a new object with the same keys but scrubPii() applied
  //      to each value
  //
  // 4. Otherwise, return data unchanged
}

// =============================================================================
// STRUCTURED LOGGER
// =============================================================================

const LEVELS = { DEBUG: 10, INFO: 20, WARN: 30, ERROR: 40 };

class StructuredLogger {
  /**
   * @param {string} serviceName - Included in every log line
   * @param {string} minLevel - Minimum level to output
   */
  constructor(serviceName = "agent", minLevel = "DEBUG") {
    // TODO: Store serviceName and minLevel
    // Initialize this.logs as an empty array
  }

  /**
   * Output a structured JSON log line.
   * @returns {object|null} The log entry, or null if filtered
   */
  log(level, message, options = {}) {
    // TODO:
    // 1. Check if level is at or above minLevel. If below, return null.
    // 2. Build entry object with:
    //    - timestamp: new Date().toISOString()
    //    - level, service (this.serviceName), message
    //    - traceId: options.traceId (if present)
    //    - spanId: options.spanId (if present)
    //    - ...any other options
    // 3. Remove keys with undefined/null values
    // 4. Scrub PII from the entry
    // 5. console.log(JSON.stringify(entry))
    // 6. Push to this.logs
    // 7. Return entry
  }

  /**
   * Log an LLM API call.
   */
  logLlmCall({ model, inputTokens, outputTokens, durationMs, traceId, spanId }) {
    // TODO: Call this.log() with level "INFO", descriptive message,
    // and fields: model, inputTokens, outputTokens, totalTokens,
    // durationMs, eventType: "llm_call"
  }

  /**
   * Log a tool execution.
   */
  logToolCall({ toolName, toolInput, toolOutput, durationMs, traceId, spanId }) {
    // TODO: Call this.log() with level "INFO", descriptive message,
    // and fields: toolName, toolInput (scrubbed), toolOutput (scrubbed),
    // durationMs, eventType: "tool_call"
  }

  /**
   * Log an error.
   */
  logError(error, { traceId, spanId, ...extra } = {}) {
    // TODO: Call this.log() with level "ERROR",
    // message = error.message || String(error),
    // errorType = error.constructor.name,
    // eventType = "error", plus extra fields
  }
}

// =============================================================================
// SELF-TEST
// =============================================================================

function selfTest() {
  console.log("=".repeat(60));
  console.log("M19 Structured Logger — Self-Test");
  console.log("=".repeat(60));

  // --- PII Scrubbing Tests ---
  console.log("\n--- PII Scrubbing Tests ---\n");

  const testCases = [
    ["SSN in text", "Customer SSN is 123-45-6789, please verify"],
    ["Email in text", "Contact john.doe@example.com for details"],
    ["Phone in text", "Call (555) 123-4567 for support"],
    ["Multiple PII", "SSN: 987-65-4321, email: jane@test.com, phone: 555-987-6543"],
    ["Nested object", { name: "John", ssn: "111-22-3333", email: "john@test.com" }],
    ["Array with PII", ["Call 555-111-2222", "Email: test@test.com"]],
    ["No PII", "UCC filing #12345 for Acme Corp in New York"],
  ];

  for (const [label, data] of testCases) {
    const result = scrubPii(data);
    console.log(`  ${label}:`);
    console.log(`    Input:  ${JSON.stringify(data)}`);
    console.log(`    Output: ${JSON.stringify(result)}`);
    console.log();
  }

  // --- Structured Logger Tests ---
  console.log("\n--- Structured Logger Tests ---\n");

  let logger = new StructuredLogger("ucc_agent");

  logger.log("INFO", "Agent started", { traceId: "trace_001" });

  logger.logLlmCall({
    model: "claude-sonnet-4-6",
    inputTokens: 350,
    outputTokens: 120,
    durationMs: 823.5,
    traceId: "trace_001",
    spanId: "span_001",
  });

  logger.logToolCall({
    toolName: "search_filings",
    toolInput: { debtor_name: "John Doe", ssn: "123-45-6789" },
    toolOutput: { results: [{ filing: "UCC-001", debtor: "John Doe" }] },
    durationMs: 45.2,
    traceId: "trace_001",
    spanId: "span_002",
  });

  try {
    throw new Error("API rate limit exceeded");
  } catch (e) {
    logger.logError(e, { traceId: "trace_001", spanId: "span_003" });
  }

  // Level filtering
  logger = new StructuredLogger("ucc_agent", "WARN");
  const result = logger.log("DEBUG", "This should be filtered out");
  console.assert(result === null, "DEBUG should be filtered when minLevel is WARN");
  console.log("\n(DEBUG log correctly filtered by minLevel=WARN)");
  console.log("\nAll structured logger tests passed!");
}

export { scrubPii, StructuredLogger, LEVELS };

const isMain = process.argv[1] && process.argv[1].endsWith("structured_logger.js");
if (isMain) {
  selfTest();
}
